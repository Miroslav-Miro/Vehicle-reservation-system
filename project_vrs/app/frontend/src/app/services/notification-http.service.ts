import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, forkJoin, Observable } from 'rxjs';

export interface NotificationDto {
    id: number;
    message: string;
    type?: string | null;
    is_read: boolean;
    created_at: string; // ISO string
}

@Injectable({ providedIn: 'root' })
export class NotificationsHttpService {
    private base = 'http://localhost:8000/api';

    constructor(private http: HttpClient) { }

    /** GET /api/notifications/ — unwraps paginated or plain list */
    list(): Observable<NotificationDto[]> {
        return this.http.get<any>(`${this.base}/notifications/`).pipe(
            map(res => (Array.isArray(res) ? res : (res?.results ?? [])))
        );
    }

    /** PATCH /api/notifications/:id/ { is_read: true } */
    markRead(id: number): Observable<NotificationDto> {
        return this.http.patch<NotificationDto>(`${this.base}/notifications/${id}/`, { is_read: true });
    }

    /** Convenience: mark many as read (client-side batch) */
    markAllRead(ids: number[]): Observable<NotificationDto[]> {
        if (!ids.length) return new Observable(sub => { sub.next([]); sub.complete(); });
        return forkJoin(ids.map(id => this.markRead(id)));
    }
}
