import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { apiBase } from '../shared/api';

export interface Model {
    id: number;
    model_name: string;
}

export interface Brand {
    id: number;
    brand_name: string;
    models: Model[];
}


@Injectable({ providedIn: 'root' })
export class BrandModelService {
    private base = `${apiBase()}/brands_models_filter`

    constructor(private http: HttpClient) { }

    getAll(): Observable<Brand[]> {
        return this.http.get<Brand[]>(this.base);
    }
}
