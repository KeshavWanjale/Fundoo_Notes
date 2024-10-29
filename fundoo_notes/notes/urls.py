from rest_framework.routers import DefaultRouter
from .views import NoteViewSet

router = DefaultRouter()
router.trailing_slash=''
router.register(r'', NoteViewSet, basename='notes')

urlpatterns = router.urls