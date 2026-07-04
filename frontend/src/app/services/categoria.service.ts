import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Categoria } from '../models/categoria.model';
import { ResultadoImportacao } from '../models/csv.model';
import { environment } from '../../environments/environment';

const API_URL = `${environment.apiUrl}/categorias/`;

interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class CategoriaService {
  constructor(private http: HttpClient) {}

  // GET /api/categorias/?nome=  -> lista de categorias, com filtro de busca opcional por nome
  listar(filtros?: { nome?: string }): Observable<Paginado<Categoria>> {
    let params = new HttpParams();
    if (filtros?.nome) {
      params = params.set('nome', filtros.nome);
    }
    return this.http.get<Paginado<Categoria>>(API_URL, { params });
  }

  criar(categoria: Categoria): Observable<Categoria> {
    return this.http.post<Categoria>(API_URL, categoria);
  }

  atualizar(id: number, categoria: Categoria): Observable<Categoria> {
    return this.http.put<Categoria>(`${API_URL}${id}/`, categoria);
  }

  remover(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}${id}/`);
  }

  obter(id: number): Observable<Categoria> {
    return this.http.get<Categoria>(`${API_URL}${id}/`);
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
