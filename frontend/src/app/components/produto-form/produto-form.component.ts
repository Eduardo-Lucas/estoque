import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Produto, UnidadeMedida } from '../../models/produto.model';
import { Categoria } from '../../models/categoria.model';
import { Fornecedor } from '../../models/fornecedor.model';
import { ProdutoService } from '../../services/produto.service';
import { CategoriaService } from '../../services/categoria.service';
import { FornecedorService } from '../../services/fornecedor.service';

@Component({
  selector: 'app-produto-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './produto-form.component.html',
  styleUrl: './produto-form.component.css',
})
export class ProdutoFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private produtoService = inject(ProdutoService);
  private categoriaService = inject(CategoriaService);
  private fornecedorService = inject(FornecedorService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  produtoId: number | null = null;
  carregando = false;
  erro = '';

  categorias: Categoria[] = [];
  fornecedores: Fornecedor[] = [];

  unidades: { valor: UnidadeMedida; rotulo: string }[] = [
    { valor: 'UN', rotulo: 'Unidade' },
    { valor: 'KG', rotulo: 'Quilograma' },
    { valor: 'LT', rotulo: 'Litro' },
    { valor: 'MT', rotulo: 'Metro' },
    { valor: 'CX', rotulo: 'Caixa' },
    { valor: 'PC', rotulo: 'Pacote' },
  ];

  get emEdicao(): boolean {
    return this.produtoId !== null;
  }

  form = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.minLength(2)]],
    sku: [''],
    codigo_barras: [''],
    descricao: [''],
    categoria: [null as number | null],
    fornecedor: [null as number | null],
    unidade_medida: ['UN' as UnidadeMedida, Validators.required],
    quantidade: [0, [Validators.required, Validators.min(0)]],
    estoque_minimo: [0, [Validators.required, Validators.min(0)]],
    preco_custo: [0, [Validators.required, Validators.min(0)]],
    preco: [0, [Validators.required, Validators.min(0)]],
    ativo: [true],
  });

  ngOnInit(): void {
    this.carregarCategorias();
    this.carregarFornecedores();

    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.produtoId = Number(idParam);
      this.carregarProduto(this.produtoId);
    }
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

  carregarProduto(id: number): void {
    this.carregando = true;
    this.produtoService.obter(id).subscribe({
      next: (produto) => {
        this.form.setValue({
          nome: produto.nome,
          sku: produto.sku ?? '',
          codigo_barras: produto.codigo_barras ?? '',
          descricao: produto.descricao ?? '',
          categoria: produto.categoria ?? null,
          fornecedor: produto.fornecedor ?? null,
          unidade_medida: produto.unidade_medida,
          quantidade: produto.quantidade,
          estoque_minimo: produto.estoque_minimo,
          preco_custo: Number(produto.preco_custo),
          preco: Number(produto.preco),
          ativo: produto.ativo,
        });
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar o produto.';
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

    const dados = this.form.getRawValue();
    const produto: Produto = {
      ...dados,
      sku: dados.sku || null,
    };

    const operacao = this.produtoId
      ? this.produtoService.atualizar(this.produtoId, produto)
      : this.produtoService.criar(produto);

    operacao.subscribe({
      next: () => this.router.navigate(['/produtos']),
      error: (err) => {
        this.erro = err.message;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['/produtos']);
  }
}
