from rest_framework.routers import DefaultRouter
from .views import ProdutoViewSet, MovimentacaoViewSet

router = DefaultRouter()
router.register(r'produtos', ProdutoViewSet)
router.register(r'movimentacoes', MovimentacaoViewSet)

urlpatterns = router.urls
