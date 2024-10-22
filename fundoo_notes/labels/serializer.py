from .models import Label
from rest_framework import serializers


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color', 'user']
        read_only_fields = ['user'] 