// import { HttpInterceptorFn } from '@angular/common/http';

// export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
//   const token = localStorage.getItem('access');
//   if (token) {
//     req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
//   }
//   return next(req);
// };

// jwt.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';
import { catchError, switchMap } from 'rxjs/operators';
import { throwError } from 'rxjs';

function attachAuth(req: HttpRequest<any>, token: string | null) {
    return token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
}

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
    const auth = inject(AuthService);

    // attach current access token
    let request = attachAuth(req, localStorage.getItem('access'));

    return next(request).pipe(
        catchError((err: any) => {
            // Only handle 401s from API, and don't loop on the refresh endpoint itself
            const is401 = err instanceof HttpErrorResponse && err.status === 401;
            const isRefreshCall = req.url.includes('/api/auth/refresh/');
            if (!is401 || isRefreshCall) {
                return throwError(() => err);
            }

            // Try refresh once, then retry the original request with new access token
            return auth.refreshToken().pipe(
                switchMap(() => {
                    const retried = attachAuth(req, localStorage.getItem('access'));
                    return next(retried);
                }),
                catchError(e => {
                    // Refresh failed -> propagate the original error
                    return throwError(() => e);
                })
            );
        })
    );
};
