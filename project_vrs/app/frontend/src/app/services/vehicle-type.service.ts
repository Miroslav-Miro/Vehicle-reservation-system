import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { apiBase } from '../shared/api';

export interface VehicleType {
    id: number;
    vehicle_type: string;
}

@Injectable({ providedIn: 'root' })
export class VehicleTypeService {
    private base = `${apiBase()}/vehicle_type_filter`

    constructor(private http: HttpClient) { }

    getAll(): Observable<VehicleType[]> {
        return this.http.get<VehicleType[]>(this.base);
    }
}
