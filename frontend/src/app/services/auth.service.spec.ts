import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { TokenResponse } from '../models/auth.model';
import { AuthService } from './auth.service';

const API_URL = `${environment.apiUrl}/auth/token/`;

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('começa deslogado quando não há token salvo', () => {
    expect(service.autenticado()).toBe(false);
    expect(service.usuario()).toBeNull();
    expect(service.getToken()).toBeNull();
  });

  it('login guarda o token/usuário e atualiza os signals', () => {
    const resposta: TokenResponse = { token: 'abc123' };

    service.login({ email: 'eduardo@example.com', password: 'senha' }).subscribe((r) => expect(r).toEqual(resposta));

    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'eduardo@example.com', password: 'senha' });
    req.flush(resposta);

    expect(service.getToken()).toBe('abc123');
    expect(service.autenticado()).toBe(true);
    expect(service.usuario()).toBe('eduardo@example.com');
    expect(localStorage.getItem('estoque_auth_token')).toBe('abc123');
    expect(localStorage.getItem('estoque_auth_email')).toBe('eduardo@example.com');
  });

  it('logout limpa o token/usuário do storage e dos signals', () => {
    service.login({ email: 'eduardo@example.com', password: 'senha' }).subscribe();
    httpMock.expectOne(API_URL).flush({ token: 'abc123' });

    service.logout();

    expect(service.getToken()).toBeNull();
    expect(service.autenticado()).toBe(false);
    expect(service.usuario()).toBeNull();
    expect(localStorage.getItem('estoque_auth_token')).toBeNull();
    expect(localStorage.getItem('estoque_auth_email')).toBeNull();
  });

  it('recupera a sessão já salva no localStorage ao iniciar', () => {
    localStorage.setItem('estoque_auth_token', 'token-existente');
    localStorage.setItem('estoque_auth_email', 'maria@example.com');

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    const novoServico = TestBed.inject(AuthService);

    expect(novoServico.getToken()).toBe('token-existente');
    expect(novoServico.autenticado()).toBe(true);
    expect(novoServico.usuario()).toBe('maria@example.com');
  });
});
