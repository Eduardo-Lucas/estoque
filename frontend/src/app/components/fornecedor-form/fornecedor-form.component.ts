import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Fornecedor } from '../../models/fornecedor.model';
import { FornecedorService } from '../../services/fornecedor.service';

@Component({
  selector: 'app-fornecedor-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './fornecedor-form.component.html',
  styleUrl: './fornecedor-form.component.css',
})
export class FornecedorFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private fornecedorService = inject(FornecedorService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  fornecedorId: number | null = null;
  carregando = false;
  erro = '';

  get emEdicao(): boolean {
    return this.fornecedorId !== null;
  }

  form = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.minLength(2)]],
    cnpj: [''],
    telefone: [''],
    email: ['', Validators.email],
    endereco: [''],
    ativo: [true],
  });

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.fornecedorId = Number(idParam);
      this.carregarFornecedor(this.fornecedorId);
    }
  }

  carregarFornecedor(id: number): void {
    this.carregando = true;
    this.fornecedorService.obter(id).subscribe({
      next: (fornecedor) => {
        this.form.setValue({
          nome: fornecedor.nome,
          cnpj: fornecedor.cnpj ?? '',
          telefone: fornecedor.telefone ?? '',
          email: fornecedor.email ?? '',
          endereco: fornecedor.endereco ?? '',
          ativo: fornecedor.ativo ?? true,
        });
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar o fornecedor.';
        this.carregando = false;
      },
    });
  }

  salvar(): void {
    this.erro = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const fornecedor = this.form.getRawValue() as Fornecedor;
    const operacao = this.fornecedorId
      ? this.fornecedorService.atualizar(this.fornecedorId, fornecedor)
      : this.fornecedorService.criar(fornecedor);

    operacao.subscribe({
      next: () => this.router.navigate(['/fornecedores']),
      error: (err) => {
        this.erro = err.message;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['/fornecedores']);
  }
}
