import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AbstractControl,
  AsyncValidatorFn,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Observable, catchError, map, of } from 'rxjs';
import { Produto } from '../../models/produto.model';
import { Movimentacao, TIPO_MOVIMENTACAO_LABELS, TipoMovimentacao } from '../../models/movimentacao.model';
import { ProdutoService } from '../../services/produto.service';
import { MovimentacaoService } from '../../services/movimentacao.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-movimentacao-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './movimentacao-form.component.html',
  styleUrl: './movimentacao-form.component.css',
})
export class MovimentacaoFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private produtoService = inject(ProdutoService);
  private movimentacaoService = inject(MovimentacaoService);
  private authService = inject(AuthService);

  produtos: Produto[] = [];
  movimentacoes: Movimentacao[] = [];
  readonly tipoLabels = TIPO_MOVIMENTACAO_LABELS;

  erro = '';
  sucesso = '';
  carregando = false;

  form = this.fb.nonNullable.group(
    {
      produto: [0, [Validators.required, Validators.min(1)]],
      tipo: ['REQUISICAO' as TipoMovimentacao, Validators.required],
      quantidade: [1, [Validators.required, Validators.min(1)]],
      solicitante: [this.authService.usuario() ?? '', Validators.required],
      observacao: [''],
    },
    { updateOn: 'blur', asyncValidators: [this.estoqueSuficienteValidator()] },
  );

  ngOnInit(): void {
    this.carregarProdutos();
    this.carregarMovimentacoes();
  }

  carregarProdutos(): void {
    this.produtoService.listar().subscribe({
      next: (resposta) => (this.produtos = resposta.results),
    });
  }

  carregarMovimentacoes(): void {
    this.carregando = true;
    this.movimentacaoService.listar().subscribe({
      next: (resposta) => {
        this.movimentacoes = resposta.results;
        this.carregando = false;
      },
      error: () => (this.carregando = false),
    });
  }

  registrar(): void {
    this.erro = '';
    this.sucesso = '';

    if (this.form.invalid || this.form.pending) {
      this.form.markAllAsTouched();
      return;
    }

    this.movimentacaoService.criar(this.form.getRawValue() as Movimentacao).subscribe({
      next: () => {
        const tipo = this.form.getRawValue().tipo;
        this.sucesso =
          tipo === 'REQUISICAO'
            ? 'Requisição registrada e estoque atualizado.'
            : 'Devolução registrada e estoque atualizado.';
        this.form.reset({
          produto: 0,
          tipo: 'REQUISICAO',
          quantidade: 1,
          solicitante: this.authService.usuario() ?? '',
          observacao: '',
        });
        this.carregarMovimentacoes();
        this.carregarProdutos();
      },
      error: (err) => {
        this.erro = err.message;
      },
    });
  }

  private estoqueSuficienteValidator(): AsyncValidatorFn {
    return (group: AbstractControl): Observable<ValidationErrors | null> => {
      const tipo = group.get('tipo')?.value;
      const produtoId = group.get('produto')?.value;
      const quantidade = group.get('quantidade')?.value;

      if (tipo !== 'REQUISICAO' || !produtoId || !quantidade || quantidade <= 0) {
        return of(null);
      }

      return this.produtoService.obter(produtoId).pipe(
        map((produto) =>
          quantidade > produto.quantidade ? { estoqueInsuficiente: { disponivel: produto.quantidade } } : null,
        ),
        catchError(() => of(null)),
      );
    };
  }
}
