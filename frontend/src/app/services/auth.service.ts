import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { Credenciais, DadosRegistro, RespostaRegistro, TokenResponse } from '../models/auth.model';
import { environment } from '../../environments/environment';

const API_AUTH_URL = `${environment.apiUrl}/auth`;
const STORAGE_KEY = 'estoque_auth_token';
const EMAIL_STORAGE_KEY = 'estoque_auth_email';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly tokenSignal = signal<string | null>(localStorage.getItem(STORAGE_KEY));
  private readonly emailSignal = signal<string | null>(localStorage.getItem(EMAIL_STORAGE_KEY));

  readonly autenticado = computed(() => !!this.tokenSignal());
  readonly usuario = computed(() => this.emailSignal());

  constructor(private http: HttpClient) {}

  login(credenciais: Credenciais): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${API_AUTH_URL}/token/`, credenciais)
      .pipe(tap((resposta) => this.armazenarSessao(resposta.token, credenciais.email)));
  }

  // POST /api/auth/registro/ -> cria a conta e a empresa; a conta nasce
  // inativa, então isso NÃO guarda sessão — só depois de confirmarEmail().
  registrar(dados: DadosRegistro): Observable<RespostaRegistro> {
    return this.http.post<RespostaRegistro>(`${API_AUTH_URL}/registro/`, dados);
  }

  // POST /api/auth/confirmar-email/ -> confirma a conta e já loga (a resposta
  // tem o mesmo formato do login).
  confirmarEmail(uid: string, token: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${API_AUTH_URL}/confirmar-email/`, { uid, token })
      .pipe(tap((resposta) => this.armazenarSessao(resposta.token, resposta.email ?? '')));
  }

  logout(): void {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(EMAIL_STORAGE_KEY);
    this.tokenSignal.set(null);
    this.emailSignal.set(null);
  }

  getToken(): string | null {
    return this.tokenSignal();
  }

  private armazenarSessao(token: string, email: string): void {
    localStorage.setItem(STORAGE_KEY, token);
    this.tokenSignal.set(token);
    if (email) {
      localStorage.setItem(EMAIL_STORAGE_KEY, email);
      this.emailSignal.set(email);
    }
  }
}
