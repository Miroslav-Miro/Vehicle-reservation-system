import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = 'http://localhost:8000/api/auth';
  private role: string | null = null;

  constructor(private http: HttpClient) {}

  login(username: string, password: string) {
    return this.http.post(`${this.apiUrl}/login/`, { username, password }).pipe(
      tap((res: any) => {
        localStorage.setItem('access', res.access);
        localStorage.setItem('refresh', res.refresh);
        localStorage.setItem('role', res.role);
        this.role = res.role;
      })
    );
  }

  logout() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('role');
    this.role = null;
  }

  getRole(): string | null {
    if (!this.role) {
      this.role = localStorage.getItem('role');
    }
    return this.role;
  }

  isAdmin(): boolean {
    return this.getRole() === 'admin';
  }

  isManager(): boolean {
    return this.getRole() === 'manager';
  }

  isUser(): boolean {
    return this.getRole() === 'user';
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access');
  }
}
