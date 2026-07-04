export interface ItemNfeNaoEncontrado {
  item: number;
  codigo_fornecedor: string;
  descricao: string;
}

export interface ErroItemNfe {
  item: number;
  mensagem: string;
}

export interface ResultadoImportacaoNfe {
  numero_nfe: string;
  fornecedor: string;
  itens_processados: number;
  itens_ja_processados: number;
  nao_encontrados: ItemNfeNaoEncontrado[];
  erros: ErroItemNfe[];
}
