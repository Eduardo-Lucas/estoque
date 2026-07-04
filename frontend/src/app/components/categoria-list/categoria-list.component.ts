import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Categoria } from '../../models/categoria.model';
import { ResultadoImportacao } from '../../models/csv.model';
import { CategoriaService } from '../../services/categoria.service';

@Component({
  selector: 'app-categoria-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './categoria-list.component.html',
  styleUrl: './categoria-list.component.css',
})
export class CategoriaListComponent implements OnInit {
  private categoriaService = inject(CategoriaService);
  private router = inject(Router);

  categorias: Categoria[] = [];
  carregando = false;
  erro = '';
  sucesso = '';

  categoriaParaRemover: Categoria | null = null;

  importando = false;
  exportando = false;
  resultadoImportacao: ResultadoImportacao | null = null;

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando = true;
    this.categoriaService.listar().subscribe({
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

  criarCategoria(): void {
    this.router.navigate(['/categorias/novo']);
  }

  editar(categoria: Categoria): void {
    this.router.navigate(['/categorias', categoria.id, 'editar']);
  }

  importarCsv(event: Event): void {
    const input = event.target as HTMLInputElement;
    const arquivo = input.files?.[0];
    if (!arquivo) return;

    this.erro = '';
    this.sucesso = '';
    this.resultadoImportacao = null;
    this.importando = true;

    this.categoriaService.importarCsv(arquivo).subscribe({
      next: (resultado) => {
        this.importando = false;
        this.resultadoImportacao = resultado;
        this.sucesso = `${resultado.criados} categoria(s) criada(s), ${resultado.atualizados} atualizada(s).`;
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

    this.categoriaService.exportarCsv().subscribe({
      next: (blob) => {
        this.exportando = false;
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'categorias.csv';
        link.click();
        URL.revokeObjectURL(url);
      },
      error: (err) => {
        this.exportando = false;
        this.erro = err.message;
      },
    });
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
