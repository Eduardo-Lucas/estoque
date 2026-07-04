export interface Produto {
  id?: number;
  nome: string;
  descricao?: string;
  quantidade: number;
  preco: number | string;
  criado_em?: string;
  atualizado_em?: string;
}

export interface ErroImportacao {
  linha: number;
  mensagem: string;
}

export interface ResultadoImportacao {
  criados: number;
  atualizados: number;
  erros: ErroImportacao[];
}
