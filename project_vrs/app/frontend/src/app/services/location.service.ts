import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Location {
    id: number;
    location_name: string;
    address: string;
}

@Injectable({ providedIn: 'root' })
export class LocationService {
    private base = 'http://localhost:8000/api/locations_filter';

    constructor(private http: HttpClient) { }

    getAll(): Observable<Location[]> {
        return this.http.get<Location[]>(this.base);
    }
}
