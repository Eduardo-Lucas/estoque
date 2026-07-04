import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { errorInterceptor } from './error.interceptor';
import { AuthService } from '../services/auth.service';

describe('errorInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let logout: jest.Mock;
  let navigate: jest.SpyInstance;

  beforeEach(() => {
    logout = jest.fn();

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([errorInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: AuthService, useValue: { logout } },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
  });

  afterEach(() => httpMock.verify());

  it('em 401: desloga e redireciona para /login', (done) => {
    http.get('/protegido').subscribe({
      error: () => {
        expect(logout).toHaveBeenCalled();
        expect(navigate).toHaveBeenCalledWith(['/login']);
        done();
      },
    });

    httpMock.expectOne('/protegido').flush({}, { status: 401, statusText: 'Unauthorized' });
  });

  it('em erro diferente de 401: não desloga nem redireciona', (done) => {
    http.get('/produtos').subscribe({
      error: () => {
        expect(logout).not.toHaveBeenCalled();
        expect(navigate).not.toHaveBeenCalled();
        done();
      },
    });

    httpMock.expectOne('/produtos').flush({}, { status: 500, statusText: 'Server Error' });
  });

  it('extrai a mensagem de non_field_errors do DRF', (done) => {
    http.post('/auth/token/', {}).subscribe({
      error: (err) => {
        expect(err.message).toBe('Credenciais inválidas.');
        done();
      },
    });

    httpMock.expectOne('/auth/token/').flush(
      { non_field_errors: ['Credenciais inválidas.'] },
      { status: 400, statusText: 'Bad Request' },
    );
  });

  it('extrai a mensagem do primeiro campo com erro de validação', (done) => {
    http.post('/produtos/', {}).subscribe({
      error: (err) => {
        expect(err.message).toBe('Já existe um produto com esse nome.');
        done();
      },
    });

    httpMock.expectOne('/produtos/').flush(
      { nome: ['Já existe um produto com esse nome.'] },
      { status: 400, statusText: 'Bad Request' },
    );
  });

  it('usa mensagem genérica quando o corpo do erro não é reconhecido', (done) => {
    http.get('/produtos/').subscribe({
      error: (err) => {
        expect(err.message).toBe('Ocorreu um erro inesperado. Tente novamente.');
        done();
      },
    });

    httpMock.expectOne('/produtos/').flush(null, { status: 500, statusText: 'Server Error' });
  });
});
