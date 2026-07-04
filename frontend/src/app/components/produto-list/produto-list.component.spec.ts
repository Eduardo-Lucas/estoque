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
    importarCsv: jest.Mock;
    exportarCsv: jest.Mock;
    importarNfe: jest.Mock;
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
      importarCsv: jest.fn(),
      exportarCsv: jest.fn(),
      importarNfe: jest.fn(),
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

  describe('importação CSV', () => {
    function eventoComArquivo(arquivo: File | undefined): Event {
      const input = document.createElement('input');
      Object.defineProperty(input, 'files', { value: arquivo ? [arquivo] : [] });
      return { target: input } as unknown as Event;
    }

    it('importa o csv selecionado e recarrega a lista', () => {
      const resultado = { criados: 2, atualizados: 1, erros: [] };
      produtoService.importarCsv.mockReturnValue(of(resultado));
      const arquivo = new File(['nome,quantidade\nX,1'], 'produtos.csv');

      component.importarCsv(eventoComArquivo(arquivo));

      expect(produtoService.importarCsv).toHaveBeenCalledWith(arquivo);
      expect(component.resultadoImportacao).toEqual(resultado);
      expect(component.sucesso).toBe('2 produto(s) criado(s), 1 atualizado(s).');
      expect(component.importando).toBe(false);
    });

    it('não faz nada quando nenhum arquivo é selecionado', () => {
      component.importarCsv(eventoComArquivo(undefined));
      expect(produtoService.importarCsv).not.toHaveBeenCalled();
    });

    it('trata erro de importação', () => {
      produtoService.importarCsv.mockReturnValue(throwError(() => new Error('csv inválido')));
      const arquivo = new File(['x'], 'produtos.csv');

      component.importarCsv(eventoComArquivo(arquivo));

      expect(component.erro).toBe('csv inválido');
      expect(component.importando).toBe(false);
    });
  });

  describe('importação de NF-e', () => {
    function eventoComArquivo(arquivo: File | undefined): Event {
      const input = document.createElement('input');
      Object.defineProperty(input, 'files', { value: arquivo ? [arquivo] : [] });
      return { target: input } as unknown as Event;
    }

    it('importa o XML selecionado, mostra o resumo e recarrega a lista', () => {
      const resultado = {
        numero_nfe: '123',
        fornecedor: 'Distribuidora ABC',
        itens_processados: 2,
        itens_ja_processados: 1,
        nao_encontrados: [],
        erros: [],
      };
      produtoService.importarNfe.mockReturnValue(of(resultado));
      const arquivo = new File(['<NFe></NFe>'], 'nfe.xml');

      component.importarNfe(eventoComArquivo(arquivo));

      expect(produtoService.importarNfe).toHaveBeenCalledWith(arquivo);
      expect(component.resultadoImportacaoNfe).toEqual(resultado);
      expect(component.sucesso).toContain('123');
      expect(component.sucesso).toContain('Distribuidora ABC');
      expect(component.sucesso).toContain('2 item(ns) processado(s)');
      expect(component.importandoNfe).toBe(false);
    });

    it('não faz nada quando nenhum arquivo é selecionado', () => {
      component.importarNfe(eventoComArquivo(undefined));
      expect(produtoService.importarNfe).not.toHaveBeenCalled();
    });

    it('trata erro de importação', () => {
      produtoService.importarNfe.mockReturnValue(throwError(() => new Error('XML inválido')));
      const arquivo = new File(['x'], 'nfe.xml');

      component.importarNfe(eventoComArquivo(arquivo));

      expect(component.erro).toBe('XML inválido');
      expect(component.importandoNfe).toBe(false);
    });
  });

  describe('exportação CSV', () => {
    let createObjectURL: jest.Mock;
    let revokeObjectURL: jest.Mock;
    let clickSpy: jest.SpyInstance;

    beforeEach(() => {
      createObjectURL = jest.fn().mockReturnValue('blob:mock-url');
      revokeObjectURL = jest.fn();
      (URL as any).createObjectURL = createObjectURL;
      (URL as any).revokeObjectURL = revokeObjectURL;
      clickSpy = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    });

    afterEach(() => clickSpy.mockRestore());

    it('exporta o csv disparando o download', () => {
      const blob = new Blob(['nome,quantidade\n']);
      produtoService.exportarCsv.mockReturnValue(of(blob));

      component.exportarCsv();

      expect(createObjectURL).toHaveBeenCalledWith(blob);
      expect(clickSpy).toHaveBeenCalled();
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
      expect(component.exportando).toBe(false);
    });

    it('trata erro de exportação', () => {
      produtoService.exportarCsv.mockReturnValue(throwError(() => new Error('erro ao exportar')));

      component.exportarCsv();

      expect(component.erro).toBe('erro ao exportar');
      expect(component.exportando).toBe(false);
    });
  });
});
