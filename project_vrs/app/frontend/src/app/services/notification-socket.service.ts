import { Injectable } from '@angular/core';
import { Subject, Observable } from 'rxjs';

export type LiveEvent = any; // your WS payload (e.g., { action, reservation, message })

@Injectable({ providedIn: 'root' })
export class NotificationsSocketService {
    private socket?: WebSocket;
    private reconnectDelay = 1000;
    private readonly maxDelay = 10000;
    private shouldReconnect = true;

    private _events$ = new Subject<LiveEvent>();
    get events$(): Observable<LiveEvent> { return this._events$.asObservable(); }

    connect(): void {
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            return;
        }
        this.shouldReconnect = true;

        const access = localStorage.getItem('access') ?? '';
        if (!access) { this.scheduleReconnect(); return; }

        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        const host = this.resolveHost();
        const url = `${proto}://${host}/ws/notifications/?token=${encodeURIComponent(access)}`;

        try { this.socket?.close(); } catch { }
        try { this.socket = new WebSocket(url); }
        catch { this.scheduleReconnect(); return; }

        this.socket.onopen = () => { this.reconnectDelay = 1000; };
        this.socket.onmessage = (evt) => {
            try { this._events$.next(JSON.parse(evt.data)); } catch { /* ignore */ }
        };
        this.socket.onerror = () => { /* let close handle it */ };
        this.socket.onclose = () => { if (this.shouldReconnect) this.scheduleReconnect(); };
    }

    close(): void {
        this.shouldReconnect = false;
        try { this.socket?.close(1000, 'client_closed'); } catch { }
        this.socket = undefined;
    }

    private scheduleReconnect() {
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.6, this.maxDelay);
    }

    private resolveHost(): string {
        if (location.port && location.port !== '4200') return location.host;
        const apiHost = (window as any).__env?.API_HOST ?? (window as any).__env?.API_BASE ?? localStorage.getItem('api_host') ?? 'localhost:8000';
        try { return new URL(/^https?:\/\//i.test(apiHost) ? apiHost : `http://${apiHost}`).host; }
        catch { return apiHost; }
    }
}
