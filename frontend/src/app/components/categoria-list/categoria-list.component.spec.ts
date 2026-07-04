import { TestBed, ComponentFixture } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { CategoriaListComponent } from './categoria-list.component';
import { CategoriaService } from '../../services/categoria.service';
import { Categoria } from '../../models/categoria.model';

describe('CategoriaListComponent', () => {
  let fixture: ComponentFixture<CategoriaListComponent>;
  let component: CategoriaListComponent;
  let categoriaService: { listar: jest.Mock; remover: jest.Mock };
  let navigate: jest.SpyInstance;

  const categoria: Categoria = { id: 1, nome: 'Ferragens', descricao: 'Parafusos e afins' };

  function respostaPaginada(results: Categoria[], count = results.length) {
    return { count, next: null, previous: null, results };
  }

  beforeEach(async () => {
    categoriaService = {
      listar: jest.fn().mockReturnValue(of(respostaPaginada([categoria]))),
      remover: jest.fn().mockReturnValue(of(undefined)),
    };

    await TestBed.configureTestingModule({
      imports: [CategoriaListComponent],
      providers: [provideRouter([]), { provide: CategoriaService, useValue: categoriaService }],
    }).compileComponents();

    fixture = TestBed.createComponent(CategoriaListComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('carrega as categorias ao iniciar, sem filtro', () => {
    expect(categoriaService.listar).toHaveBeenCalledWith({ nome: '' });
    expect(component.categorias).toEqual([categoria]);
    expect(component.carregando).toBe(false);
  });

  it('exibe mensagem de erro quando a listagem falha', () => {
    categoriaService.listar.mockReturnValue(throwError(() => new Error('falhou')));
    component.carregar();
    expect(component.erro).toContain('categorias');
    expect(component.carregando).toBe(false);
  });

  it('criarCategoria navega para /categorias/novo', () => {
    component.criarCategoria();
    expect(navigate).toHaveBeenCalledWith(['/categorias/novo']);
  });

  it('editar navega para /categorias/:id/editar', () => {
    component.editar(categoria);
    expect(navigate).toHaveBeenCalledWith(['/categorias', categoria.id, 'editar']);
  });

  describe('filtro por nome', () => {
    function eventoDeValor(valor: string): Event {
      const input = document.createElement('input');
      input.value = valor;
      return { target: input } as unknown as Event;
    }

    beforeEach(() => {
      jest.useFakeTimers();
      categoriaService.listar.mockClear();
    });

    afterEach(() => jest.useRealTimers());

    it('temFiltroAtivo é falso sem filtro', () => {
      expect(component.temFiltroAtivo).toBe(false);
    });

    it('alterarFiltroNome espera 300ms (debounce) antes de recarregar', () => {
      component.alterarFiltroNome(eventoDeValor('ferrag'));
      expect(categoriaService.listar).not.toHaveBeenCalled();

      jest.advanceTimersByTime(300);

      expect(component.filtroNome).toBe('ferrag');
      expect(categoriaService.listar).toHaveBeenCalledWith({ nome: 'ferrag' });
      expect(component.temFiltroAtivo).toBe(true);
    });

    it('limparFiltro reseta o filtro e recarrega', () => {
      component.filtroNome = 'ferrag';
      component.limparFiltro();
      expect(component.filtroNome).toBe('');
      expect(categoriaService.listar).toHaveBeenCalledWith({ nome: '' });
    });

    it('ngOnDestroy cancela o debounce pendente', () => {
      component.alterarFiltroNome(eventoDeValor('ferrag'));
      component.ngOnDestroy();
      jest.advanceTimersByTime(300);
      expect(categoriaService.listar).not.toHaveBeenCalled();
    });
  });

  describe('remoção', () => {
    it('pedirRemocao guarda a categoria e cancelarRemocao limpa', () => {
      component.pedirRemocao(categoria);
      expect(component.categoriaParaRemover).toEqual(categoria);
      component.cancelarRemocao();
      expect(component.categoriaParaRemover).toBeNull();
    });

    it('confirmarRemocao remove a categoria e recarrega a lista', () => {
      component.pedirRemocao(categoria);
      component.confirmarRemocao();

      expect(categoriaService.remover).toHaveBeenCalledWith(categoria.id);
      expect(component.sucesso).toBe('Categoria removida com sucesso.');
      expect(component.categoriaParaRemover).toBeNull();
    });

    it('confirmarRemocao trata erro do backend', () => {
      categoriaService.remover.mockReturnValue(throwError(() => new Error('falha ao remover')));
      component.pedirRemocao(categoria);
      component.confirmarRemocao();

      expect(component.erro).toBe('falha ao remover');
      expect(component.categoriaParaRemover).toBeNull();
    });
  });
});
