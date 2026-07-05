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

export interface FiltroMovimentacao {
  produtoId?: number;
  dataInicio?: string;
  dataFim?: string;
}

@Injectable({ providedIn: 'root' })
export class MovimentacaoService {
  constructor(private http: HttpClient) {}

  // GET /api/movimentacoes/?produto=<id>&data_inicio=AAAA-MM-DD&data_fim=AAAA-MM-DD
  // -> histórico de movimentações, opcionalmente filtrado por produto e/ou período
  listar(filtro?: FiltroMovimentacao): Observable<Paginado<Movimentacao>> {
    let params = new HttpParams();
    if (filtro?.produtoId) {
      params = params.set('produto', filtro.produtoId);
    }
    if (filtro?.dataInicio) {
      params = params.set('data_inicio', filtro.dataInicio);
    }
    if (filtro?.dataFim) {
      params = params.set('data_fim', filtro.dataFim);
    }
    return this.http.get<Paginado<Movimentacao>>(API_URL, { params });
  }

  // POST /api/movimentacoes/ -> registra a movimentação.
  // O backend recalcula o saldo (SaldoEstoque) automaticamente a partir do ledger.
  criar(movimentacao: Movimentacao): Observable<Movimentacao> {
    return this.http.post<Movimentacao>(API_URL, movimentacao);
  }
}
