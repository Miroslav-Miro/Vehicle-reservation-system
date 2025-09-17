import { Component } from '@angular/core';
import { LocationService } from '../services/location.service';
import { Location } from '../services/location.service';
import { Observable } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { OnInit } from '@angular/core';

@Component({
  selector: 'app-home',
  standalone: true,  
  imports: [CommonModule,FormsModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.less'
})
export class HomeComponent implements OnInit {
  locations$!: Observable<Location[]>;
  pickup: Location | null = null;   // <-- needed

  constructor(private locationService: LocationService) {}

  ngOnInit(): void {
    this.locations$ = this.locationService.getAll(); // returns array (see Option A)
  }
}
