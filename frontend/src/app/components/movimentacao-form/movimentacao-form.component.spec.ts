import { TestBed, ComponentFixture, fakeAsync, tick } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { MovimentacaoFormComponent } from './movimentacao-form.component';
import { ProdutoService } from '../../services/produto.service';
import { MovimentacaoService } from '../../services/movimentacao.service';
import { AuthService } from '../../services/auth.service';
import { Produto } from '../../models/produto.model';
import { Movimentacao } from '../../models/movimentacao.model';

describe('MovimentacaoFormComponent', () => {
  let fixture: ComponentFixture<MovimentacaoFormComponent>;
  let component: MovimentacaoFormComponent;
  let produtoService: { listar: jest.Mock; obter: jest.Mock };
  let movimentacaoService: { listar: jest.Mock; criar: jest.Mock };

  const produtoDisponivel: Produto = {
    id: 1,
    nome: 'Parafuso 10mm',
    unidade_medida: 'UN',
    quantidade: 10,
    estoque_minimo: 0,
    preco_custo: 0,
    preco: 0,
    ativo: true,
  };

  const movimentacao: Movimentacao = {
    id: 1,
    produto: 1,
    tipo: 'REQUISICAO',
    quantidade: 1,
    solicitante: 'eduardo',
  };

  beforeEach(async () => {
    produtoService = {
      listar: jest.fn().mockReturnValue(of({ count: 1, next: null, previous: null, results: [produtoDisponivel] })),
      obter: jest.fn().mockReturnValue(of(produtoDisponivel)),
    };
    movimentacaoService = {
      listar: jest.fn().mockReturnValue(of({ count: 1, next: null, previous: null, results: [movimentacao] })),
      criar: jest.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [MovimentacaoFormComponent],
      providers: [
        { provide: ProdutoService, useValue: produtoService },
        { provide: MovimentacaoService, useValue: movimentacaoService },
        { provide: AuthService, useValue: { usuario: () => 'eduardo' } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MovimentacaoFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('pré-preenche o solicitante com o usuário logado', () => {
    expect(component.form.getRawValue().solicitante).toBe('eduardo');
  });

  it('carrega produtos e movimentações ao iniciar', () => {
    expect(component.produtos).toEqual([produtoDisponivel]);
    expect(component.movimentacoes).toEqual([movimentacao]);
    expect(component.carregando).toBe(false);
  });

  it('não registra quando o form é inválido', () => {
    component.form.setValue({ produto: 0, tipo: 'REQUISICAO', quantidade: 1, solicitante: 'eduardo', observacao: '' });
    component.registrar();
    expect(movimentacaoService.criar).not.toHaveBeenCalled();
  });

  it('bloqueia requisição maior que o estoque disponível (async validator)', fakeAsync(() => {
    component.form.setValue({
      produto: 1,
      tipo: 'REQUISICAO',
      quantidade: 99,
      solicitante: 'eduardo',
      observacao: '',
    });
    tick();

    expect(produtoService.obter).toHaveBeenCalledWith(1);
    expect(component.form.hasError('estoqueInsuficiente')).toBe(true);
    expect(component.form.getError('estoqueInsuficiente').disponivel).toBe(10);

    component.registrar();
    expect(movimentacaoService.criar).not.toHaveBeenCalled();
  }));

  it('permite requisição dentro do estoque disponível', fakeAsync(() => {
    component.form.setValue({
      produto: 1,
      tipo: 'REQUISICAO',
      quantidade: 5,
      solicitante: 'eduardo',
      observacao: '',
    });
    tick();

    expect(component.form.valid).toBe(true);
  }));

  it('registra com sucesso, mostra mensagem e reseta o formulário', fakeAsync(() => {
    movimentacaoService.criar.mockReturnValue(of(movimentacao));
    component.form.setValue({
      produto: 1,
      tipo: 'REQUISICAO',
      quantidade: 5,
      solicitante: 'eduardo',
      observacao: '',
    });
    tick();

    component.registrar();

    expect(movimentacaoService.criar).toHaveBeenCalled();
    expect(component.sucesso).toBe('Requisição registrada e estoque atualizado.');
    expect(component.form.getRawValue().produto).toBe(0);
  }));

  it('exibe mensagem de devolução ao registrar devolução com sucesso', fakeAsync(() => {
    movimentacaoService.criar.mockReturnValue(of(movimentacao));
    component.form.setValue({
      produto: 1,
      tipo: 'DEVOLUCAO',
      quantidade: 5,
      solicitante: 'eduardo',
      observacao: '',
    });
    tick();

    component.registrar();

    expect(component.sucesso).toBe('Devolução registrada e estoque atualizado.');
  }));

  it('trata erro do backend ao registrar', fakeAsync(() => {
    movimentacaoService.criar.mockReturnValue(throwError(() => new Error('Estoque insuficiente para "X".')));
    component.form.setValue({
      produto: 1,
      tipo: 'REQUISICAO',
      quantidade: 5,
      solicitante: 'eduardo',
      observacao: '',
    });
    tick();

    component.registrar();

    expect(component.erro).toBe('Estoque insuficiente para "X".');
  }));
});
