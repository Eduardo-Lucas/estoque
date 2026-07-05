import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { Movimentacao } from '../models/movimentacao.model';
import { MovimentacaoService } from './movimentacao.service';

const API_URL = `${environment.apiUrl}/movimentacoes/`;

describe('MovimentacaoService', () => {
  let service: MovimentacaoService;
  let httpMock: HttpTestingController;

  const movimentacao: Movimentacao = {
    id: 1,
    produto: 5,
    tipo: 'REQUISICAO',
    quantidade: 2,
    solicitante: 'Ana',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MovimentacaoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lista movimentações sem filtro', () => {
    service.listar().subscribe((resposta) => expect(resposta.results).toEqual([movimentacao]));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.has('produto')).toBe(false);
    req.flush({ count: 1, next: null, previous: null, results: [movimentacao] });
  });

  it('lista movimentações filtradas por produto', () => {
    service.listar({ produtoId: 5 }).subscribe((resposta) => expect(resposta.results).toEqual([movimentacao]));
    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.params.get('produto')).toBe('5');
    req.flush({ count: 1, next: null, previous: null, results: [movimentacao] });
  });

  it('lista movimentações filtradas por período', () => {
    service.listar({ produtoId: 5, dataInicio: '2026-07-01', dataFim: '2026-07-31' }).subscribe();
    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.params.get('produto')).toBe('5');
    expect(req.request.params.get('data_inicio')).toBe('2026-07-01');
    expect(req.request.params.get('data_fim')).toBe('2026-07-31');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('não envia parâmetros de período quando vazios', () => {
    service.listar({ produtoId: 5 }).subscribe();
    const req = httpMock.expectOne((r) => r.url === API_URL);
    expect(req.request.params.has('data_inicio')).toBe(false);
    expect(req.request.params.has('data_fim')).toBe(false);
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('registra uma movimentação via POST', () => {
    service.criar(movimentacao).subscribe((resposta) => expect(resposta).toEqual(movimentacao));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(movimentacao);
    req.flush(movimentacao);
  });
});
