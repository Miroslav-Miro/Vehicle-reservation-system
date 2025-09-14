import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CurrentReservationsComponent } from './current-reservations.component';

describe('CurrentReservationsComponent', () => {
  let component: CurrentReservationsComponent;
  let fixture: ComponentFixture<CurrentReservationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CurrentReservationsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CurrentReservationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
