import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Categoria } from '../../models/categoria.model';
import { CategoriaService } from '../../services/categoria.service';

@Component({
  selector: 'app-categoria-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './categoria-form.component.html',
  styleUrl: './categoria-form.component.css',
})
export class CategoriaFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private categoriaService = inject(CategoriaService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  categoriaId: number | null = null;
  carregando = false;
  erro = '';

  get emEdicao(): boolean {
    return this.categoriaId !== null;
  }

  form = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.minLength(2)]],
    descricao: [''],
    ativo: [true],
  });

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.categoriaId = Number(idParam);
      this.carregarCategoria(this.categoriaId);
    }
  }

  carregarCategoria(id: number): void {
    this.carregando = true;
    this.categoriaService.obter(id).subscribe({
      next: (categoria) => {
        this.form.setValue({
          nome: categoria.nome,
          descricao: categoria.descricao ?? '',
          ativo: categoria.ativo ?? true,
        });
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar a categoria.';
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

    const categoria = this.form.getRawValue() as Categoria;
    const operacao = this.categoriaId
      ? this.categoriaService.atualizar(this.categoriaId, categoria)
      : this.categoriaService.criar(categoria);

    operacao.subscribe({
      next: () => this.router.navigate(['/categorias']),
      error: (err) => {
        this.erro = err.message;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['/categorias']);
  }
}
