import { Component, OnInit, HostListener } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { LocationService, Location } from '../services/location.service';
import { BrandModelService, Brand, Model } from '../services/brand-model.service';
import { VehicleTypeService, VehicleType } from '../services/vehicle-type.service';
import { EngineTypeService, EngineType } from '../services/engine-type.service';

type BasketItem = {
  vehicle_id: number;
  brand: string;
  model: string;
  price_per_day: number;
  available_count: number;
  qty: number;
};

@Component({
  selector: 'app-vehicle-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './vehicle-list.component.html',
  styleUrls: ['./vehicle-list.component.less'],
})
export class VehicleListComponent implements OnInit {
  // ---------- Storage Keys ----------
  private STORAGE = {
    filters: 'vl.filters',
    basket: 'vl.basket',
    sidebar: 'vl.sidebarOpen',
  };

  // ---------- Basket state ----------
  // Partial so template optional-chaining is valid (no NG8107).
  basket: Partial<Record<number, BasketItem>> = {};
  sidebarOpen = false;

  get basketItems(): BasketItem[] {
    return Object.values(this.basket).filter((x): x is BasketItem => !!x);
  }
  get basketCount(): number {
    return this.basketItems.reduce((s, it) => s + it.qty, 0);
  }
  get basketTotal(): number {
    return this.basketItems.reduce((s, it) => s + it.qty * Number(it.price_per_day), 0);
  }

  toggleSidebar(open?: boolean) {
    this.sidebarOpen = open !== undefined ? open : !this.sidebarOpen;
    this.saveSidebarToStorage();
  }

  @HostListener('document:keydown.escape')
  onEsc() { this.sidebarOpen = false; this.saveSidebarToStorage(); }

  // Helpers usable from template
  toInt(n: any): number { return typeof n === 'number' ? n : parseInt(n, 10) || 0; }
  qtyInBasket(id: number): number {
    return this.basket[id]?.qty ?? 0;
  }
  isMaxed(v: any): boolean {
    const max = this.toInt(v.available_count);
    return this.qtyInBasket(v.vehicle_id) >= max || max === 0;
  }

  addToBasket(v: any) {
    const id = v.vehicle_id;
    const max = this.toInt(v.available_count);
    const existing = this.basket[id];

    if (existing) {
      if (existing.qty < max) existing.qty += 1;
      this.sidebarOpen = true;
      this.saveBasketToStorage();
      this.saveSidebarToStorage();
      return;
    }
    if (max <= 0) return;

    this.basket[id] = {
      vehicle_id: v.vehicle_id,
      brand: v.brand,
      model: v.model,
      price_per_day: Number(v.price_per_day),
      available_count: max,
      qty: 1,
    };
    this.sidebarOpen = true;
    this.saveBasketToStorage();
    this.saveSidebarToStorage();
  }

  incQty(it: BasketItem) {
    const max = this.toInt(it.available_count);
    if (it.qty < max) { it.qty += 1; this.saveBasketToStorage(); }
  }
  decQty(it: BasketItem) {
    if (it.qty > 1) { it.qty -= 1; this.saveBasketToStorage(); }
  }
  removeFromBasket(id: number) { delete this.basket[id]; this.saveBasketToStorage(); }
  clearBasket() { this.basket = {}; this.saveBasketToStorage(); }

  reserve() {
    if (!this.isSearchReady() || this.basketCount === 0) return;
    const lines = this.basketItems.map(it => ({ vehicle_id: it.vehicle_id, qty: it.qty }));
    const payload = {
      start: this.filters.start,
      end: this.filters.end,
      start_location_id: this.filters.location_id,
      end_location_id: this.filters.end_location_id ?? this.filters.location_id, // <-- here
      lines,
    };
    this.http.post('http://localhost:8000/api/public/reservations/', payload).subscribe({
      next: () => { this.clearBasket(); this.sidebarOpen = false; this.saveSidebarToStorage(); alert('Reservation submitted!'); },
      error: (err) => alert(err?.error?.detail || 'Failed to reserve.'),
    });
  }

  // ---------- Existing list & filters ----------
  locations$!: Observable<Location[]>;
  brands: Brand[] = [];
  models: Model[] = [];
  vehicles: any[] = [];

  vehicleTypes: VehicleType[] = [];
  engineTypes: EngineType[] = [];

  selectedVehicleTypeId: number | null = null;
  selectedEngineTypeId: number | null = null;

  showExtraFilters = false;
  private autoSearch$ = new Subject<void>();

  errorMsg = '';

