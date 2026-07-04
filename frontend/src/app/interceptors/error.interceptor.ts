import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) {
        auth.logout();
        router.navigate(['/login']);
      }
      return throwError(() => new Error(extrairMensagem(err)));
    }),
  );
};

function extrairMensagem(err: HttpErrorResponse): string {
  if (err?.error?.non_field_errors?.length) {
    return err.error.non_field_errors[0];
  }
  if (err?.error && typeof err.error === 'object') {
    const primeiraChave = Object.keys(err.error)[0];
    const valor = err.error[primeiraChave];
    return Array.isArray(valor) ? valor[0] : String(valor);
  }
  return 'Ocorreu um erro inesperado. Tente novamente.';
}
