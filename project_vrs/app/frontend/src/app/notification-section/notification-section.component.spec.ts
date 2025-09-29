import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NotificationSectionComponent } from './notification-section.component';

describe('NotificationSectionComponent', () => {
  let component: NotificationSectionComponent;
  let fixture: ComponentFixture<NotificationSectionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NotificationSectionComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NotificationSectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