  filters: any = {
    location_id: null,
    end_location_id: null,
    start: '',
    end: '',
    brand_id: null,
    model_id: null,
    vehicle_type: '',
    engine_type: '',
    price_min: null,
    price_max: null,
    seats_min: null,
    seats_max: null,
  };

  constructor(
    private http: HttpClient,
    private locationService: LocationService,
    private brandModelService: BrandModelService,
    private vehicleTypeService: VehicleTypeService,
    private engineTypeService: EngineTypeService
  ) { }

  ngOnInit(): void {
    // Load saved state first
    this.loadFiltersFromStorage();
    this.loadBasketFromStorage();
    this.loadSidebarFromStorage();

    // Data for selects
    this.locations$ = this.locationService.getAll();

    this.brandModelService.getAll().subscribe({
      next: (res) => (this.brands = res),
      error: (err) => console.error(err),
    });

    this.vehicleTypeService.getAll().subscribe({
      next: (res) => {
        this.vehicleTypes = res;
        this.syncSelectedIdsFromFilters(); // map back vehicle_type string -> selectedVehicleTypeId
      },
      error: (err) => console.error(err),
    });

    this.engineTypeService.getAll().subscribe({
      next: (res) => {
        this.engineTypes = res;
        this.syncSelectedIdsFromFilters(); // map back engine_type string -> selectedEngineTypeId
      },
      error: (err) => console.error(err),
    });

    this.autoSearch$.pipe(debounceTime(250)).subscribe(() => {
      if (this.isSearchReady()) this.searchVehicles();
    });
  }

  // Map stored string filters back to select IDs once options are loaded
  private syncSelectedIdsFromFilters(): void {
    if (this.vehicleTypes?.length && this.filters.vehicle_type) {
      const vt = this.vehicleTypes.find(t => t.vehicle_type === this.filters.vehicle_type);
      this.selectedVehicleTypeId = vt?.id ?? null;
    }
    if (this.engineTypes?.length && this.filters.engine_type) {
      const et = this.engineTypes.find(e => e.engine_type === this.filters.engine_type);
      this.selectedEngineTypeId = et?.id ?? null;
    }
  }

  private isSearchReady(): boolean {
    return !!this.filters.location_id && !!this.filters.start && !!this.filters.end;
  }
  private queueSearch(): void {
    if (this.isSearchReady()) this.autoSearch$.next();
  }

