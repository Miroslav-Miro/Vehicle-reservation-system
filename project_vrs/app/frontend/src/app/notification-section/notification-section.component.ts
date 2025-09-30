import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { NotificationsHttpService, NotificationDto } from '../services/notification-http.service';
import { NotificationsSocketService } from '../services/notification-socket.service';

type UiNotification = {
  id: number;
  type: string;
  message: string;
  created_at: Date;
  is_read: boolean;
};

@Component({
  selector: 'app-notification-section',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notification-section.component.html',
  styleUrls: ['./notification-section.component.less'],
})
export class NotificationSectionComponent implements OnInit, OnDestroy {
  notifications: UiNotification[] = [];
  panelOpen = false;

  private sub?: Subscription;

  constructor(
    private http: NotificationsHttpService,
    private socket: NotificationsSocketService
  ) {}

  ngOnInit(): void {
    this.reload();

    // open WS & refresh list on any live event
    this.socket.connect();
    this.sub = this.socket.events$.subscribe(() => {
      this.reload();
      this.panelOpen = true; // optional auto-open
    });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    this.socket.close();
  }

  // -------- UI helpers --------

  togglePanel(force?: boolean) {
    this.panelOpen = force !== undefined ? force : !this.panelOpen;
    if (this.panelOpen) this.markAllRead();
  }

  get unreadCount(): number {
    return this.notifications.filter(n => !n.is_read).length;
  }

  trackById = (_: number, n: UiNotification) => n.id;

  // -------- data flow --------

  private reload() {
    this.http.list().subscribe((rows: NotificationDto[]) => {
      this.notifications = rows.map(r => ({
        id: r.id,
        type: (r.type ?? 'info') as string,
        message: r.message ?? '',
        created_at: new Date(r.created_at),
        is_read: !!r.is_read,
      }));
    });
  }

  markAllRead() {
    const ids = this.notifications.filter(n => !n.is_read).map(n => n.id);
    if (!ids.length) return;
    this.http.markAllRead(ids).subscribe({
      next: () => this.reload(),
      error: () => this.reload(),
    });
  }
}
