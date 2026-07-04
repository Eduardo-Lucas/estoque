import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { Produto } from '../models/produto.model';
import { ResultadoImportacao } from '../models/csv.model';
import { ProdutoService } from './produto.service';

const API_URL = `${environment.apiUrl}/produtos/`;

describe('ProdutoService', () => {
  let service: ProdutoService;
  let httpMock: HttpTestingController;

  const produto: Produto = {
    id: 1,
    nome: 'Parafuso 10mm',
    unidade_medida: 'UN',
    quantidade: 10,
    estoque_minimo: 0,
    preco_custo: '1.00',
    preco: '2.50',
    ativo: true,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ProdutoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lista produtos com parâmetros de paginação', () => {
    service.listar(2, 20).subscribe((resposta) => {
      expect(resposta.results).toEqual([produto]);
    });

    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('page')).toBe('2');
    expect(req.request.params.get('page_size')).toBe('20');
    req.flush({ count: 1, next: null, previous: null, results: [produto] });
  });

  it('usa página 1 e tamanho 10 por padrão', () => {
    service.listar().subscribe();
    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.params.get('page')).toBe('1');
    expect(req.request.params.get('page_size')).toBe('10');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('cria um produto via POST', () => {
    service.criar(produto).subscribe((resposta) => expect(resposta).toEqual(produto));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(produto);
    req.flush(produto);
  });

  it('atualiza um produto via PUT no endpoint com id', () => {
    service.atualizar(1, produto).subscribe();
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('PUT');
    req.flush(produto);
  });

  it('remove um produto via DELETE', () => {
    service.remover(1).subscribe();
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('obtém um produto por id', () => {
    service.obter(1).subscribe((resposta) => expect(resposta).toEqual(produto));
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('GET');
    req.flush(produto);
  });

  it('envia o arquivo CSV como multipart no campo "arquivo"', () => {
    const arquivo = new File(['nome,quantidade\nX,1'], 'produtos.csv', { type: 'text/csv' });
    const resultado: ResultadoImportacao = { criados: 1, atualizados: 0, erros: [] };

    service.importarCsv(arquivo).subscribe((resposta) => expect(resposta).toEqual(resultado));

    const req = httpMock.expectOne(`${API_URL}importar_csv/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBe(true);
    expect((req.request.body as FormData).get('arquivo')).toBe(arquivo);
    req.flush(resultado);
  });

  it('exporta CSV esperando um blob como resposta', () => {
    const blob = new Blob(['nome,quantidade\n']);
    service.exportarCsv().subscribe((resposta) => expect(resposta).toEqual(blob));

    const req = httpMock.expectOne(`${API_URL}exportar_csv/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.responseType).toBe('blob');
    req.flush(blob);
  });
});
