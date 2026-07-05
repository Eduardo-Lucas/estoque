import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { Categoria } from '../models/categoria.model';
import { CategoriaService } from './categoria.service';

const API_URL = `${environment.apiUrl}/categorias/`;

describe('CategoriaService', () => {
  let service: CategoriaService;
  let httpMock: HttpTestingController;

  const categoria: Categoria = { id: 1, nome: 'Ferragens', descricao: 'Parafusos e afins' };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CategoriaService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lista categorias', () => {
    service.listar().subscribe((resposta) => expect(resposta.results).toEqual([categoria]));
    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.has('nome')).toBe(false);
    req.flush({ count: 1, next: null, previous: null, results: [categoria] });
  });

  it('envia o filtro de nome quando informado', () => {
    service.listar({ nome: 'ferrag' }).subscribe();
    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.params.get('nome')).toBe('ferrag');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('cria uma categoria via POST', () => {
    service.criar(categoria).subscribe((resposta) => expect(resposta).toEqual(categoria));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(categoria);
    req.flush(categoria);
  });

  it('atualiza uma categoria via PUT', () => {
    service.atualizar(1, categoria).subscribe();
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('PUT');
    req.flush(categoria);
  });

  it('inativa uma categoria via DELETE', () => {
    service.inativar(1).subscribe();
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('obtém uma categoria por id', () => {
    service.obter(1).subscribe((resposta) => expect(resposta).toEqual(categoria));
    const req = httpMock.expectOne(`${API_URL}1/`);
    req.flush(categoria);
  });

  it('envia o CSV para importar_csv como multipart', () => {
    const arquivo = new File(['nome,descricao\nFerragens,x'], 'categorias.csv', { type: 'text/csv' });
    service.importarCsv(arquivo).subscribe();
    const req = httpMock.expectOne(`${API_URL}importar_csv/`);
    expect(req.request.method).toBe('POST');
    expect((req.request.body as FormData).get('arquivo')).toBe(arquivo);
    req.flush({ criados: 1, atualizados: 0, erros: [] });
  });

  it('exporta CSV como blob', () => {
    service.exportarCsv().subscribe();
    const req = httpMock.expectOne(`${API_URL}exportar_csv/`);
    expect(req.request.responseType).toBe('blob');
    req.flush(new Blob());
  });
});
