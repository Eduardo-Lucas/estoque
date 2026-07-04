from rest_framework.pagination import PageNumberPagination


class PaginacaoPadrao(PageNumberPagination):
    """Paginação padrão da API, permitindo o cliente escolher o tamanho da página via ?page_size=."""
    page_size_query_param = 'page_size'
    max_page_size = 100
