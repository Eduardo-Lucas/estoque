import { TestBed, ComponentFixture } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { FornecedorListComponent } from './fornecedor-list.component';
import { FornecedorService } from '../../services/fornecedor.service';
import { Fornecedor } from '../../models/fornecedor.model';

describe('FornecedorListComponent', () => {
  let fixture: ComponentFixture<FornecedorListComponent>;
  let component: FornecedorListComponent;
  let fornecedorService: { listar: jest.Mock; inativar: jest.Mock };
  let navigate: jest.SpyInstance;

  const fornecedor: Fornecedor = { id: 1, nome: 'Distribuidora ABC', email: 'contato@abc.com' };

  function respostaPaginada(results: Fornecedor[], count = results.length) {
    return { count, next: null, previous: null, results };
  }

  beforeEach(async () => {
    fornecedorService = {
      listar: jest.fn().mockReturnValue(of(respostaPaginada([fornecedor]))),
      inativar: jest.fn().mockReturnValue(of(undefined)),
    };

    await TestBed.configureTestingModule({
      imports: [FornecedorListComponent],
      providers: [provideRouter([]), { provide: FornecedorService, useValue: fornecedorService }],
    }).compileComponents();

    fixture = TestBed.createComponent(FornecedorListComponent);
    component = fixture.componentInstance;
    navigate = jest.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  it('carrega os fornecedores ao iniciar, sem filtro', () => {
    expect(fornecedorService.listar).toHaveBeenCalledWith({ nome: '' });
    expect(component.fornecedores).toEqual([fornecedor]);
    expect(component.carregando).toBe(false);
  });

  it('exibe mensagem de erro quando a listagem falha', () => {
    fornecedorService.listar.mockReturnValue(throwError(() => new Error('falhou')));
    component.carregar();
    expect(component.erro).toContain('fornecedores');
    expect(component.carregando).toBe(false);
  });

  it('criarFornecedor navega para /fornecedores/novo', () => {
    component.criarFornecedor();
    expect(navigate).toHaveBeenCalledWith(['/fornecedores/novo']);
  });

  it('editar navega para /fornecedores/:id/editar', () => {
    component.editar(fornecedor);
    expect(navigate).toHaveBeenCalledWith(['/fornecedores', fornecedor.id, 'editar']);
  });

  describe('filtro por nome', () => {
    function eventoDeValor(valor: string): Event {
      const input = document.createElement('input');
      input.value = valor;
      return { target: input } as unknown as Event;
    }

    beforeEach(() => {
      jest.useFakeTimers();
      fornecedorService.listar.mockClear();
    });

    afterEach(() => jest.useRealTimers());

    it('temFiltroAtivo é falso sem filtro', () => {
      expect(component.temFiltroAtivo).toBe(false);
    });

    it('alterarFiltroNome espera 300ms (debounce) antes de recarregar', () => {
      component.alterarFiltroNome(eventoDeValor('abc'));
      expect(fornecedorService.listar).not.toHaveBeenCalled();

      jest.advanceTimersByTime(300);

      expect(component.filtroNome).toBe('abc');
      expect(fornecedorService.listar).toHaveBeenCalledWith({ nome: 'abc' });
      expect(component.temFiltroAtivo).toBe(true);
    });

    it('limparFiltro reseta o filtro e recarrega', () => {
      component.filtroNome = 'abc';
      component.limparFiltro();
      expect(component.filtroNome).toBe('');
      expect(fornecedorService.listar).toHaveBeenCalledWith({ nome: '' });
    });

    it('ngOnDestroy cancela o debounce pendente', () => {
      component.alterarFiltroNome(eventoDeValor('abc'));
      component.ngOnDestroy();
      jest.advanceTimersByTime(300);
      expect(fornecedorService.listar).not.toHaveBeenCalled();
    });
  });

  describe('inativação', () => {
    it('pedirInativacao guarda o fornecedor e cancelarInativacao limpa', () => {
      component.pedirInativacao(fornecedor);
      expect(component.fornecedorParaInativar).toEqual(fornecedor);
      component.cancelarInativacao();
      expect(component.fornecedorParaInativar).toBeNull();
    });

    it('confirmarInativacao inativa o fornecedor e recarrega a lista', () => {
      component.pedirInativacao(fornecedor);
      component.confirmarInativacao();

      expect(fornecedorService.inativar).toHaveBeenCalledWith(fornecedor.id);
      expect(component.sucesso).toBe('Fornecedor inativado com sucesso.');
      expect(component.fornecedorParaInativar).toBeNull();
    });

    it('confirmarInativacao trata erro do backend', () => {
      fornecedorService.inativar.mockReturnValue(throwError(() => new Error('falha ao inativar')));
      component.pedirInativacao(fornecedor);
      component.confirmarInativacao();

      expect(component.erro).toBe('falha ao inativar');
      expect(component.fornecedorParaInativar).toBeNull();
    });
  });
});
