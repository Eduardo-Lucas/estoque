import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { DadosRegistro, TokenResponse } from '../models/auth.model';
import { AuthService } from './auth.service';

const API_URL = `${environment.apiUrl}/auth/token/`;
const API_REGISTRO_URL = `${environment.apiUrl}/auth/registro/`;
const API_CONFIRMAR_EMAIL_URL = `${environment.apiUrl}/auth/confirmar-email/`;

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

  it('registrar envia os dados de conta+empresa e não guarda sessão', () => {
    const dados: DadosRegistro = {
      nome: 'Fulana',
      email: 'fulana@empresa.com',
      password: 'senha-forte-123',
      empresa_razao_social: 'Empresa Nova',
      empresa_cnpj: '11222333000144',
    };

    service.registrar(dados).subscribe((r) => expect(r).toEqual({ detail: 'Cadastro realizado.' }));

    const req = httpMock.expectOne(API_REGISTRO_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(dados);
    req.flush({ detail: 'Cadastro realizado.' });

    expect(service.autenticado()).toBe(false);
    expect(service.getToken()).toBeNull();
  });

  it('confirmarEmail envia uid/token e guarda a sessão com o e-mail devolvido', () => {
    service.confirmarEmail('uid-123', 'token-abc').subscribe();

    const req = httpMock.expectOne(API_CONFIRMAR_EMAIL_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ uid: 'uid-123', token: 'token-abc' });
    req.flush({ token: 'token-sessao', email: 'nova@empresa.com' });

    expect(service.getToken()).toBe('token-sessao');
    expect(service.autenticado()).toBe(true);
    expect(service.usuario()).toBe('nova@empresa.com');
  });
});
