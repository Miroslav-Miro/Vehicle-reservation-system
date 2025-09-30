import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { apiBase } from '../shared/api';

export interface Location {
    id: number;
    location_name: string;
    address: string;
}

@Injectable({ providedIn: 'root' })
export class LocationService {
    private base = `${apiBase()}/locations_filter`;

    constructor(private http: HttpClient) { }

    getAll(): Observable<Location[]> {
        return this.http.get<Location[]>(this.base);
    }
}
