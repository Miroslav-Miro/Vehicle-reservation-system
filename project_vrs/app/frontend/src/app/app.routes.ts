import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { LoginComponent } from './auth/login/login.component';
import { VehicleListComponent } from './vehicle-list/vehicle-list.component';
import { RegisterComponent } from './auth/register/register.component';
import { CurrentReservationsComponent } from './current-reservations/current-reservations.component';
import { HistoryReservationsComponent } from './history-reservations/history-reservations.component';
import { VehicleDetailComponent } from './vehicle-detail/vehicle-detail.component';
import { NotificationSectionComponent } from './notification-section/notification-section.component';
import { AuthGuard } from './auth/auth.guard';
import { AdminGuard } from './auth/admin.guard';
import { ManagerGuard } from './auth/manager.guard';
import { GuestGuard } from './auth/guest.guard';
// import { AdminDashboardComponent } from './admin/admin-dashboard.component';
// import { ManagerDashboardComponent } from './manager/manager-dashboard.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'vehicles', component: VehicleListComponent },
  { path: 'vehicles/:id', component: VehicleDetailComponent },
  { path: 'auth/login', component: LoginComponent, canMatch: [GuestGuard] },
  { path: 'auth/register', component: RegisterComponent, canMatch: [GuestGuard] },
  { path: 'reservations/current',component: CurrentReservationsComponent, canActivate: [AuthGuard]},
  { path: 'reservations/history', component: HistoryReservationsComponent, canActivate: [AuthGuard]},
  { path: 'notifications', component:NotificationSectionComponent, canActivate: [AuthGuard]},


  // Protected routes

  // Admin-only
//   { path: 'admin', component: AdminDashboardComponent, canActivate: [AdminGuard] },

  // Manager-only
//   { path: 'manager', component: ManagerDashboardComponent, canActivate: [ManagerGuard] },

  // { path: '**', redirectTo: '', pathMatch: 'full'  }
];
