import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { Credenciais, TokenResponse } from '../models/auth.model';
import { environment } from '../../environments/environment';

const API_URL = `${environment.apiUrl}/auth/token/`;
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
      .post<TokenResponse>(API_URL, credenciais)
      .pipe(tap((resposta) => this.armazenarSessao(resposta.token, credenciais.email)));
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
    localStorage.setItem(EMAIL_STORAGE_KEY, email);
    this.tokenSignal.set(token);
    this.emailSignal.set(email);
  }
}
