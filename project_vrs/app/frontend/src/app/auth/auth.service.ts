import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { BehaviorSubject } from 'rxjs';
import { apiBase } from '../shared/api';
import { throwError } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = `${apiBase()}/auth`;
  private role: string | null = null;

  private _isAuthed$ = new BehaviorSubject<boolean>(!!localStorage.getItem('access'));
  isAuthed$ = this._isAuthed$.asObservable()

  constructor(private http: HttpClient) {}

  login(username: string, password: string) {
    return this.http.post(`${this.apiUrl}/login/`, { username, password }).pipe(
      tap((res: any) => {
        localStorage.setItem('access', res.access);
        localStorage.setItem('refresh', res.refresh);
        localStorage.setItem('role', res.role);
        this.role = res.role;

        this._isAuthed$.next(true);
      })
    );
  }
  register(data: any) {
    return this.http.post(`${this.apiUrl}/register/`, data);
  }

  refreshToken() {
    const refresh = localStorage.getItem('refresh');
    if (!refresh) return throwError(() => new Error('No refresh token'));
    return this.http.post<any>(`${apiBase()}/auth/refresh/`, { refresh }).pipe(
      tap(res => {
        if (res.access) localStorage.setItem('access', res.access);
      })
    );
  }


  logout() {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('role');
    this.role = null;
    this._isAuthed$.next(false);
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
