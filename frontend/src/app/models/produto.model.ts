export type UnidadeMedida = 'UN' | 'KG' | 'LT' | 'MT' | 'CX' | 'PC';

export interface Produto {
  id?: number;
  nome: string;
  sku?: string | null;
  codigo_barras?: string;
  descricao?: string;
  categoria?: number | null;
  categoria_nome?: string | null;
  fornecedor?: number | null;
  fornecedor_nome?: string | null;
  unidade_medida: UnidadeMedida;
  quantidade: number;
  estoque_minimo: number;
  preco_custo: number | string;
  preco: number | string;
  ativo: boolean;
  criado_em?: string;
  atualizado_em?: string;
}
