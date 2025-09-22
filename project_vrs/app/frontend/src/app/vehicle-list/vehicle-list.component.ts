import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { LocationService, Location } from '../services/location.service';
import { BrandModelService, Brand, Model } from '../services/brand-model.service';
import { VehicleTypeService, VehicleType } from '../services/vehicle-type.service';
import { EngineTypeService, EngineType } from '../services/engine-type.service';

@Component({
  selector: 'app-vehicle-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
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
  ) {}

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
  }

  onBrandChange(): void {
    const brand = this.brands.find((b) => b.id === this.filters.brand_id) || null;
    this.models = brand ? brand.models : [];
    this.filters.model_id = null;
  }

  clearBrand(): void {
    this.filters.brand_id = null;
    this.models = [];
    this.filters.model_id = null;
  }

  clearModel(): void {
    this.filters.model_id = null;
  }

  onVehicleTypeChange(): void {
    const vt = this.vehicleTypes.find(v => v.id === this.selectedVehicleTypeId) || null;
    this.filters.vehicle_type = vt ? vt.vehicle_type : '';
  }

  clearVehicleType(): void {
    this.selectedVehicleTypeId = null;
    this.filters.vehicle_type = '';
  }

  onEngineTypeChange(): void {
    const et = this.engineTypes.find(e => e.id === this.selectedEngineTypeId) || null;
    this.filters.engine_type = et ? et.engine_type : '';
  }

  clearEngineType(): void {
    this.selectedEngineTypeId = null;
    this.filters.engine_type = '';
  }

  clearAll(): void {
    this.filters = {
      location_id: null,
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
    this.selectedVehicleTypeId = null;
    this.selectedEngineTypeId = null;
    this.models = [];
    this.errorMsg = '';
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
    // 1) If location is chosen -> start & end are required
    if (hasLocation && (!hasStart || !hasEnd)) {
      this.errorMsg = 'Please choose both start and end dates when a location is selected.';
      return;
    }
    // 2) If only one date is provided -> invalid (must be both or neither)
    if ((hasStart && !hasEnd) || (!hasStart && hasEnd)) {
      this.errorMsg = 'Please provide both start and end dates, or clear both.';
      return;
    }

    let params = new HttpParams();

    // start/end normalization only if both provided
    if (hasStart && hasEnd) {
      const startIso = this.filters.start.includes('T') ? this.toIsoZ(this.filters.start) : this.filters.start;
      const endIso = this.filters.end.includes('T') ? this.toIsoZ(this.filters.end) : this.filters.end;
      params = params.set('start', startIso).set('end', endIso);
    }

    // Only include location if it's chosen (Any location -> null)
    if (hasLocation) {
      params = params.set('location_id', this.filters.location_id);
    }

    // Optional filters (only send truthy)
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
          // optional: clear message if user fixed the issue and data came back
          this.errorMsg = '';
          console.log('API response:', res);
        },
        error: (err) => {
          console.error(err);
          // bubble backend errors to UI (e.g., parse errors)
          this.errorMsg = err?.error?.detail || 'Something went wrong while searching.';
        },
      });
  }
}
