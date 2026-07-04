import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { provideRouter } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('authGuard', () => {
  function configurar(autenticado: boolean) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { autenticado: () => autenticado } },
      ],
    });
  }

  function executarGuard() {
    return TestBed.runInInjectionContext(() => authGuard({} as any, {} as any));
  }

  it('permite acesso quando o usuário está autenticado', () => {
    configurar(true);
    expect(executarGuard()).toBe(true);
  });

  it('redireciona para /login quando o usuário não está autenticado', () => {
    configurar(false);
    const resultado = executarGuard();

    expect(resultado).not.toBe(true);
    const router = TestBed.inject(Router);
    const esperado = router.createUrlTree(['/login']);
    expect((resultado as UrlTree).toString()).toBe(esperado.toString());
  });
});
