import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { apiBase } from '../shared/api';

export interface Vehicle {
    vehicle_id: number;
    brand: string;
    model: string;
    vehicle_type: string;
    engine_type: string;
    seats: number;
    price_per_day: number;
    available_count: number;
}

@Injectable({ providedIn: 'root' })
export class VehicleService {
    private base = `${apiBase()}/public/vehicles/available/`;

    constructor(private http: HttpClient) { }

    getFeatured(count = 4): Observable<Vehicle[]> {
        const params = new HttpParams().set('random', count.toString());
        return this.http.get<Vehicle[]>(this.base, { params });
    }
}
