import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { LoginComponent } from './auth/login/login.component';
import { RegisterComponent } from './auth/register/register.component';
import { AuthGuard } from './auth/auth.guard';
import { AdminGuard } from './auth/admin.guard';
import { ManagerGuard } from './auth/manager.guard';
// import { AdminDashboardComponent } from './admin/admin-dashboard.component';
// import { ManagerDashboardComponent } from './manager/manager-dashboard.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'auth/login', component: LoginComponent },
  { path: 'auth/register', component: RegisterComponent },
  { path: '', component: HomeComponent },

  // Protected routes

  // Admin-only
//   { path: 'admin', component: AdminDashboardComponent, canActivate: [AdminGuard] },

  // Manager-only
//   { path: 'manager', component: ManagerDashboardComponent, canActivate: [ManagerGuard] },

  { path: '**', redirectTo: '' }
];
