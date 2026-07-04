export interface ErroImportacao {
  linha: number;
  mensagem: string;
}

export interface ResultadoImportacao {
  criados: number;
  atualizados: number;
  erros: ErroImportacao[];
}
