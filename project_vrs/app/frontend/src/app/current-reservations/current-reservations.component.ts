import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, NgFor, NgIf } from '@angular/common';
import { ReservationsService } from '../reservations/reservation.service';
import { NotificationSectionComponent } from '../notification-section/notification-section.component';

@Component({
  selector: 'app-current-reservations',
  standalone: true,
  imports: [CommonModule, NgIf, NgFor, DatePipe, NotificationSectionComponent],
  templateUrl: './current-reservations.component.html',
  styleUrls: ['./current-reservations.component.less']
})
export class CurrentReservationsComponent implements OnInit {
  loading = false;
  error = '';
  reservations: any[] = [];

  constructor(private api: ReservationsService) {}

  ngOnInit(): void {
    this.loading = true;
    this.api.getCurrent().subscribe({
      next: (res:any) => {
        this.reservations = res?.results ?? [];
        this.loading = false;
        console.log(res)
      },
      error: () => {
        this.error = 'Failed to load reservations.';
        this.loading = false;
      }
    });
  }

  cancel(res: any) {
    if (!confirm(`Cancel reservation #${res.id}?`)) return;

    res._busy = true;
    this.api.cancel(res.id).subscribe({
      next: () => {
        // Option A: update status locally and keep it in the list
        // res.status.status = 'cancelled';

        // Option B (common): remove from "active" list after cancel
        this.reservations = this.reservations.filter(r => r.id !== res.id);
      },
      error: () => {
        res._busy = false;
        this.error = `Could not cancel reservation #${res.id}.`;
      }
    });
  }
}
