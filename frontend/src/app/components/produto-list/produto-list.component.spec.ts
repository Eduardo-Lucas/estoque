import { TestBed, ComponentFixture } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ProdutoListComponent } from './produto-list.component';
import { ProdutoService } from '../../services/produto.service';
import { CategoriaService } from '../../services/categoria.service';
import { FornecedorService } from '../../services/fornecedor.service';
import { Produto } from '../../models/produto.model';
import { Categoria } from '../../models/categoria.model';
import { Fornecedor } from '../../models/fornecedor.model';

describe('ProdutoListComponent', () => {
  let fixture: ComponentFixture<ProdutoListComponent>;
  let component: ProdutoListComponent;
  let produtoService: {
    listar: jest.Mock;
    inativar: jest.Mock;
  };
  let categoriaService: { listar: jest.Mock };
  let fornecedorService: { listar: jest.Mock };
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

  const categoria: Categoria = { id: 2, nome: 'Ferragens' };
  const fornecedor: Fornecedor = { id: 3, nome: 'Distribuidora ABC' };

  function respostaPaginada<T>(results: T[], count = results.length) {
    return { count, next: null, previous: null, results };
  }

  beforeEach(async () => {
    produtoService = {
      listar: jest.fn().mockReturnValue(of(respostaPaginada([produto]))),
      inativar: jest.fn().mockReturnValue(of(undefined)),
    };
    categoriaService = { listar: jest.fn().mockReturnValue(of(respostaPaginada([categoria]))) };
    fornecedorService = { listar: jest.fn().mockReturnValue(of(respostaPaginada([fornecedor]))) };

    await TestBed.configureTestingModule({
      imports: [ProdutoListComponent],
      providers: [
        provideRouter([]),
        { provide: ProdutoService, useValue: produtoService },
        { provide: CategoriaService, useValue: categoriaService },
        { provide: FornecedorService, useValue: fornecedorService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProdutoListComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('carrega os produtos ao iniciar, sem filtros', () => {
    expect(produtoService.listar).toHaveBeenCalledWith(1, 10, { nome: '', categoria: null, fornecedor: null });
    expect(component.produtos).toEqual([produto]);
    expect(component.totalRegistros).toBe(1);
    expect(component.carregando).toBe(false);
  });

  it('carrega categorias e fornecedores para os selects de filtro', () => {
    expect(categoriaService.listar).toHaveBeenCalled();
    expect(fornecedorService.listar).toHaveBeenCalled();
    expect(component.categorias).toEqual([categoria]);
    expect(component.fornecedores).toEqual([fornecedor]);
  });

  it('exibe mensagem de erro quando a listagem falha', () => {
    produtoService.listar.mockReturnValue(throwError(() => new Error('falhou')));
    component.carregar();
    expect(component.erro).toContain('backend');
    expect(component.carregando).toBe(false);
  });

  it('volta uma página quando a página atual fica vazia após navegação', () => {
    component.pagina = 2;
    produtoService.listar.mockReturnValue(of(respostaPaginada<Produto>([], 0)));
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

  describe('filtros de busca', () => {
    function eventoDeValor(valor: string): Event {
      const input = document.createElement('input');
      input.value = valor;
      return { target: input } as unknown as Event;
    }

    function eventoDeSelect(valor: string): Event {
      const select = document.createElement('select');
      const option = document.createElement('option');
      option.value = valor;
      select.appendChild(option);
      select.value = valor;
      return { target: select } as unknown as Event;
    }

    beforeEach(() => {
      jest.useFakeTimers();
      produtoService.listar.mockClear();
    });

    afterEach(() => jest.useRealTimers());

    it('temFiltroAtivo é falso sem nenhum filtro aplicado', () => {
      expect(component.temFiltroAtivo).toBe(false);
    });

    it('alterarFiltroNome espera 300ms (debounce) antes de recarregar', () => {
      component.alterarFiltroNome(eventoDeValor('parafuso'));
      expect(produtoService.listar).not.toHaveBeenCalled();

      jest.advanceTimersByTime(300);

      expect(component.filtroNome).toBe('parafuso');
      expect(component.pagina).toBe(1);
      expect(produtoService.listar).toHaveBeenCalledWith(1, 10, { nome: 'parafuso', categoria: null, fornecedor: null });
    });

    it('digitar de novo antes dos 300ms reinicia o debounce', () => {
      component.alterarFiltroNome(eventoDeValor('par'));
      jest.advanceTimersByTime(200);
      component.alterarFiltroNome(eventoDeValor('parafuso'));
      jest.advanceTimersByTime(200);
      expect(produtoService.listar).not.toHaveBeenCalled();

      jest.advanceTimersByTime(100);
      expect(produtoService.listar).toHaveBeenCalledTimes(1);
      expect(component.filtroNome).toBe('parafuso');
    });

    it('alterarFiltroCategoria recarrega imediatamente e reseta a página', () => {
      component.pagina = 3;
      component.alterarFiltroCategoria(eventoDeSelect('2'));

      expect(component.filtroCategoria).toBe(2);
      expect(component.pagina).toBe(1);
      expect(produtoService.listar).toHaveBeenCalledWith(1, 10, { nome: '', categoria: 2, fornecedor: null });
    });

    it('alterarFiltroCategoria com valor vazio limpa o filtro', () => {
      component.filtroCategoria = 2;
      component.alterarFiltroCategoria(eventoDeSelect(''));
      expect(component.filtroCategoria).toBeNull();
    });

    it('alterarFiltroFornecedor recarrega imediatamente e reseta a página', () => {
      component.pagina = 3;
      component.alterarFiltroFornecedor(eventoDeSelect('3'));

      expect(component.filtroFornecedor).toBe(3);
      expect(component.pagina).toBe(1);
      expect(produtoService.listar).toHaveBeenCalledWith(1, 10, { nome: '', categoria: null, fornecedor: 3 });
    });

    it('temFiltroAtivo é verdadeiro quando algum filtro está aplicado', () => {
      component.filtroCategoria = 2;
      expect(component.temFiltroAtivo).toBe(true);
    });

    it('limparFiltros reseta tudo e recarrega', () => {
      component.filtroNome = 'parafuso';
      component.filtroCategoria = 2;
      component.filtroFornecedor = 3;
      component.pagina = 2;

      component.limparFiltros();

      expect(component.filtroNome).toBe('');
      expect(component.filtroCategoria).toBeNull();
      expect(component.filtroFornecedor).toBeNull();
      expect(component.pagina).toBe(1);
      expect(produtoService.listar).toHaveBeenCalledWith(1, 10, { nome: '', categoria: null, fornecedor: null });
    });

    it('ngOnDestroy cancela o debounce pendente', () => {
      component.alterarFiltroNome(eventoDeValor('parafuso'));
      component.ngOnDestroy();
      jest.advanceTimersByTime(300);
      expect(produtoService.listar).not.toHaveBeenCalled();
    });
  });

  describe('inativação', () => {
    it('pedirInativacao guarda o produto e cancelarInativacao limpa', () => {
      component.pedirInativacao(produto);
      expect(component.produtoParaInativar).toEqual(produto);
      component.cancelarInativacao();
      expect(component.produtoParaInativar).toBeNull();
    });

    it('confirmarInativacao inativa o produto e recarrega a lista', () => {
      component.pedirInativacao(produto);
      component.confirmarInativacao();

      expect(produtoService.inativar).toHaveBeenCalledWith(produto.id);
      expect(component.sucesso).toBe('Produto inativado com sucesso.');
      expect(component.produtoParaInativar).toBeNull();
    });

    it('confirmarInativacao trata erro do backend', () => {
      produtoService.inativar.mockReturnValue(throwError(() => new Error('falha ao inativar')));
      component.pedirInativacao(produto);
      component.confirmarInativacao();

      expect(component.erro).toBe('falha ao inativar');
      expect(component.produtoParaInativar).toBeNull();
    });
  });
});
