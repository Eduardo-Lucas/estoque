import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResultadoImportacao } from '../../models/csv.model';
import { ResultadoImportacaoNfe } from '../../models/nfe.model';
import { ProdutoService } from '../../services/produto.service';
import { CategoriaService } from '../../services/categoria.service';
import { FornecedorService } from '../../services/fornecedor.service';

interface EstadoImportacaoCsv {
  importando: boolean;
  exportando: boolean;
  erro: string;
  sucesso: string;
  resultado: ResultadoImportacao | null;
}

function estadoCsvInicial(): EstadoImportacaoCsv {
  return { importando: false, exportando: false, erro: '', sucesso: '', resultado: null };
}

@Component({
  selector: 'app-importacoes',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './importacoes.component.html',
  styleUrl: './importacoes.component.css',
})
export class ImportacoesComponent {
  private produtoService = inject(ProdutoService);
  private categoriaService = inject(CategoriaService);
  private fornecedorService = inject(FornecedorService);

  produtoCsv = estadoCsvInicial();
  categoriaCsv = estadoCsvInicial();
  fornecedorCsv = estadoCsvInicial();

  produtoNfe = {
    importando: false,
    erro: '',
    sucesso: '',
    resultado: null as ResultadoImportacaoNfe | null,
  };

  importarProdutoCsv(event: Event): void {
    const arquivo = this.arquivoSelecionado(event);
    if (!arquivo) return;

    this.produtoCsv.erro = '';
    this.produtoCsv.sucesso = '';
    this.produtoCsv.resultado = null;
    this.produtoCsv.importando = true;

    this.produtoService.importarCsv(arquivo).subscribe({
      next: (resultado) => {
        this.produtoCsv.importando = false;
        this.produtoCsv.resultado = resultado;
        this.produtoCsv.sucesso = `${resultado.criados} produto(s) criado(s), ${resultado.atualizados} atualizado(s).`;
        this.limparInput(event);
      },
      error: (err) => {
        this.produtoCsv.importando = false;
        this.produtoCsv.erro = err.message;
        this.limparInput(event);
      },
    });
  }

  exportarProdutoCsv(): void {
    this.produtoCsv.erro = '';
    this.produtoCsv.exportando = true;

    this.produtoService.exportarCsv().subscribe({
      next: (blob) => {
        this.produtoCsv.exportando = false;
        this.baixarArquivo(blob, 'produtos.csv');
      },
      error: (err) => {
        this.produtoCsv.exportando = false;
        this.produtoCsv.erro = err.message;
      },
    });
  }

  importarProdutoNfe(event: Event): void {
    const arquivo = this.arquivoSelecionado(event);
    if (!arquivo) return;

    this.produtoNfe.erro = '';
    this.produtoNfe.sucesso = '';
    this.produtoNfe.resultado = null;
    this.produtoNfe.importando = true;

    this.produtoService.importarNfe(arquivo).subscribe({
      next: (resultado) => {
        this.produtoNfe.importando = false;
        this.produtoNfe.resultado = resultado;
        this.produtoNfe.sucesso = `NF-e ${resultado.numero_nfe} (${resultado.fornecedor}): `
          + `${resultado.itens_processados} item(ns) processado(s), `
          + `${resultado.itens_ja_processados} já processado(s) anteriormente.`;
        this.limparInput(event);
      },
      error: (err) => {
        this.produtoNfe.importando = false;
        this.produtoNfe.erro = err.message;
        this.limparInput(event);
      },
    });
  }

  importarCategoriaCsv(event: Event): void {
    const arquivo = this.arquivoSelecionado(event);
    if (!arquivo) return;

    this.categoriaCsv.erro = '';
    this.categoriaCsv.sucesso = '';
    this.categoriaCsv.resultado = null;
    this.categoriaCsv.importando = true;

    this.categoriaService.importarCsv(arquivo).subscribe({
      next: (resultado) => {
        this.categoriaCsv.importando = false;
        this.categoriaCsv.resultado = resultado;
        this.categoriaCsv.sucesso = `${resultado.criados} categoria(s) criada(s), ${resultado.atualizados} atualizada(s).`;
        this.limparInput(event);
      },
      error: (err) => {
        this.categoriaCsv.importando = false;
        this.categoriaCsv.erro = err.message;
        this.limparInput(event);
      },
    });
  }

  exportarCategoriaCsv(): void {
    this.categoriaCsv.erro = '';
    this.categoriaCsv.exportando = true;

    this.categoriaService.exportarCsv().subscribe({
      next: (blob) => {
        this.categoriaCsv.exportando = false;
        this.baixarArquivo(blob, 'categorias.csv');
      },
      error: (err) => {
        this.categoriaCsv.exportando = false;
        this.categoriaCsv.erro = err.message;
      },
    });
  }

  importarFornecedorCsv(event: Event): void {
    const arquivo = this.arquivoSelecionado(event);
    if (!arquivo) return;

    this.fornecedorCsv.erro = '';
    this.fornecedorCsv.sucesso = '';
    this.fornecedorCsv.resultado = null;
    this.fornecedorCsv.importando = true;

    this.fornecedorService.importarCsv(arquivo).subscribe({
      next: (resultado) => {
        this.fornecedorCsv.importando = false;
        this.fornecedorCsv.resultado = resultado;
        this.fornecedorCsv.sucesso = `${resultado.criados} fornecedor(es) criado(s), ${resultado.atualizados} atualizado(s).`;
        this.limparInput(event);
      },
      error: (err) => {
        this.fornecedorCsv.importando = false;
        this.fornecedorCsv.erro = err.message;
        this.limparInput(event);
      },
    });
  }

  exportarFornecedorCsv(): void {
    this.fornecedorCsv.erro = '';
    this.fornecedorCsv.exportando = true;

    this.fornecedorService.exportarCsv().subscribe({
      next: (blob) => {
        this.fornecedorCsv.exportando = false;
        this.baixarArquivo(blob, 'fornecedores.csv');
      },
      error: (err) => {
        this.fornecedorCsv.exportando = false;
        this.fornecedorCsv.erro = err.message;
      },
    });
  }

  private arquivoSelecionado(event: Event): File | undefined {
    const input = event.target as HTMLInputElement;
    return input.files?.[0];
  }

  private limparInput(event: Event): void {
    (event.target as HTMLInputElement).value = '';
  }

  private baixarArquivo(blob: Blob, nomeArquivo: string): void {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nomeArquivo;
    link.click();
    URL.revokeObjectURL(url);
  }
}
