import { TestBed, ComponentFixture } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ProdutoListComponent } from './produto-list.component';
import { ProdutoService } from '../../services/produto.service';
import { Produto } from '../../models/produto.model';

describe('ProdutoListComponent', () => {
  let fixture: ComponentFixture<ProdutoListComponent>;
  let component: ProdutoListComponent;
  let produtoService: {
    listar: jest.Mock;
    remover: jest.Mock;
  };
  let navigate: jest.SpyInstance;

  const produto: Produto = {
    id: 1,
    nome: 'Parafuso 10mm',
    unidade_medida: 'UN',
    quantidade: 10,
    estoque_minimo: 5,
    preco_custo: '1.00',
    preco: '2.50',
    ativo: true,
  };

  function respostaPaginada(results: Produto[], count = results.length) {
    return { count, next: null, previous: null, results };
  }

  beforeEach(async () => {
    produtoService = {
      listar: jest.fn().mockReturnValue(of(respostaPaginada([produto]))),
      remover: jest.fn().mockReturnValue(of(undefined)),
    };

    await TestBed.configureTestingModule({
      imports: [ProdutoListComponent],
      providers: [provideRouter([]), { provide: ProdutoService, useValue: produtoService }],
    }).compileComponents();

    fixture = TestBed.createComponent(ProdutoListComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('carrega os produtos ao iniciar', () => {
    expect(produtoService.listar).toHaveBeenCalledWith(1, 10);
    expect(component.produtos).toEqual([produto]);
    expect(component.totalRegistros).toBe(1);
    expect(component.carregando).toBe(false);
  });

  it('exibe mensagem de erro quando a listagem falha', () => {
    produtoService.listar.mockReturnValue(throwError(() => new Error('falhou')));
    component.carregar();
    expect(component.erro).toContain('backend');
    expect(component.carregando).toBe(false);
  });

  it('volta uma página quando a página atual fica vazia após navegação', () => {
    component.pagina = 2;
    produtoService.listar.mockReturnValue(of(respostaPaginada([], 0)));
    component.carregar();
    expect(component.pagina).toBe(1);
  });

  it('calcula o total de páginas com base no total de registros', () => {
    component.totalRegistros = 25;
    component.tamanhoPagina = 10;
    expect(component.totalPaginas).toBe(3);
  });

  it('criarProduto navega para /produtos/novo', () => {
    component.criarProduto();
    expect(navigate).toHaveBeenCalledWith(['/produtos/novo']);
  });

  it('editar navega para /produtos/:id/editar', () => {
    component.editar(produto);
    expect(navigate).toHaveBeenCalledWith(['/produtos', produto.id, 'editar']);
  });

  it('verHistorico navega para /produtos/:id/historico', () => {
    component.verHistorico(produto);
    expect(navigate).toHaveBeenCalledWith(['/produtos', produto.id, 'historico']);
  });

  it('proximaPagina avança e recarrega quando não é a última página', () => {
    component.totalRegistros = 30;
    component.tamanhoPagina = 10;
    component.pagina = 1;
    component.proximaPagina();
    expect(component.pagina).toBe(2);
  });

  it('proximaPagina não avança além da última página', () => {
    component.totalRegistros = 10;
    component.tamanhoPagina = 10;
    component.pagina = 1;
    component.proximaPagina();
    expect(component.pagina).toBe(1);
  });

  it('paginaAnterior não recua abaixo da página 1', () => {
    component.pagina = 1;
    component.paginaAnterior();
    expect(component.pagina).toBe(1);
  });

  describe('remoção', () => {
    it('pedirRemocao guarda o produto e cancelarRemocao limpa', () => {
      component.pedirRemocao(produto);
      expect(component.produtoParaRemover).toEqual(produto);
      component.cancelarRemocao();
      expect(component.produtoParaRemover).toBeNull();
    });

    it('confirmarRemocao remove o produto e recarrega a lista', () => {
      component.pedirRemocao(produto);
      component.confirmarRemocao();

      expect(produtoService.remover).toHaveBeenCalledWith(produto.id);
      expect(component.sucesso).toBe('Produto removido com sucesso.');
      expect(component.produtoParaRemover).toBeNull();
    });

    it('confirmarRemocao trata erro do backend', () => {
      produtoService.remover.mockReturnValue(throwError(() => new Error('falha ao remover')));
      component.pedirRemocao(produto);
      component.confirmarRemocao();

      expect(component.erro).toBe('falha ao remover');
      expect(component.produtoParaRemover).toBeNull();
    });
  });
});
