from rest_framework import status
from rest_framework.viewsets import ViewSet 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Note
from .serializer import NoteSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.decorators import action
from loguru import logger


class NoteViewSet(ViewSet):
    """
    Description:
        A ViewSet to handle CRUD operations for the Note model. It includes actions 
        to list, create, retrieve, update, and delete notes for an authenticated user. 
        Additionally, provides custom actions to toggle the archive and trash status 
        of notes, and fetch archived or trashed notes.
    Permissions:
        - Requires authentication using JWT.
        - Only authenticated users can access the note-related operations.
    """

    permission_classes = [IsAuthenticated] 
    authentication_classes = [JWTAuthentication]

    def list(self, request):
        """
        Description:
            Fetch all non-archived, non-trashed notes for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with a list of notes and a success message.
        """
        try:
            notes = Note.objects.filter(user=request.user, is_archive=False, is_trash=False)
            serializer = NoteSerializer(notes, many=True)

            logger.info("Successfully fetched notes for user.")
            return Response({
                "message": "Successfully fetched notes for user.", 
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred", 
                "status": "error", 
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """
        Description:
            Create a new note for the authenticated user.
        Parameter:
            request (Request): The request object containing the note data to be created.
        Returns:
            Response: A response with the created note data and a success message.
        """
        try:
            serializer = NoteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)

            logger.info("Successfully created note for user.")
            return Response({
                "message": "Successfully created note for user.",
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {serializer.errors}")
            return Response({
                "message": "Unexpected error occurred", 
                "status": "error", 
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """
        Description:
            Retrieve a specific note by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
            pk (int): The primary key of the note to be retrieved.
        Returns:
            Response: A response with the note data and a success message.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note)

            logger.info("Successfully fetched a note for user using note id.")
            return Response({
                "message": "Successfully fetched a note for user using note id.", 
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred", 
                "status": "error", 
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """
        Description:
            Update a specific note by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object containing the updated note data.
            pk (int): The primary key of the note to be updated.
        Returns:
            Response: A response with a success message after updating the note.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()

                logger.info("Note updated successfully.")
                return Response({
                    "message": "Note updated successfully.", 
                    "status": "success", 
                }, status=status.HTTP_200_OK)
            
            logger.error(f"Unexpected error occurred: {serializer.errors}")
            return Response({
                "message": "Unexpected error occurred", 
                "status": "error", 
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred", 
                "status": "error", 
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """
        Description:
            Delete a specific note by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
            pk (int): The primary key of the note to be deleted.
        Returns:
            Response: A response with a success message after deleting the note.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.delete()

            logger.info("Note deleted successfully.")
            return Response({
                "message": "Note deleted successfully.",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return Response({
                "message": "An unexpected error occurred.",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Custom actions

    @action(detail=True, methods=['patch'])
    def toggle_archive(self, request, pk=None):
        """
        Description:
            Toggle the archive status of a specific note by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
            pk (int): The primary key of the note to be toggled.
        Returns:
            Response: A response with the updated archive status of the note.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.is_archive = not note.is_archive
            note.save()

            logger.info("Successfully toggled archive status.")
            return Response({
                "message": "Successfully toggled archive status.",
                "status": "success",
                "data": {"is_archive": note.is_archive}
            }, status=status.HTTP_200_OK)

        except Note.DoesNotExist:
            logger.error("Note not found.")
            return Response({
                "message": "Note not found.",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred.",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def archived(self, request):
        """
        Description:
            Fetch all archived notes for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with a list of archived notes and a success message.
        """
        try:
            notes = Note.objects.filter(user=request.user, is_archive=True, is_trash=False)
            serializer = NoteSerializer(notes, many=True)

            logger.info("Successfully fetched archived notes.")
            return Response({
                "message": "Successfully fetched archived notes.",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred.",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def toggle_trash(self, request, pk=None):
        """
        Description:
            Toggle the trash status of a specific note by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
            pk (int): The primary key of the note to be toggled.
        Returns:
            Response: A response with the updated trash status of the note.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.is_trash = not note.is_trash
            note.save()

            logger.info("Successfully toggled trash status.")
            return Response({
                "message": "Successfully toggled trash status.",
                "status": "success",
                "data": {"is_trash": note.is_trash}
            }, status=status.HTTP_200_OK)

        except Note.DoesNotExist:
            logger.error("Note not found.")
            return Response({
                "message": "Note not found.",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred.",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trashed(self, request):
        """
        Description:
            Fetch all trashed notes for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with a list of trashed notes and a success message.
        """
        try:
            notes = Note.objects.filter(user=request.user, is_trash=True)
            serializer = NoteSerializer(notes, many=True)

            logger.info("Successfully fetched trashed notes.")
            return Response({
                "message": "Successfully fetched trashed notes.",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return Response({
                "message": "Unexpected error occurred.",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)