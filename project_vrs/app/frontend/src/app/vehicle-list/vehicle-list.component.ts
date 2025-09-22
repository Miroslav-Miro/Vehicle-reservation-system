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
  styleUrls: ['./vehicle-list.component.less'] // <- plural, Angular expects styleUrls
})
export class VehicleListComponent implements OnInit {
  locations$!: Observable<Location[]>;
  brands: Brand[] = [];
  models: Model[] = [];
  vehicles: any[] = [];

  vehicleTypes: VehicleType[] = [];
  engineTypes: EngineType[] = [];

  // UI model (ids for selects). We'll map them to names for the API.
  selectedVehicleTypeId: number | null = null;
  selectedEngineTypeId: number | null = null;

  filters: any = {
    location_id: null,
    start: '',
    end: '',
    brand_id: null,
    model_id: null,
    // backend expects strings for these two:
    vehicle_type: '', // will be set from selectedVehicleTypeId before request
    engine_type: '',  // will be set from selectedEngineTypeId before request
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
    // Locations (async pipe in template)
    this.locations$ = this.locationService.getAll();

    // Brands with nested models
    this.brandModelService.getAll().subscribe({
      next: (res) => (this.brands = res),
      error: (err) => console.error(err),
    });

    // Vehicle types
    this.vehicleTypeService.getAll().subscribe({
      next: (res) => (this.vehicleTypes = res),
      error: (err) => console.error(err),
    });

    // Engine types
    this.engineTypeService.getAll().subscribe({
      next: (res) => (this.engineTypes = res),
      error: (err) => console.error(err),
    });
  }

  onBrandChange(): void {
    const brand = this.brands.find((b) => b.id === this.filters.brand_id) || null;
    this.models = brand ? brand.models : [];
    this.filters.model_id = null; // reset model when brand changes or is cleared
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
  }

  // If you use <input type="datetime-local">, normalize to ISO with seconds + Z
  private toIsoZ(value: string): string {
    // value comes like "2025-09-22T19:01"
    return value ? `${value}:00Z` : '';
  }

  searchVehicles(): void {
    let params = new HttpParams();

    // ensure start/end are in full ISO (if you're using datetime-local inputs)
    const startIso = this.filters.start.includes('T') ? this.toIsoZ(this.filters.start) : this.filters.start;
    const endIso = this.filters.end.includes('T') ? this.toIsoZ(this.filters.end) : this.filters.end;

    const payload = {
      ...this.filters,
      start: startIso,
      end: endIso,
    };

    // Build query only with truthy values
    for (const key in payload) {
      if (payload[key]) {
        params = params.set(key, payload[key]);
      }
    }

    this.http
      .get<any[]>('http://localhost:8000/api/public/vehicles/available/', { params })
      .subscribe({
        next: (res) => {
          this.vehicles = res;
          console.log('API response:', res);
        },
        error: (err) => console.error(err),
      });
  }
}
