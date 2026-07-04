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

  it('lista movimentações', () => {
    service.listar().subscribe((resposta) => expect(resposta.results).toEqual([movimentacao]));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [movimentacao] });
  });

  it('registra uma movimentação via POST', () => {
    service.criar(movimentacao).subscribe((resposta) => expect(resposta).toEqual(movimentacao));
    const req = httpMock.expectOne(API_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(movimentacao);
    req.flush(movimentacao);
  });
});
