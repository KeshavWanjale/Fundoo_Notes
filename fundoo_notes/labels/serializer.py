from .models import Lable
from rest_framework import serializers


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lable
        fields = ['id', 'name', 'color', 'user']
        read_only_fields = ['user'] 