export type TipoMovimentacao = 'REQUISICAO' | 'DEVOLUCAO';

export interface Movimentacao {
  id?: number;
  produto: number;
  produto_nome?: string;
  tipo: TipoMovimentacao;
  quantidade: number;
  solicitante: string;
  observacao?: string;
  data?: string;
}
