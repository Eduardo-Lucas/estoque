import { TestBed, ComponentFixture } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ProdutoFormComponent } from './produto-form.component';
import { ProdutoService } from '../../services/produto.service';
import { CategoriaService } from '../../services/categoria.service';
import { FornecedorService } from '../../services/fornecedor.service';
import { Produto } from '../../models/produto.model';
import { Categoria } from '../../models/categoria.model';
import { Fornecedor } from '../../models/fornecedor.model';

describe('ProdutoFormComponent', () => {
  let fixture: ComponentFixture<ProdutoFormComponent>;
  let component: ProdutoFormComponent;
  let produtoService: { obter: jest.Mock; criar: jest.Mock; atualizar: jest.Mock };
  let categoriaService: { listar: jest.Mock };
  let fornecedorService: { listar: jest.Mock };
  let navigate: jest.SpyInstance;

  const categorias: Categoria[] = [{ id: 1, nome: 'Ferragens' }];
  const fornecedores: Fornecedor[] = [{ id: 1, nome: 'Distribuidora ABC' }];

  const produtoExistente: Produto = {
    id: 7,
    nome: 'Parafuso 10mm',
    sku: 'PRF-001',
    codigo_barras: '',
    descricao: 'Desc',
    categoria: 1,
    fornecedor: 1,
    unidade_medida: 'CX',
    quantidade: 50,
    estoque_minimo: 10,
    preco_custo: '5.00',
    preco: '9.90',
    ativo: true,
  };

  function configurar(idParam: string | null) {
    produtoService = { obter: jest.fn().mockReturnValue(of(produtoExistente)), criar: jest.fn(), atualizar: jest.fn() };
    categoriaService = { listar: jest.fn().mockReturnValue(of({ count: 1, next: null, previous: null, results: categorias })) };
    fornecedorService = { listar: jest.fn().mockReturnValue(of({ count: 1, next: null, previous: null, results: fornecedores })) };

    TestBed.configureTestingModule({
      imports: [ProdutoFormComponent],
      providers: [
        provideRouter([]),
        { provide: ProdutoService, useValue: produtoService },
        { provide: CategoriaService, useValue: categoriaService },
        { provide: FornecedorService, useValue: fornecedorService },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap(idParam ? { id: idParam } : {}) } },
        },
      ],
    });

    fixture = TestBed.createComponent(ProdutoFormComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  }

  describe('modo criação', () => {
    beforeEach(() => configurar(null));

    it('carrega categorias e fornecedores para os selects', () => {
      expect(component.categorias).toEqual(categorias);
      expect(component.fornecedores).toEqual(fornecedores);
    });

    it('não está em edição e não busca produto', () => {
      expect(component.emEdicao).toBe(false);
      expect(produtoService.obter).not.toHaveBeenCalled();
    });

    it('não salva e marca campos tocados quando o form é inválido', () => {
      component.salvar();
      expect(produtoService.criar).not.toHaveBeenCalled();
      expect(component.form.get('nome')?.touched).toBe(true);
    });

    it('cria o produto e navega para /produtos', () => {
      produtoService.criar.mockReturnValue(of(produtoExistente));
      component.form.patchValue({ nome: 'Produto Novo', quantidade: 5, preco: 10 });

      component.salvar();

      expect(produtoService.criar).toHaveBeenCalled();
      const enviado = produtoService.criar.mock.calls[0][0];
      expect(enviado.nome).toBe('Produto Novo');
      expect(enviado.sku).toBeNull();
      expect(navigate).toHaveBeenCalledWith(['/produtos']);
    });

    it('envia sku preenchido quando informado', () => {
      produtoService.criar.mockReturnValue(of(produtoExistente));
      component.form.patchValue({ nome: 'Produto Novo', quantidade: 5, preco: 10, sku: 'ABC-1' });

      component.salvar();

      expect(produtoService.criar.mock.calls[0][0].sku).toBe('ABC-1');
    });

    it('trata erro ao salvar', () => {
      produtoService.criar.mockReturnValue(throwError(() => new Error('nome duplicado')));
      component.form.patchValue({ nome: 'Produto Novo', quantidade: 5, preco: 10 });

      component.salvar();

      expect(component.erro).toBe('nome duplicado');
      expect(navigate).not.toHaveBeenCalled();
    });

    it('cancelar navega de volta para /produtos', () => {
      component.cancelar();
      expect(navigate).toHaveBeenCalledWith(['/produtos']);
    });
  });

  describe('modo edição', () => {
    beforeEach(() => configurar('7'));

    it('identifica o id da rota e busca o produto', () => {
      expect(component.emEdicao).toBe(true);
      expect(produtoService.obter).toHaveBeenCalledWith(7);
    });

    it('preenche o formulário com os dados do produto', () => {
      expect(component.form.getRawValue()).toMatchObject({
        nome: 'Parafuso 10mm',
        sku: 'PRF-001',
        categoria: 1,
        fornecedor: 1,
        unidade_medida: 'CX',
        quantidade: 50,
        estoque_minimo: 10,
        preco_custo: 5,
        preco: 9.9,
      });
      expect(component.carregando).toBe(false);
    });

    it('atualiza o produto existente ao salvar', () => {
      produtoService.atualizar.mockReturnValue(of(produtoExistente));

      component.salvar();

      expect(produtoService.atualizar).toHaveBeenCalledWith(7, expect.objectContaining({ nome: 'Parafuso 10mm' }));
      expect(navigate).toHaveBeenCalledWith(['/produtos']);
    });

    it('trata erro ao carregar produto', () => {
      produtoService.obter.mockReturnValue(throwError(() => new Error('não encontrado')));
      const outraFixture = TestBed.createComponent(ProdutoFormComponent);
      outraFixture.detectChanges();
      expect(outraFixture.componentInstance.erro).toBe('Não foi possível carregar o produto.');
      expect(outraFixture.componentInstance.carregando).toBe(false);
    });
  });
});
