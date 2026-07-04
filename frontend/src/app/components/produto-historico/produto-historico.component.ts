import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Produto } from '../../models/produto.model';
import { Movimentacao, TIPO_MOVIMENTACAO_LABELS } from '../../models/movimentacao.model';
import { ProdutoService } from '../../services/produto.service';
import { MovimentacaoService } from '../../services/movimentacao.service';

@Component({
  selector: 'app-produto-historico',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './produto-historico.component.html',
  styleUrl: './produto-historico.component.css',
})
export class ProdutoHistoricoComponent implements OnInit {
  private produtoService = inject(ProdutoService);
  private movimentacaoService = inject(MovimentacaoService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  produtoId!: number;
  produto: Produto | null = null;
  movimentacoes: Movimentacao[] = [];
  readonly tipoLabels = TIPO_MOVIMENTACAO_LABELS;

  carregandoProduto = false;
  carregandoMovimentacoes = false;
  erro = '';

  ngOnInit(): void {
    this.produtoId = Number(this.route.snapshot.paramMap.get('id'));
    this.carregarProduto();
    this.carregarMovimentacoes();
  }

  carregarProduto(): void {
    this.carregandoProduto = true;
    this.produtoService.obter(this.produtoId).subscribe({
      next: (produto) => {
        this.produto = produto;
        this.carregandoProduto = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar o produto.';
        this.carregandoProduto = false;
      },
    });
  }

  carregarMovimentacoes(): void {
    this.carregandoMovimentacoes = true;
    this.movimentacaoService.listar(this.produtoId).subscribe({
      next: (resposta) => {
        this.movimentacoes = resposta.results;
        this.carregandoMovimentacoes = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar o histórico de movimentações.';
        this.carregandoMovimentacoes = false;
      },
    });
  }

  voltar(): void {
    this.router.navigate(['/produtos']);
  }
}
