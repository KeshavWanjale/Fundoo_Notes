from django.urls import path
from .views import LabelViewSet

urlpatterns = [
    path('labels/', LabelViewSet.as_view(), name='label-list-create'),
    path('labels/<int:pk>/', LabelViewSet.as_view(), name='label-update-delete-listbyid'),
]