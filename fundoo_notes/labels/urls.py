from django.urls import path
from .views import LabelViewSet, LabelViewSetByID

urlpatterns = [
    path('labels', LabelViewSet.as_view(), name='label-list-create'),
    path('labels/<int:pk>', LabelViewSetByID.as_view(), name='label-update-delete-listbyid'),
]