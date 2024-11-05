from django.urls import path
from .views import LabelViewSet, LabelViewSetByID, RawSQLLabelView, RawSQLLabelViewByID

urlpatterns = [
    path('', LabelViewSet.as_view(), name='label-list-create'),
    path('<int:pk>', LabelViewSetByID.as_view(), name='label-update-delete'),
    path('raw',RawSQLLabelView.as_view(), name='raw-lable-list'),
    path('raw/<int:pk>',RawSQLLabelViewByID.as_view(), name='raw-lable-detail')
]