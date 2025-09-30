import { inject, Injectable } from '@angular/core';
import { CanMatch, Router, UrlTree } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class GuestGuard implements CanMatch {
  private auth = inject(AuthService);
  private router = inject(Router);

  canMatch(): boolean | UrlTree {
    // If logged in, redirect away from auth pages
    return this.auth.isAuthenticated() ? this.router.parseUrl('/') : true;
  }
}
