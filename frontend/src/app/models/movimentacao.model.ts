export type TipoMovimentacao =
  | 'REQUISICAO'
  | 'DEVOLUCAO'
  | 'COMPRA'
  | 'AJUSTE_POSITIVO'
  | 'AJUSTE_NEGATIVO';

export const TIPO_MOVIMENTACAO_LABELS: Record<TipoMovimentacao, string> = {
  REQUISICAO: 'Requisição',
  DEVOLUCAO: 'Devolução',
  COMPRA: 'Compra',
  AJUSTE_POSITIVO: 'Ajuste de inventário (+)',
  AJUSTE_NEGATIVO: 'Ajuste de inventário (-)',
};

export interface Movimentacao {
  id?: number;
  produto: number;
  produto_nome?: string;
  tipo: TipoMovimentacao;
  quantidade: number;
  custo_unitario?: number | string | null;
  solicitante: string;
  observacao?: string;
  data?: string;
}
