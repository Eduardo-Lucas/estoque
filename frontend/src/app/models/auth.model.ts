export interface Credenciais {
  email: string;
  password: string;
}

export interface TokenResponse {
  token: string;
  email?: string;
}

export interface DadosRegistro {
  email: string;
  password: string;
  nome: string;
  empresa_razao_social: string;
  empresa_nome_fantasia?: string;
  empresa_cnpj: string;
}

export interface RespostaRegistro {
  detail: string;
}
