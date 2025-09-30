import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { apiBase } from '../shared/api';

@Injectable({ providedIn: 'root' })
export class ReservationsService {
    private base = apiBase();

    constructor(private http: HttpClient) { }

    // NOTE: your path says "user_reservalitions" (typo?).
    // If your real endpoint is /user_reservations, just fix the string.
    getCurrent() {
        return this.http.get<any>(`${this.base}/user_reservations?status=active`);
    }

    getHistory() {
        return this.http.get<any>(`${this.base}/user_reservations?status=history`);
    }

    updateStatus(id: number, status: string): Observable<any> {
        // If your backend expects {"status":"cancelled"}:
        return this.http.patch<any>(`${this.base}/user_reservations/${id}/`, { status });
        // If your backend expects {"status": {"id": X}} (uncomment and use this instead):
        // return this.http.patch<any>(`${this.base}/user_reservalitions/${id}/`, { status: { id: X } });
    }

    /** Convenience: cancel */
    cancel(id: number) {
        return this.updateStatus(id, 'cancelled'); // or 'canceled' → match your backend spelling
    }
}
