import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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

  // GET /api/movimentacoes/ -> histórico de requisições e devoluções
  listar(): Observable<Paginado<Movimentacao>> {
    return this.http.get<Paginado<Movimentacao>>(API_URL);
  }

  // POST /api/movimentacoes/ -> registra requisição ou devolução
  // O backend ajusta a quantidade do produto automaticamente.
  criar(movimentacao: Movimentacao): Observable<Movimentacao> {
    return this.http.post<Movimentacao>(API_URL, movimentacao);
  }
}
