import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Movimentacao } from '../models/movimentacao.model';
import { environment } from '../../environments/environment';

const API_URL = `${environment.apiUrl}/movimentacoes/`;

interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class MovimentacaoService {
  constructor(private http: HttpClient) {}

  // GET /api/movimentacoes/?produto=<id> -> histórico de requisições e devoluções,
  // opcionalmente filtrado por um produto específico
  listar(produtoId?: number): Observable<Paginado<Movimentacao>> {
    const params = produtoId ? new HttpParams().set('produto', produtoId) : undefined;
    return this.http.get<Paginado<Movimentacao>>(API_URL, { params });
  }

  // POST /api/movimentacoes/ -> registra requisição ou devolução
  // O backend ajusta a quantidade do produto automaticamente.
  criar(movimentacao: Movimentacao): Observable<Movimentacao> {
    return this.http.post<Movimentacao>(API_URL, movimentacao);
  }
}
