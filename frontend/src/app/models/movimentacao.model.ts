export type TipoMovimentacao = 'REQUISICAO' | 'DEVOLUCAO' | 'COMPRA';

export const TIPO_MOVIMENTACAO_LABELS: Record<TipoMovimentacao, string> = {
  REQUISICAO: 'Requisição',
  DEVOLUCAO: 'Devolução',
  COMPRA: 'Compra',
};

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
