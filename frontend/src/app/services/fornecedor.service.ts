import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Fornecedor } from '../models/fornecedor.model';
import { ResultadoImportacao } from '../models/csv.model';
import { environment } from '../../environments/environment';

const API_URL = `${environment.apiUrl}/fornecedores/`;

interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class FornecedorService {
  constructor(private http: HttpClient) {}

  // GET /api/fornecedores/?nome=  -> lista de fornecedores, com filtro de busca opcional por nome
  listar(filtros?: { nome?: string }): Observable<Paginado<Fornecedor>> {
    let params = new HttpParams();
    if (filtros?.nome) {
      params = params.set('nome', filtros.nome);
    }
    return this.http.get<Paginado<Fornecedor>>(API_URL, { params });
  }

  criar(fornecedor: Fornecedor): Observable<Fornecedor> {
    return this.http.post<Fornecedor>(API_URL, fornecedor);
  }

  atualizar(id: number, fornecedor: Fornecedor): Observable<Fornecedor> {
    return this.http.put<Fornecedor>(`${API_URL}${id}/`, fornecedor);
  }

  // DELETE /api/fornecedores/{id}/  -> inativa o fornecedor (define ativo=false; não remove o registro)
  inativar(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}${id}/`);
  }

  obter(id: number): Observable<Fornecedor> {
    return this.http.get<Fornecedor>(`${API_URL}${id}/`);
  }

  importarCsv(arquivo: File): Observable<ResultadoImportacao> {
    const formData = new FormData();
    formData.append('arquivo', arquivo);
    return this.http.post<ResultadoImportacao>(`${API_URL}importar_csv/`, formData);
  }

  exportarCsv(): Observable<Blob> {
    return this.http.get(`${API_URL}exportar_csv/`, { responseType: 'blob' });
  }
}
