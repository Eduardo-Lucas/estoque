import { Component, OnInit, inject } from '@angular/core';
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
export class FornecedorListComponent implements OnInit {
  private fornecedorService = inject(FornecedorService);
  private router = inject(Router);

  fornecedores: Fornecedor[] = [];
  carregando = false;
  erro = '';
  sucesso = '';

  fornecedorParaRemover: Fornecedor | null = null;

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando = true;
    this.fornecedorService.listar().subscribe({
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
