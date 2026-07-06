import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from '../../services/auth.service';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let component: LoginComponent;
  let authService: { login: jest.Mock };
  let navigate: jest.SpyInstance;

  beforeEach(async () => {
    authService = { login: jest.fn() };

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [provideRouter([]), { provide: AuthService, useValue: authService }],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('não chama o serviço e marca os campos como tocados quando o form é inválido', () => {
    component.entrar();

    expect(authService.login).not.toHaveBeenCalled();
    expect(component.form.get('email')?.touched).toBe(true);
    expect(component.form.get('password')?.touched).toBe(true);
  });

  it('login bem-sucedido navega para /produtos', () => {
    authService.login.mockReturnValue(of({ token: 'abc' }));
    component.form.setValue({ email: 'eduardo@example.com', password: 'senha123' });

    component.entrar();

    expect(authService.login).toHaveBeenCalledWith({ email: 'eduardo@example.com', password: 'senha123' });
    expect(component.carregando).toBe(false);
    expect(navigate).toHaveBeenCalledWith(['/produtos']);
  });

  it('login com erro exibe a mensagem e não navega', () => {
    authService.login.mockReturnValue(throwError(() => new Error('Credenciais inválidas.')));
    component.form.setValue({ email: 'eduardo@example.com', password: 'errada' });

    component.entrar();

    expect(component.erro).toBe('Credenciais inválidas.');
    expect(component.carregando).toBe(false);
    expect(navigate).not.toHaveBeenCalled();
  });

  it('alterna a visibilidade da senha', () => {
    expect(component.senhaVisivel).toBe(false);
    component.alternarVisibilidadeSenha();
    expect(component.senhaVisivel).toBe(true);
  });
});

describe('LoginComponent (vindo do registro)', () => {
  it('mostra aviso de conta criada quando a query param "criado" está presente', async () => {
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { login: jest.fn() } },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { queryParamMap: convertToParamMap({ criado: '1' }) } },
        },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(LoginComponent);
    jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();

    expect(fixture.componentInstance.mensagem).toBe('Conta criada! Faça login para continuar.');
  });
});
