import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { apiBase } from '../shared/api';

export interface EngineType {
    id: number;
    engine_type: string;
}

@Injectable({ providedIn: 'root' })
export class EngineTypeService {
    private base = `${apiBase()}/engine_type_filter`

    constructor(private http: HttpClient) { }

    getAll(): Observable<EngineType[]> {
        return this.http.get<EngineType[]>(this.base);
    }
}
