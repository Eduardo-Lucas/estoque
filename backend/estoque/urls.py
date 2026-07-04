from rest_framework.routers import DefaultRouter
from .views import ProdutoViewSet, CategoriaViewSet, FornecedorViewSet, MovimentacaoViewSet

router = DefaultRouter()
router.register(r'produtos', ProdutoViewSet)
router.register(r'categorias', CategoriaViewSet)
router.register(r'fornecedores', FornecedorViewSet)
router.register(r'movimentacoes', MovimentacaoViewSet)

urlpatterns = router.urls
