import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Fornecedor } from '../../models/fornecedor.model';
import { FornecedorService } from '../../services/fornecedor.service';

@Component({
  selector: 'app-fornecedor-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './fornecedor-list.component.html',
  styleUrl: './fornecedor-list.component.css',
})
export class FornecedorListComponent implements OnInit, OnDestroy {
  private fornecedorService = inject(FornecedorService);
  private router = inject(Router);

  fornecedores: Fornecedor[] = [];
  carregando = false;
  erro = '';
  sucesso = '';

  fornecedorParaRemover: Fornecedor | null = null;

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
    this.fornecedorService.listar({ nome: this.filtroNome }).subscribe({
      next: (resposta) => {
        this.fornecedores = resposta.results;
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar os fornecedores.';
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

  criarFornecedor(): void {
    this.router.navigate(['/fornecedores/novo']);
  }

  editar(fornecedor: Fornecedor): void {
    this.router.navigate(['/fornecedores', fornecedor.id, 'editar']);
  }

  pedirRemocao(fornecedor: Fornecedor): void {
    this.fornecedorParaRemover = fornecedor;
  }

  cancelarRemocao(): void {
    this.fornecedorParaRemover = null;
  }

  confirmarRemocao(): void {
    const fornecedor = this.fornecedorParaRemover;
    if (!fornecedor?.id) return;

    this.erro = '';
    this.sucesso = '';

    this.fornecedorService.remover(fornecedor.id).subscribe({
      next: () => {
        this.sucesso = 'Fornecedor removido com sucesso.';
        this.fornecedorParaRemover = null;
        this.carregar();
      },
      error: (err) => {
        this.erro = err.message;
        this.fornecedorParaRemover = null;
      },
    });
  }
}
