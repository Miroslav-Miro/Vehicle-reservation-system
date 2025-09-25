import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';


import { LocationService, Location } from '../services/location.service';
import { BrandModelService, Brand, Model } from '../services/brand-model.service';
import { VehicleTypeService, VehicleType } from '../services/vehicle-type.service';
import { EngineTypeService, EngineType } from '../services/engine-type.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-vehicle-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './vehicle-list.component.html',
  styleUrls: ['./vehicle-list.component.less'],
})
export class VehicleListComponent implements OnInit {
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

  errorMsg = ''; // <-- for validation messages

  filters: any = {
    location_id: null,
    start: '',
    end: '',
    brand_id: null,
    model_id: null,
    vehicle_type: '', // mapped from selectedVehicleTypeId
    engine_type: '',  // mapped from selectedEngineTypeId
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
    this.locations$ = this.locationService.getAll();

    this.brandModelService.getAll().subscribe({
      next: (res) => (this.brands = res),
      error: (err) => console.error(err),
    });

    this.vehicleTypeService.getAll().subscribe({
      next: (res) => (this.vehicleTypes = res),
      error: (err) => console.error(err),
    });

    this.engineTypeService.getAll().subscribe({
      next: (res) => (this.engineTypes = res),
      error: (err) => console.error(err),
    });

    this.autoSearch$.pipe(debounceTime(250)).subscribe(() => {
      if (this.isSearchReady()) this.searchVehicles();
    });
  }

  private isSearchReady(): boolean {
    return !!this.filters.location_id && !!this.filters.start && !!this.filters.end;
  }

  private queueSearch(): void {
    if (this.isSearchReady()) this.autoSearch$.next();
  }

  /** 🔔 Numeric inputs auto-search */
  onNumericFilterChange(
    field: 'price_min' | 'price_max' | 'seats_min' | 'seats_max',
    value: any
  ): void {
    this.filters[field] = (value === '' || value === null) ? null : Number(value);
    this.queueSearch();
  }

  onBrandChange(): void {
    const brand = this.brands.find((b) => b.id === this.filters.brand_id) || null;
    this.models = brand ? brand.models : [];
    this.filters.model_id = null;
    this.queueSearch();
  }

  clearBrand(): void {
    this.filters.brand_id = null;
    this.models = [];
    this.filters.model_id = null;
    this.queueSearch();
  }

  onModelChange(): void {
    this.queueSearch();
  }

  clearModel(): void {
    this.filters.model_id = null;
    this.queueSearch();
  }

  onVehicleTypeChange(): void {
    const vt = this.vehicleTypes.find(v => v.id === this.selectedVehicleTypeId) || null;
    this.filters.vehicle_type = vt ? vt.vehicle_type : '';
    this.queueSearch();
  }

  clearVehicleType(): void {
    this.selectedVehicleTypeId = null;
    this.filters.vehicle_type = '';
    this.queueSearch();
  }

  onEngineTypeChange(): void {
    const et = this.engineTypes.find(e => e.id === this.selectedEngineTypeId) || null;
    this.filters.engine_type = et ? et.engine_type : '';
    this.queueSearch();
  }

  clearEngineType(): void {
    this.selectedEngineTypeId = null;
    this.filters.engine_type = '';
    this.queueSearch();
  }

clearAll(): void {
  this.filters = {
    ...this.filters,  // keep existing location_id, start, end
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
  this.queueSearch();
}

  // Normalize datetime-local -> ISO with seconds + Z
  private toIsoZ(value: string): string {
    // input like "2025-09-22T19:01" -> "2025-09-22T19:01:00Z"
    return value ? `${value}:00Z` : '';
  }

  searchVehicles(): void {
    this.errorMsg = '';

    const hasLocation = this.filters.location_id !== null && this.filters.location_id !== undefined;
    const hasStart = !!this.filters.start;
    const hasEnd = !!this.filters.end;

    // Validation rules:
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

    if (hasLocation) {
      params = params.set('location_id', this.filters.location_id);
    }

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

          // ✅ show filters only after search succeeds
          this.showExtraFilters = true;
        },
        error: (err) => {
          console.error(err);
          this.errorMsg = err?.error?.detail || 'Something went wrong while searching.';
        },
      });
  }

}
