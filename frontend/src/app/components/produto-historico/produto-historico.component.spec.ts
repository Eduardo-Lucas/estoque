import { TestBed, ComponentFixture } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ProdutoHistoricoComponent } from './produto-historico.component';
import { ProdutoService } from '../../services/produto.service';
import { MovimentacaoService } from '../../services/movimentacao.service';
import { Produto } from '../../models/produto.model';
import { Movimentacao } from '../../models/movimentacao.model';

describe('ProdutoHistoricoComponent', () => {
  let fixture: ComponentFixture<ProdutoHistoricoComponent>;
  let component: ProdutoHistoricoComponent;
  let produtoService: { obter: jest.Mock };
  let movimentacaoService: { listar: jest.Mock };
  let navigate: jest.SpyInstance;

  const produto: Produto = {
    id: 3,
    nome: 'Parafuso 10mm',
    unidade_medida: 'UN',
    saldo: 10,
    estoque_minimo: 5,
    preco_custo_referencia: '1.00',
    preco: '2.50',
    ativo: true,
  };

  const movimentacao: Movimentacao = {
    id: 1,
    produto: 3,
    tipo: 'REQUISICAO',
    quantidade: 2,
    solicitante: 'Ana',
  };

  function configurar() {
    produtoService = { obter: jest.fn().mockReturnValue(of(produto)) };
    movimentacaoService = {
      listar: jest.fn().mockReturnValue(of({ count: 1, next: null, previous: null, results: [movimentacao] })),
    };

    TestBed.configureTestingModule({
      imports: [ProdutoHistoricoComponent],
      providers: [
        provideRouter([]),
        { provide: ProdutoService, useValue: produtoService },
        { provide: MovimentacaoService, useValue: movimentacaoService },
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ id: '3' }) } } },
      ],
    });

    fixture = TestBed.createComponent(ProdutoHistoricoComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  }

  beforeEach(() => configurar());

  it('lê o id do produto a partir da rota', () => {
    expect(component.produtoId).toBe(3);
  });

  it('carrega os dados do produto', () => {
    expect(produtoService.obter).toHaveBeenCalledWith(3);
    expect(component.produto).toEqual(produto);
    expect(component.carregandoProduto).toBe(false);
  });

  it('carrega o histórico de movimentações filtrado pelo produto', () => {
    expect(movimentacaoService.listar).toHaveBeenCalledWith({ produtoId: 3, dataInicio: undefined, dataFim: undefined });
    expect(component.movimentacoes).toEqual([movimentacao]);
    expect(component.carregandoMovimentacoes).toBe(false);
  });

  it('trata erro ao carregar o produto', () => {
    produtoService.obter.mockReturnValue(throwError(() => new Error('falhou')));
    const outraFixture = TestBed.createComponent(ProdutoHistoricoComponent);
    outraFixture.detectChanges();
    expect(outraFixture.componentInstance.erro).toBe('Não foi possível carregar o produto.');
  });

  it('trata erro ao carregar o histórico', () => {
    movimentacaoService.listar.mockReturnValue(throwError(() => new Error('falhou')));
    const outraFixture = TestBed.createComponent(ProdutoHistoricoComponent);
    outraFixture.detectChanges();
    expect(outraFixture.componentInstance.erro).toBe('Não foi possível carregar o histórico de movimentações.');
  });

  it('voltar navega para /produtos', () => {
    component.voltar();
    expect(navigate).toHaveBeenCalledWith(['/produtos']);
  });

  describe('filtro por período', () => {
    function eventoDeValor(valor: string): Event {
      const input = document.createElement('input');
      input.type = 'date';
      input.value = valor;
      return { target: input } as unknown as Event;
    }

    it('temFiltroPeriodo é falso sem nenhum filtro aplicado', () => {
      expect(component.temFiltroPeriodo).toBe(false);
    });

    it('alterarFiltroDataInicio atualiza o filtro e recarrega', () => {
      movimentacaoService.listar.mockClear();
      component.alterarFiltroDataInicio(eventoDeValor('2026-07-01'));

      expect(component.filtroDataInicio).toBe('2026-07-01');
      expect(component.temFiltroPeriodo).toBe(true);
      expect(movimentacaoService.listar).toHaveBeenCalledWith({
        produtoId: 3, dataInicio: '2026-07-01', dataFim: undefined,
      });
    });

    it('alterarFiltroDataFim atualiza o filtro e recarrega', () => {
      movimentacaoService.listar.mockClear();
      component.alterarFiltroDataFim(eventoDeValor('2026-07-31'));

      expect(component.filtroDataFim).toBe('2026-07-31');
      expect(movimentacaoService.listar).toHaveBeenCalledWith({
        produtoId: 3, dataInicio: undefined, dataFim: '2026-07-31',
      });
    });

    it('limparFiltroPeriodo reseta os dois campos e recarrega', () => {
      component.alterarFiltroDataInicio(eventoDeValor('2026-07-01'));
      component.alterarFiltroDataFim(eventoDeValor('2026-07-31'));
      movimentacaoService.listar.mockClear();

      component.limparFiltroPeriodo();

      expect(component.filtroDataInicio).toBe('');
      expect(component.filtroDataFim).toBe('');
      expect(component.temFiltroPeriodo).toBe(false);
      expect(movimentacaoService.listar).toHaveBeenCalledWith({
        produtoId: 3, dataInicio: undefined, dataFim: undefined,
      });
    });
  });
});
