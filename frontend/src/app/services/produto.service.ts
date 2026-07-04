import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Produto } from '../models/produto.model';
import { ResultadoImportacao } from '../models/csv.model';
import { ResultadoImportacaoNfe } from '../models/nfe.model';
import { environment } from '../../environments/environment';

const API_URL = `${environment.apiUrl}/produtos/`;

interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

@Injectable({ providedIn: 'root' })
export class ProdutoService {
  constructor(private http: HttpClient) {}

  // GET /api/produtos/?page=&page_size=  -> lista paginada de produtos
  listar(pagina: number = 1, tamanhoPagina: number = 10): Observable<Paginado<Produto>> {
    const params = new HttpParams().set('page', pagina).set('page_size', tamanhoPagina);
    return this.http.get<Paginado<Produto>>(API_URL, { params });
  }

  // POST /api/produtos/  -> cria um novo produto
  criar(produto: Produto): Observable<Produto> {
    return this.http.post<Produto>(API_URL, produto);
  }

  // PUT /api/produtos/{id}/  -> atualiza um produto existente
  atualizar(id: number, produto: Produto): Observable<Produto> {
    return this.http.put<Produto>(`${API_URL}${id}/`, produto);
  }

  // DELETE /api/produtos/{id}/  -> remove um produto
  remover(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}${id}/`);
  }

  // GET /api/produtos/{id}/  -> detalhe de um produto (usado pelo AsyncValidator de estoque)
  obter(id: number): Observable<Produto> {
    return this.http.get<Produto>(`${API_URL}${id}/`);
  }

  // POST /api/produtos/importar_csv/  -> importação em lote via arquivo CSV
  importarCsv(arquivo: File): Observable<ResultadoImportacao> {
    const formData = new FormData();
    formData.append('arquivo', arquivo);
    return this.http.post<ResultadoImportacao>(`${API_URL}importar_csv/`, formData);
  }

  // GET /api/produtos/exportar_csv/  -> exporta todos os produtos como CSV
  exportarCsv(): Observable<Blob> {
    return this.http.get(`${API_URL}exportar_csv/`, { responseType: 'blob' });
  }

  // POST /api/produtos/importar_nfe/  -> dá entrada em estoque a partir do XML de uma NF-e de compra
  importarNfe(arquivo: File): Observable<ResultadoImportacaoNfe> {
    const formData = new FormData();
    formData.append('arquivo', arquivo);
    return this.http.post<ResultadoImportacaoNfe>(`${API_URL}importar_nfe/`, formData);
  }
}
