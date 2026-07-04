import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { Fornecedor } from '../models/fornecedor.model';
import { FornecedorService } from './fornecedor.service';

const API_URL = `${environment.apiUrl}/fornecedores/`;

describe('FornecedorService', () => {
  let service: FornecedorService;
  let httpMock: HttpTestingController;

  const fornecedor: Fornecedor = { id: 1, nome: 'Distribuidora ABC', email: 'contato@abc.com' };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(FornecedorService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lista fornecedores', () => {
    service.listar().subscribe((resposta) => expect(resposta.results).toEqual([fornecedor]));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [fornecedor] });
  });

  it('cria um fornecedor via POST', () => {
    service.criar(fornecedor).subscribe((resposta) => expect(resposta).toEqual(fornecedor));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('POST');
    req.flush(fornecedor);
  });

  it('atualiza um fornecedor via PUT', () => {
    service.atualizar(1, fornecedor).subscribe();
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('PUT');
    req.flush(fornecedor);
  });

  it('remove um fornecedor via DELETE', () => {
    service.remover(1).subscribe();
    const req = httpMock.expectOne(`${API_URL}1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('obtém um fornecedor por id', () => {
    service.obter(1).subscribe((resposta) => expect(resposta).toEqual(fornecedor));
    const req = httpMock.expectOne(`${API_URL}1/`);
    req.flush(fornecedor);
  });

  it('envia o CSV para importar_csv como multipart', () => {
    const arquivo = new File(['nome,cnpj\nABC,123'], 'fornecedores.csv', { type: 'text/csv' });
    service.importarCsv(arquivo).subscribe();
    const req = httpMock.expectOne(`${API_URL}importar_csv/`);
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
