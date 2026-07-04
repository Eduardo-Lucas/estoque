import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Produto } from '../../models/produto.model';
import { ResultadoImportacao } from '../../models/csv.model';
import { ProdutoService } from '../../services/produto.service';

@Component({
  selector: 'app-produto-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './produto-list.component.html',
  styleUrl: './produto-list.component.css',
})
export class ProdutoListComponent implements OnInit {
  private produtoService = inject(ProdutoService);
  private router = inject(Router);

  produtos: Produto[] = [];
  carregando = false;
  erro = '';
  sucesso = '';

  produtoParaRemover: Produto | null = null;

  importando = false;
  exportando = false;
  resultadoImportacao: ResultadoImportacao | null = null;

  pagina = 1;
  tamanhoPagina = 10;
  totalRegistros = 0;

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.totalRegistros / this.tamanhoPagina));
  }

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando = true;
    this.produtoService.listar(this.pagina, this.tamanhoPagina).subscribe({
      next: (resposta) => {
        this.produtos = resposta.results;
        this.totalRegistros = resposta.count;
        this.carregando = false;

        // se a página atual ficou vazia (ex: removeu o último item da última página), volta uma página
        if (this.produtos.length === 0 && this.pagina > 1) {
          this.pagina--;
          this.carregar();
        }
      },
      error: () => {
        this.erro = 'Não foi possível carregar os produtos. Verifique se o backend está rodando em localhost:8000.';
        this.carregando = false;
      },
    });
  }

  alterarTamanhoPagina(event: Event): void {
    this.tamanhoPagina = Number((event.target as HTMLSelectElement).value);
    this.pagina = 1;
    this.carregar();
  }

  paginaAnterior(): void {
    if (this.pagina > 1) {
      this.pagina--;
      this.carregar();
    }
  }

  proximaPagina(): void {
    if (this.pagina < this.totalPaginas) {
      this.pagina++;
      this.carregar();
    }
  }

  criarProduto(): void {
    this.router.navigate(['/produtos/novo']);
  }

  editar(produto: Produto): void {
    this.router.navigate(['/produtos', produto.id, 'editar']);
  }

  importarCsv(event: Event): void {
    const input = event.target as HTMLInputElement;
    const arquivo = input.files?.[0];
    if (!arquivo) return;

    this.erro = '';
    this.sucesso = '';
    this.resultadoImportacao = null;
    this.importando = true;

    this.produtoService.importarCsv(arquivo).subscribe({
      next: (resultado) => {
        this.importando = false;
        this.resultadoImportacao = resultado;
        this.sucesso = `${resultado.criados} produto(s) criado(s), ${resultado.atualizados} atualizado(s).`;
        this.pagina = 1;
        this.carregar();
        input.value = '';
      },
      error: (err) => {
        this.importando = false;
        this.erro = err.message;
        input.value = '';
      },
    });
  }

  exportarCsv(): void {
    this.erro = '';
    this.exportando = true;

    this.produtoService.exportarCsv().subscribe({
      next: (blob) => {
        this.exportando = false;
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'produtos.csv';
        link.click();
        URL.revokeObjectURL(url);
      },
      error: (err) => {
        this.exportando = false;
        this.erro = err.message;
      },
    });
  }

  pedirRemocao(produto: Produto): void {
    this.produtoParaRemover = produto;
  }

  cancelarRemocao(): void {
    this.produtoParaRemover = null;
  }

  confirmarRemocao(): void {
    const produto = this.produtoParaRemover;
    if (!produto?.id) return;

    this.erro = '';
    this.sucesso = '';

    this.produtoService.remover(produto.id).subscribe({
      next: () => {
        this.sucesso = 'Produto removido com sucesso.';
        this.produtoParaRemover = null;
        this.carregar();
      },
      error: (err) => {
        this.erro = err.message;
        this.produtoParaRemover = null;
      },
    });
  }
}
