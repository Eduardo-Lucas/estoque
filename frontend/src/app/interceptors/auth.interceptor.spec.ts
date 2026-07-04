import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  function configurar(token: string | null) {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: { getToken: () => token } },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  }

  afterEach(() => httpMock.verify());

  it('anexa o header Authorization quando há token', () => {
    configurar('abc123');
    http.get('/qualquer-coisa').subscribe();

    const req = httpMock.expectOne('/qualquer-coisa');
    expect(req.request.headers.get('Authorization')).toBe('Token abc123');
    req.flush({});
  });

  it('não anexa o header quando não há token', () => {
    configurar(null);
    http.get('/qualquer-coisa').subscribe();

    const req = httpMock.expectOne('/qualquer-coisa');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });
});
