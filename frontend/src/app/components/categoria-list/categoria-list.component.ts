import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Categoria } from '../../models/categoria.model';
import { CategoriaService } from '../../services/categoria.service';

@Component({
  selector: 'app-categoria-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './categoria-list.component.html',
  styleUrl: './categoria-list.component.css',
})
export class CategoriaListComponent implements OnInit, OnDestroy {
  private categoriaService = inject(CategoriaService);
  private router = inject(Router);

  categorias: Categoria[] = [];
  carregando = false;
  erro = '';
  sucesso = '';

  categoriaParaRemover: Categoria | null = null;

  filtroNome = '';
  private debounceFiltroNome?: ReturnType<typeof setTimeout>;

  get temFiltroAtivo(): boolean {
    return !!this.filtroNome;
  }

  ngOnInit(): void {
    this.carregar();
  }

  ngOnDestroy(): void {
    clearTimeout(this.debounceFiltroNome);
  }

  carregar(): void {
    this.carregando = true;
    this.categoriaService.listar({ nome: this.filtroNome }).subscribe({
      next: (resposta) => {
        this.categorias = resposta.results;
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar as categorias.';
        this.carregando = false;
      },
    });
  }

  alterarFiltroNome(event: Event): void {
    this.filtroNome = (event.target as HTMLInputElement).value;
    clearTimeout(this.debounceFiltroNome);
    this.debounceFiltroNome = setTimeout(() => this.carregar(), 300);
  }

  limparFiltro(): void {
    this.filtroNome = '';
    this.carregar();
  }

  criarCategoria(): void {
    this.router.navigate(['/categorias/novo']);
  }

  editar(categoria: Categoria): void {
    this.router.navigate(['/categorias', categoria.id, 'editar']);
  }

  pedirRemocao(categoria: Categoria): void {
    this.categoriaParaRemover = categoria;
  }

  cancelarRemocao(): void {
    this.categoriaParaRemover = null;
  }

  confirmarRemocao(): void {
    const categoria = this.categoriaParaRemover;
    if (!categoria?.id) return;

    this.erro = '';
    this.sucesso = '';

    this.categoriaService.remover(categoria.id).subscribe({
      next: () => {
        this.sucesso = 'Categoria removida com sucesso.';
        this.categoriaParaRemover = null;
        this.carregar();
      },
      error: (err) => {
        this.erro = err.message;
        this.categoriaParaRemover = null;
      },
    });
  }
}
