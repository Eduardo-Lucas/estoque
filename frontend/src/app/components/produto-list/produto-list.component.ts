import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Produto } from '../../models/produto.model';
import { Categoria } from '../../models/categoria.model';
import { Fornecedor } from '../../models/fornecedor.model';
import { ProdutoService } from '../../services/produto.service';
import { CategoriaService } from '../../services/categoria.service';
import { FornecedorService } from '../../services/fornecedor.service';

@Component({
  selector: 'app-produto-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './produto-list.component.html',
  styleUrl: './produto-list.component.css',
})
export class ProdutoListComponent implements OnInit, OnDestroy {
  private produtoService = inject(ProdutoService);
  private categoriaService = inject(CategoriaService);
  private fornecedorService = inject(FornecedorService);
  private router = inject(Router);

  produtos: Produto[] = [];
  categorias: Categoria[] = [];
  fornecedores: Fornecedor[] = [];
  carregando = false;
  erro = '';
  sucesso = '';

  produtoParaInativar: Produto | null = null;

  pagina = 1;
  tamanhoPagina = 10;
  totalRegistros = 0;

  filtroNome = '';
  filtroCategoria: number | null = null;
  filtroFornecedor: number | null = null;
  private debounceFiltroNome?: ReturnType<typeof setTimeout>;

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.totalRegistros / this.tamanhoPagina));
  }

  get temFiltroAtivo(): boolean {
    return !!this.filtroNome || this.filtroCategoria !== null || this.filtroFornecedor !== null;
  }

  ngOnInit(): void {
    this.carregar();
    this.carregarCategorias();
    this.carregarFornecedores();
  }

  ngOnDestroy(): void {
    clearTimeout(this.debounceFiltroNome);
  }

  carregar(): void {
    this.carregando = true;
    this.produtoService.listar(this.pagina, this.tamanhoPagina, {
      nome: this.filtroNome,
      categoria: this.filtroCategoria,
      fornecedor: this.filtroFornecedor,
    }).subscribe({
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

  carregarCategorias(): void {
    this.categoriaService.listar().subscribe({
      next: (resposta) => (this.categorias = resposta.results),
    });
  }

  carregarFornecedores(): void {
    this.fornecedorService.listar().subscribe({
      next: (resposta) => (this.fornecedores = resposta.results),
    });
  }

  alterarFiltroNome(event: Event): void {
    this.filtroNome = (event.target as HTMLInputElement).value;
    clearTimeout(this.debounceFiltroNome);
    this.debounceFiltroNome = setTimeout(() => {
      this.pagina = 1;
      this.carregar();
    }, 300);
  }

  alterarFiltroCategoria(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value;
    this.filtroCategoria = valor ? Number(valor) : null;
    this.pagina = 1;
    this.carregar();
  }

  alterarFiltroFornecedor(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value;
    this.filtroFornecedor = valor ? Number(valor) : null;
    this.pagina = 1;
    this.carregar();
  }

  limparFiltros(): void {
    this.filtroNome = '';
    this.filtroCategoria = null;
    this.filtroFornecedor = null;
    this.pagina = 1;
    this.carregar();
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

  verHistorico(produto: Produto): void {
    this.router.navigate(['/produtos', produto.id, 'historico']);
  }

  pedirInativacao(produto: Produto): void {
    this.produtoParaInativar = produto;
  }

  cancelarInativacao(): void {
    this.produtoParaInativar = null;
  }

  confirmarInativacao(): void {
    const produto = this.produtoParaInativar;
    if (!produto?.id) return;

    this.erro = '';
    this.sucesso = '';

    this.produtoService.inativar(produto.id).subscribe({
      next: () => {
        this.sucesso = 'Produto inativado com sucesso.';
        this.produtoParaInativar = null;
        this.carregar();
      },
      error: (err) => {
        this.erro = err.message;
        this.produtoParaInativar = null;
      },
    });
  }
}
