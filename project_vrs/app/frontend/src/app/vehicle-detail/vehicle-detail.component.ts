import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient, HttpParams } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-vehicle-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './vehicle-detail.component.html',
  styleUrls: ['./vehicle-detail.component.less'],
})
export class VehicleDetailComponent implements OnInit {
  vehicleId!: number;
  detail: any = null;
  errorMsg = '';

  constructor(private route: ActivatedRoute, private http: HttpClient) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      this.vehicleId = Number(params.get('id'));
      this.loadDetail();
    });
  }

  private loadDetail(): void {
    // pass through optional filters from query params (location_id, start, end)
    const qp = this.route.snapshot.queryParamMap;

    let httpParams = new HttpParams();
    const loc = qp.get('location_id');
    const start = qp.get('start');
    const end = qp.get('end');

    if (loc) httpParams = httpParams.set('location_id', loc);
    if (start && end) {
      httpParams = httpParams.set('start', start).set('end', end);
    }

    this.http
      .get<any>(`http://localhost:8000/api/public/vehicles/${this.vehicleId}/`, { params: httpParams })
      .subscribe({
        next: (res) => {
          this.detail = res;
          this.errorMsg = '';
        },
        error: (err) => {
          console.error(err);
          this.errorMsg = err?.error?.detail || 'Failed to load vehicle.';
        },
      });
  }
}