  // ---------- Persist: Filters ----------
  private saveFiltersToStorage(): void {
    try {
      const toSave = {
        location_id: this.filters.location_id,
        end_location_id: this.filters.end_location_id,
        start: this.filters.start, // keep local datetime format for <input type=datetime-local>
        end: this.filters.end,
        brand_id: this.filters.brand_id,
        model_id: this.filters.model_id,
        vehicle_type: this.filters.vehicle_type,
        engine_type: this.filters.engine_type,
        price_min: this.filters.price_min,
        price_max: this.filters.price_max,
        seats_min: this.filters.seats_min,
        seats_max: this.filters.seats_max,
      };
      localStorage.setItem(this.STORAGE.filters, JSON.stringify(toSave));
    } catch { }
  }
  private loadFiltersFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.STORAGE.filters);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      this.filters = { ...this.filters, ...parsed };
    } catch { }
  }

  // ---------- Persist: Basket ----------
  private saveBasketToStorage(): void {
    try {
      localStorage.setItem(this.STORAGE.basket, JSON.stringify(this.basket));
    } catch { }
  }
  private loadBasketFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.STORAGE.basket);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Record<string, BasketItem | undefined>;
      const out: Partial<Record<number, BasketItem>> = {};
      Object.keys(parsed).forEach(k => {
        const it = parsed[k];
        if (it) {
          out[Number(k)] = {
            vehicle_id: Number(it.vehicle_id),
            brand: it.brand,
            model: it.model,
            price_per_day: Number(it.price_per_day),
            available_count: Number(it.available_count),
            qty: Number(it.qty),
          };
        }
      });
      this.basket = out;
    } catch { }
  }

  // ---------- Persist: Sidebar ----------
  private saveSidebarToStorage(): void {
    try { localStorage.setItem(this.STORAGE.sidebar, JSON.stringify(!!this.sidebarOpen)); } catch { }
  }
  private loadSidebarFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.STORAGE.sidebar);
      if (!raw) return;
      this.sidebarOpen = !!JSON.parse(raw);
    } catch { }
  }

  // ---------- Filter change handlers (save + optional auto-search) ----------
  // RESET BASKET when START LOCATION changes
  onStartLocationChange(val: any): void {
    this.filters.location_id = val;
    this.saveFiltersToStorage();
    this.clearBasket(); // reset basket on start location change
  }

  // 3) Handle end-location change (no basket reset unless you want it)
  onEndLocationChange(val: any): void {
    this.filters.end_location_id = val;
    this.saveFiltersToStorage();
    // if you WANT to reset basket when end location changes, uncomment next line:
    // this.clearBasket();
  }


  onStartDateChange(): void { this.saveFiltersToStorage(); }
  onEndDateChange(): void { this.saveFiltersToStorage(); }

  onNumericFilterChange(
    field: 'price_min' | 'price_max' | 'seats_min' | 'seats_max',
    value: any
  ): void {
    this.filters[field] = (value === '' || value === null) ? null : Number(value);
    this.saveFiltersToStorage();
    this.queueSearch();
  }

  onBrandChange(): void {
    const brand = this.brands.find((b) => b.id === this.filters.brand_id) || null;
    this.models = brand ? brand.models : [];
    this.filters.model_id = null;
    this.saveFiltersToStorage();
    this.queueSearch();
  }
  clearBrand(): void {
    this.filters.brand_id = null;
    this.models = [];
    this.filters.model_id = null;
    this.saveFiltersToStorage();
    this.queueSearch();
  }
  onModelChange(): void { this.saveFiltersToStorage(); this.queueSearch(); }
  clearModel(): void { this.filters.model_id = null; this.saveFiltersToStorage(); this.queueSearch(); }

  onVehicleTypeChange(): void {
    const vt = this.vehicleTypes.find(v => v.id === this.selectedVehicleTypeId) || null;
    this.filters.vehicle_type = vt ? vt.vehicle_type : '';
    this.saveFiltersToStorage();
    this.queueSearch();
  }
  clearVehicleType(): void { this.selectedVehicleTypeId = null; this.filters.vehicle_type = ''; this.saveFiltersToStorage(); this.queueSearch(); }

  onEngineTypeChange(): void {
    const et = this.engineTypes.find(e => e.id === this.selectedEngineTypeId) || null;
    this.filters.engine_type = et ? et.engine_type : '';
    this.saveFiltersToStorage();
    this.queueSearch();
  }
  clearEngineType(): void { this.selectedEngineTypeId = null; this.filters.engine_type = ''; this.saveFiltersToStorage(); this.queueSearch(); }

  clearAll(): void {
    this.filters = {
      ...this.filters,  // keep location_id, start, end
      brand_id: null,
      model_id: null,
      vehicle_type: '',
      engine_type: '',
      price_min: null,
      price_max: null,
      seats_min: null,
      seats_max: null,
    };
    this.selectedVehicleTypeId = null;
    this.selectedEngineTypeId = null;
    this.models = [];
    this.errorMsg = '';
    this.saveFiltersToStorage();
    this.queueSearch();
  }

  private toIsoZ(value: string): string {
    return value ? `${value}:00Z` : '';
  }

  searchVehicles(): void {
    this.errorMsg = '';

    const hasLocation = this.filters.location_id !== null && this.filters.location_id !== undefined;
    const hasStart = !!this.filters.start;
    const hasEnd = !!this.filters.end;

    if (hasLocation && (!hasStart || !hasEnd)) {
      this.errorMsg = 'Please choose both start and end dates when a location is selected.';
      return;
    }
    if ((hasStart && !hasEnd) || (!hasStart && hasEnd)) {
      this.errorMsg = 'Please provide both start and end dates, or clear both.';
      return;
    }

    let params = new HttpParams();
    if (hasStart && hasEnd) {
      const startIso = this.filters.start.includes('T') ? this.toIsoZ(this.filters.start) : this.filters.start;
      const endIso = this.filters.end.includes('T') ? this.toIsoZ(this.filters.end) : this.filters.end;
      params = params.set('start', startIso).set('end', endIso);
    }
    if (hasLocation) params = params.set('location_id', this.filters.location_id);

    const optionalKeys = [
      'brand_id', 'model_id',
      'vehicle_type', 'engine_type',
      'price_min', 'price_max',
      'seats_min', 'seats_max',
    ];
    for (const k of optionalKeys) {
      const val = this.filters[k];
      if (val !== null && val !== undefined && val !== '') {
        params = params.set(k, val);
      }
    }

    this.http
      .get<any[]>('http://localhost:8000/api/public/vehicles/available/', { params })
      .subscribe({
        next: (res) => {
          this.vehicles = res;
          this.errorMsg = '';
          this.showExtraFilters = true;
        },
        error: (err) => {
          console.error(err);
          this.errorMsg = err?.error?.detail || 'Something went wrong while searching.';
        },
      });
  }
}
