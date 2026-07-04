"""
Parsing do XML de NF-e (nota fiscal eletrônica, padrão SEFAZ).

Módulo puro, sem acesso a banco: recebe o conteúdo do arquivo e devolve os
dados já estruturados. A orquestração (matching de produto/fornecedor,
persistência) fica em `views.py`.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

import defusedxml.ElementTree as ET
from django.utils import timezone

NFE_NS = 'http://www.portalfiscal.inf.br/nfe'


class NFeInvalidaError(Exception):
    """Levantada quando o XML não é uma NF-e válida ou está corrompido."""


@dataclass
class ItemNFe:
    numero_item: int
    codigo_produto_fornecedor: str
    descricao: str
    quantidade: Decimal
    valor_unitario: Decimal


@dataclass
class EmitenteNFe:
    cnpj: str
    nome: str


@dataclass
class DadosNFe:
    chave_acesso: str
    numero: str
    valor_total: Decimal
    data_emissao: datetime | None
    emitente: EmitenteNFe
    itens: list[ItemNFe]


def _tag(nome: str) -> str:
    return f'{{{NFE_NS}}}{nome}'


def _texto(elemento, caminho: str, obrigatorio: bool = True) -> str:
    encontrado = elemento.find(caminho)
    texto = (encontrado.text or '').strip() if encontrado is not None else ''
    if obrigatorio and not texto:
        raise NFeInvalidaError(f'Campo obrigatório ausente na NF-e: {caminho}')
    return texto


def _decimal(texto: str) -> Decimal:
    try:
        return Decimal(texto or '0')
    except InvalidOperation:
        raise NFeInvalidaError(f'Valor numérico inválido na NF-e: "{texto}"')


def _extrair_chave_acesso(root, inf_nfe) -> str:
    # a chave do protocolo de autorização é mais confiável quando presente
    chave = _texto(root, f'.//{_tag("protNFe")}/{_tag("infProt")}/{_tag("chNFe")}', obrigatorio=False)
    if chave:
        return chave

    # fallback: atributo Id="NFe" + 44 dígitos no próprio infNFe
    id_attr = inf_nfe.attrib.get('Id', '')
    chave = id_attr[3:] if id_attr.startswith('NFe') else id_attr
    if not chave:
        raise NFeInvalidaError('Não foi possível identificar a chave de acesso da NF-e.')
    return chave


def _extrair_data_emissao(inf_nfe) -> datetime | None:
    # dhEmi (layout atual, com timezone) ou dEmi (layout antigo, sem hora)
    bruto = _texto(inf_nfe, f'{_tag("ide")}/{_tag("dhEmi")}', obrigatorio=False)
    if not bruto:
        bruto = _texto(inf_nfe, f'{_tag("ide")}/{_tag("dEmi")}', obrigatorio=False)
    if not bruto:
        return None
    try:
        data = datetime.fromisoformat(bruto)
    except ValueError:
        return None
    # dEmi (layout antigo) não traz timezone; assume o horário local do projeto
    return timezone.make_aware(data) if timezone.is_naive(data) else data


def _extrair_emitente(inf_nfe) -> EmitenteNFe:
    cnpj = _texto(inf_nfe, f'{_tag("emit")}/{_tag("CNPJ")}')
    nome = _texto(inf_nfe, f'{_tag("emit")}/{_tag("xNome")}')
    return EmitenteNFe(cnpj=cnpj, nome=nome)


def _extrair_itens(inf_nfe) -> list[ItemNFe]:
    dets = inf_nfe.findall(_tag('det'))
    if not dets:
        raise NFeInvalidaError('A NF-e não contém itens (nenhum elemento "det" encontrado).')

    itens = []
    for det in dets:
        numero_item_bruto = det.attrib.get('nItem')
        if not numero_item_bruto:
            raise NFeInvalidaError('Item da NF-e sem número (atributo "nItem" ausente).')

        prod = det.find(_tag('prod'))
        if prod is None:
            raise NFeInvalidaError(f'Item {numero_item_bruto} sem dados de produto (elemento "prod" ausente).')

        itens.append(ItemNFe(
            numero_item=int(numero_item_bruto),
            codigo_produto_fornecedor=_texto(prod, _tag('cProd'), obrigatorio=False),
            descricao=_texto(prod, _tag('xProd')),
            quantidade=_decimal(_texto(prod, _tag('qCom'))),
            valor_unitario=_decimal(_texto(prod, _tag('vUnCom'))),
        ))
    return itens


def parse_nfe(conteudo_xml: bytes) -> DadosNFe:
    """
    Recebe os bytes do arquivo XML de uma NF-e e devolve os dados estruturados.
    Aceita tanto o XML de distribuição (envelopado em nfeProc) quanto o NFe puro.
    Levanta NFeInvalidaError em qualquer problema estrutural do arquivo.
    """
    try:
        root = ET.fromstring(conteudo_xml)
    except ET.ParseError as exc:
        raise NFeInvalidaError(
            'Não foi possível ler o XML. Verifique se o arquivo não está corrompido.'
        ) from exc

    inf_nfe = root.find(f'.//{_tag("infNFe")}')
    if inf_nfe is None:
        raise NFeInvalidaError('O arquivo não parece ser um XML de NF-e (elemento "infNFe" não encontrado).')

    return DadosNFe(
        chave_acesso=_extrair_chave_acesso(root, inf_nfe),
        numero=_texto(inf_nfe, f'{_tag("ide")}/{_tag("nNF")}'),
        valor_total=_decimal(_texto(inf_nfe, f'{_tag("total")}/{_tag("ICMSTot")}/{_tag("vNF")}')),
        data_emissao=_extrair_data_emissao(inf_nfe),
        emitente=_extrair_emitente(inf_nfe),
        itens=_extrair_itens(inf_nfe),
    )
