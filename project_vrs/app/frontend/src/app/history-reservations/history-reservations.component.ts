import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe, NgFor, NgIf } from '@angular/common';
import { ReservationsService } from '../reservations/reservation.service';
import { NotificationSectionComponent } from '../notification-section/notification-section.component';
@Component({
  selector: 'app-history-reservations',
  standalone: true,
  imports: [CommonModule, NgIf, NgFor, DatePipe, NotificationSectionComponent],
  templateUrl: './history-reservations.component.html',
  styleUrls: ['./history-reservations.component.less']   
})
export class HistoryReservationsComponent implements OnInit {
  loading = false;
  error = '';
  reservations: any[] = [];

  constructor(private api: ReservationsService) {}

  ngOnInit(): void {
    this.loading = true;
    this.api.getHistory().subscribe({
      next: (res: any) => {
        this.reservations = res?.results ?? [];
        this.loading = false;
        console.log(res);
      },
      error: () => {
        this.error = 'Failed to load reservations.';
        this.loading = false;
      }
    });
  }
}
