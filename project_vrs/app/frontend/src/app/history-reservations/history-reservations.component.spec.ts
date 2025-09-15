import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HistoryReservationsComponent } from './history-reservations.component';

describe('HistoryReservationsComponent', () => {
  let component: HistoryReservationsComponent;
  let fixture: ComponentFixture<HistoryReservationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HistoryReservationsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HistoryReservationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
