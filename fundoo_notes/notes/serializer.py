from rest_framework import serializers
from .models import Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'description', 'color', 'image', 'is_archive', 'is_trash', 'reminder', 'user', 'collaborators', 'labels']
        read_only_fields = ['user']


class AddCollaboratorSerializer(serializers.Serializer):
    note_id = serializers.IntegerField(required=True, help_text='ID of the note')
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        required=True, 
        help_text='List of user IDs to be added as collaborators'
    )
    access_type = serializers.ChoiceField(
        choices=['read_only', 'read_write'], 
        required=True, 
        help_text='Access type for the collaborators'
    )

class RemoveCollaboratorSerializer(serializers.Serializer):
    note_id = serializers.IntegerField(required=True, help_text='ID of the note')
    collaborator_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        required=True, 
        help_text='List of collaborator IDs to be removed'
    )
