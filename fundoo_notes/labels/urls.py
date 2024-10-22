from django.urls import path
from .views import LabelViewSet, LabelViewSetByID

urlpatterns = [
    path('', LabelViewSet.as_view(), name='label-list-create'),
    path('<int:pk>', LabelViewSetByID.as_view(), name='label-update-delete-listbyid'),
]