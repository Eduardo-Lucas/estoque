import { TestBed, ComponentFixture } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ImportacoesComponent } from './importacoes.component';
import { ProdutoService } from '../../services/produto.service';
import { CategoriaService } from '../../services/categoria.service';
import { FornecedorService } from '../../services/fornecedor.service';

describe('ImportacoesComponent', () => {
  let fixture: ComponentFixture<ImportacoesComponent>;
  let component: ImportacoesComponent;
  let produtoService: { importarCsv: jest.Mock; exportarCsv: jest.Mock; importarNfe: jest.Mock };
  let categoriaService: { importarCsv: jest.Mock; exportarCsv: jest.Mock };
  let fornecedorService: { importarCsv: jest.Mock; exportarCsv: jest.Mock };

  function eventoComArquivo(arquivo: File | undefined): Event {
    const input = document.createElement('input');
    Object.defineProperty(input, 'files', { value: arquivo ? [arquivo] : [] });
    return { target: input } as unknown as Event;
  }

  beforeEach(async () => {
    produtoService = { importarCsv: jest.fn(), exportarCsv: jest.fn(), importarNfe: jest.fn() };
    categoriaService = { importarCsv: jest.fn(), exportarCsv: jest.fn() };
    fornecedorService = { importarCsv: jest.fn(), exportarCsv: jest.fn() };

    await TestBed.configureTestingModule({
      imports: [ImportacoesComponent],
      providers: [
        { provide: ProdutoService, useValue: produtoService },
        { provide: CategoriaService, useValue: categoriaService },
        { provide: FornecedorService, useValue: fornecedorService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ImportacoesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  describe('produtos (CSV)', () => {
    it('importa o csv selecionado', () => {
      const resultado = { criados: 2, atualizados: 1, erros: [] };
      produtoService.importarCsv.mockReturnValue(of(resultado));
      const arquivo = new File(['nome,quantidade\nX,1'], 'produtos.csv');

      component.importarProdutoCsv(eventoComArquivo(arquivo));

      expect(produtoService.importarCsv).toHaveBeenCalledWith(arquivo);
      expect(component.produtoCsv.resultado).toEqual(resultado);
      expect(component.produtoCsv.sucesso).toBe('2 produto(s) criado(s), 1 atualizado(s).');
      expect(component.produtoCsv.importando).toBe(false);
    });

    it('não faz nada quando nenhum arquivo é selecionado', () => {
      component.importarProdutoCsv(eventoComArquivo(undefined));
      expect(produtoService.importarCsv).not.toHaveBeenCalled();
    });

    it('trata erro de importação', () => {
      produtoService.importarCsv.mockReturnValue(throwError(() => new Error('csv inválido')));
      component.importarProdutoCsv(eventoComArquivo(new File(['x'], 'produtos.csv')));
      expect(component.produtoCsv.erro).toBe('csv inválido');
      expect(component.produtoCsv.importando).toBe(false);
    });

    it('exporta o csv', () => {
      const blob = new Blob(['nome,quantidade\n']);
      produtoService.exportarCsv.mockReturnValue(of(blob));
      const createObjectURL = jest.fn().mockReturnValue('blob:mock-url');
      const revokeObjectURL = jest.fn();
      (URL as any).createObjectURL = createObjectURL;
      (URL as any).revokeObjectURL = revokeObjectURL;
      const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

      component.exportarProdutoCsv();

      expect(createObjectURL).toHaveBeenCalledWith(blob);
      expect(clickSpy).toHaveBeenCalled();
      expect(component.produtoCsv.exportando).toBe(false);
      clickSpy.mockRestore();
    });

    it('trata erro de exportação', () => {
      produtoService.exportarCsv.mockReturnValue(throwError(() => new Error('erro ao exportar')));
      component.exportarProdutoCsv();
      expect(component.produtoCsv.erro).toBe('erro ao exportar');
      expect(component.produtoCsv.exportando).toBe(false);
    });
  });

  describe('produtos (NF-e)', () => {
    it('importa o XML selecionado e mostra o resumo', () => {
      const resultado = {
        numero_nfe: '123',
        fornecedor: 'Distribuidora ABC',
        itens_processados: 2,
        itens_ja_processados: 1,
        nao_encontrados: [],
        erros: [],
      };
      produtoService.importarNfe.mockReturnValue(of(resultado));

      component.importarProdutoNfe(eventoComArquivo(new File(['<NFe></NFe>'], 'nfe.xml')));

      expect(component.produtoNfe.resultado).toEqual(resultado);
      expect(component.produtoNfe.sucesso).toContain('123');
      expect(component.produtoNfe.sucesso).toContain('Distribuidora ABC');
      expect(component.produtoNfe.importando).toBe(false);
    });

    it('não faz nada quando nenhum arquivo é selecionado', () => {
      component.importarProdutoNfe(eventoComArquivo(undefined));
      expect(produtoService.importarNfe).not.toHaveBeenCalled();
    });

    it('trata erro de importação', () => {
      produtoService.importarNfe.mockReturnValue(throwError(() => new Error('XML inválido')));
      component.importarProdutoNfe(eventoComArquivo(new File(['x'], 'nfe.xml')));
      expect(component.produtoNfe.erro).toBe('XML inválido');
      expect(component.produtoNfe.importando).toBe(false);
    });
  });

  describe('categorias (CSV)', () => {
    it('importa o csv selecionado', () => {
      const resultado = { criados: 1, atualizados: 0, erros: [] };
      categoriaService.importarCsv.mockReturnValue(of(resultado));

      component.importarCategoriaCsv(eventoComArquivo(new File(['nome\nX'], 'categorias.csv')));

      expect(component.categoriaCsv.resultado).toEqual(resultado);
      expect(component.categoriaCsv.sucesso).toBe('1 categoria(s) criada(s), 0 atualizada(s).');
    });

    it('trata erro de importação', () => {
      categoriaService.importarCsv.mockReturnValue(throwError(() => new Error('falhou')));
      component.importarCategoriaCsv(eventoComArquivo(new File(['x'], 'categorias.csv')));
      expect(component.categoriaCsv.erro).toBe('falhou');
    });

    it('exporta o csv', () => {
      const blob = new Blob(['nome\n']);
      categoriaService.exportarCsv.mockReturnValue(of(blob));
      (URL as any).createObjectURL = jest.fn().mockReturnValue('blob:mock-url');
      (URL as any).revokeObjectURL = jest.fn();
      const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

      component.exportarCategoriaCsv();

      expect(component.categoriaCsv.exportando).toBe(false);
      clickSpy.mockRestore();
    });
  });

  describe('fornecedores (CSV)', () => {
    it('importa o csv selecionado', () => {
      const resultado = { criados: 1, atualizados: 0, erros: [] };
      fornecedorService.importarCsv.mockReturnValue(of(resultado));

      component.importarFornecedorCsv(eventoComArquivo(new File(['nome\nX'], 'fornecedores.csv')));

      expect(component.fornecedorCsv.resultado).toEqual(resultado);
      expect(component.fornecedorCsv.sucesso).toBe('1 fornecedor(es) criado(s), 0 atualizado(s).');
    });

    it('trata erro de importação', () => {
      fornecedorService.importarCsv.mockReturnValue(throwError(() => new Error('falhou')));
      component.importarFornecedorCsv(eventoComArquivo(new File(['x'], 'fornecedores.csv')));
      expect(component.fornecedorCsv.erro).toBe('falhou');
    });

    it('exporta o csv', () => {
      const blob = new Blob(['nome\n']);
      fornecedorService.exportarCsv.mockReturnValue(of(blob));
      (URL as any).createObjectURL = jest.fn().mockReturnValue('blob:mock-url');
      (URL as any).revokeObjectURL = jest.fn();
      const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

      component.exportarFornecedorCsv();

      expect(component.fornecedorCsv.exportando).toBe(false);
      clickSpy.mockRestore();
    });

    it('trata erro de exportação', () => {
      fornecedorService.exportarCsv.mockReturnValue(throwError(() => new Error('erro ao exportar')));
      component.exportarFornecedorCsv();
      expect(component.fornecedorCsv.erro).toBe('erro ao exportar');
      expect(component.fornecedorCsv.exportando).toBe(false);
    });
  });
});
