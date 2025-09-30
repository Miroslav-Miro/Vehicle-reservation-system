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
    private resolveBase(): string {
        const w: any = (window as any) || {};
        const base: string | undefined = w.__env?.API_BASE;
        if (base && typeof base === 'string' && base.trim()) return base.replace(/\/$/, '');

        // Fallback: if API_HOST provided, build a scheme + host
        const host: string | undefined = w.__env?.API_HOST || localStorage.getItem('api_host') || undefined;
        if (host) {
            try {
                const u = new URL(/^https?:\/\//i.test(host) ? host : `https://${host}`);
                return `${u.origin.replace(/\/$/, '')}/api`;
            } catch {
                return `https://${host.replace(/\/$/, '')}/api`;
            }
        }
        // Local dev default
        return 'http://localhost:8000/api';
    }

    private base = this.resolveBase();

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
