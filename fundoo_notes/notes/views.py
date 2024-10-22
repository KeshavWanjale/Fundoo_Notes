from rest_framework import status
from rest_framework.viewsets import ViewSet 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Note
from .serializer import NoteSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError

from rest_framework.decorators import action
from loguru import logger
from notes.utils.redis_utils import RedisUtils

from .schedule import schedule_reminder

from drf_yasg.utils import swagger_auto_schema


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
            Fetch all active (non-archived, non-trashed) notes for the authenticated user.
            This method checks if the user's notes are available in the Redis cache. If so, it returns 
            the cached data. Otherwise, it fetches the data from the database, caches it, and returns it.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with the list of notes, fetched either from the cache or the database.
        """
        try:
            # Check if data exists in cache
            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key)

            if cached_notes:
                filtered_cached_notes = [
                note for note in cached_notes if not note.get('is_archive') and not note.get('is_trash')
                ]
                logger.info("Returning notes from cache.")
                return Response({
                    "message": "Successfully fetched notes for user from cache.",
                    "status": "success", 
                    "data": filtered_cached_notes
                }, status=status.HTTP_200_OK)

            notes = Note.objects.filter(user=request.user, is_archive=False, is_trash=False)
            serializer = NoteSerializer(notes, many=True)
            RedisUtils.save(cache_key, serializer.data)  # Cache the notes data
            logger.info("Successfully fetched notes from DB and saved to cache.")
            return Response({
                "message": "Successfully fetched notes for user from DB.", 
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
        
    @swagger_auto_schema(
        operation_description="Create a new note for the authenticated user.",
        request_body=NoteSerializer
    )
    def create(self, request):
        """
        Description:
            Create a new note for the authenticated user. Upon successful creation, 
            the new note is appended to the cached notes in Redis for the user.
        Parameter:
            request (Request): The request object containing the note data.
        Returns:
            Response: A response with the created note data and a success message.
        """
        try:
            serializer = NoteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            note = serializer.save(user=request.user)

            if note.reminder:
                schedule_reminder(note)

            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key) or []
            cached_notes.append(NoteSerializer(note).data)  # Serialize the newly created note
            RedisUtils.save(cache_key, cached_notes)


            logger.info("Successfully created and cached note for user.")
            return Response({
                "message": "Successfully created note for user and stored in cache.",
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            # Catch validation errors and return them in the response
            logger.error(f"Validation error occurred: {e}")
            return Response({
                "message": "Validation error occurred",
                "status": "error", 
                "error": serializer.errors if serializer else str(e)  # Use serializer errors if they exist
            }, status=status.HTTP_400_BAD_REQUEST)
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
        
    @swagger_auto_schema(
        operation_description="Update an existing note by its ID for the authenticated user.",
        request_body=NoteSerializer
    )
    def update(self, request, pk=None):
        """
        Description:
            Update an existing note for the authenticated user by its primary key (ID). 
            After updating, the cached note list is updated with the modified note.
        Parameters:
            request (Request): The request object containing the updated note data.
            pk (int): The primary key of the note to update.
        Returns:
            Response: A response with a success message after updating the note.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note, data=request.data, partial=True)
            if serializer.is_valid():
                note = serializer.save()

                if note.reminder:
                    schedule_reminder(note)

                cache_key = RedisUtils.get_cache_key(request.user.id)
                cached_notes = RedisUtils.get(cache_key) or []

                for cached_note in cached_notes:
                    if cached_note['id'] == note.id:
                        # Update the note directly in the list
                        cached_note.update(serializer.data)
                        break
                
                RedisUtils.save(cache_key, cached_notes)  # Update cache with modified notes

                logger.info("Note updated successfully and cache updated.")
                return Response({
                    "message": "Note updated successfully.", 
                    "status": "success",
                    "data": serializer.data 
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
            Delete a note for the authenticated user by its primary key (ID). After deletion, 
            the cached notes are updated to remove the deleted note.
        Parameters:
            request (Request): The request object.
            pk (int): The primary key of the note to delete.
        Returns:
            Response: A response confirming the successful deletion of the note.
        """
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note_id = note.id
            note.delete()

            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key) or []
            # Filter out the deleted note from the cached notes
            cached_notes = [n for n in cached_notes if n['id'] != note_id]
            # Save the updated cache
            RedisUtils.save(cache_key, cached_notes)

            logger.info("Note deleted successfully and cache updated.")
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

            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key) or []
            for cached_note in cached_notes:
                if cached_note['id'] == note.id:
                    cached_note['is_archive'] = note.is_archive
                    break
            RedisUtils.save(cache_key, cached_notes)

            logger.info("Successfully toggled archive status and updated cache.")

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

            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key) or []
            for cached_note in cached_notes:
                if cached_note['id'] == note.id:
                    cached_note['is_trash'] = note.is_trash
                    break
            RedisUtils.save(cache_key, cached_notes)

            logger.info("Successfully toggled trash status and updated the cache")
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