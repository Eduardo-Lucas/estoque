import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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

  listar(): Observable<Paginado<Categoria>> {
    return this.http.get<Paginado<Categoria>>(API_URL);
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
