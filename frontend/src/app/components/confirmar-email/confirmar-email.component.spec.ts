import { TestBed, ComponentFixture } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ConfirmarEmailComponent } from './confirmar-email.component';
import { AuthService } from '../../services/auth.service';

describe('ConfirmarEmailComponent', () => {
  let fixture: ComponentFixture<ConfirmarEmailComponent>;
  let component: ConfirmarEmailComponent;
  let authService: { confirmarEmail: jest.Mock };
  let navigate: jest.SpyInstance;

  function configurar() {
    TestBed.configureTestingModule({
      imports: [ConfirmarEmailComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authService },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ uid: 'uid-123', token: 'token-abc' }) } },
        },
      ],
    });

    fixture = TestBed.createComponent(ConfirmarEmailComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  }

  it('confirma com uid/token da rota e navega pra /produtos em caso de sucesso', () => {
    authService = { confirmarEmail: jest.fn().mockReturnValue(of({ token: 'abc', email: 'nova@empresa.com' })) };
    configurar();

    expect(authService.confirmarEmail).toHaveBeenCalledWith('uid-123', 'token-abc');
    expect(navigate).toHaveBeenCalledWith(['/produtos']);
    expect(component.confirmando).toBe(true);
  });

  it('exibe erro e para de mostrar "confirmando" quando a confirmação falha', () => {
    authService = { confirmarEmail: jest.fn().mockReturnValue(throwError(() => new Error('Link de confirmação inválido.'))) };
    configurar();

    expect(component.confirmando).toBe(false);
    expect(component.erro).toBe('Link de confirmação inválido.');
    expect(navigate).not.toHaveBeenCalled();
  });
});
