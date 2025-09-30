import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface VehicleType {
    id: number;
    vehicle_type: string;
}

@Injectable({ providedIn: 'root' })
export class VehicleTypeService {
    private base = 'http://localhost:8000/api/vehicle_type_filter'

    constructor(private http: HttpClient) { }

    getAll(): Observable<VehicleType[]> {
        return this.http.get<VehicleType[]>(this.base);
    }
}
