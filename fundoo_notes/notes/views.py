from rest_framework import status
from rest_framework.viewsets import ViewSet 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Note, Collaborator
from user.models import CustomUser  
from .serializer import NoteSerializer, AddCollaboratorSerializer, RemoveCollaboratorSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError

from rest_framework.decorators import action
from loguru import logger
from notes.utils.redis_utils import RedisUtils

from .schedule import schedule_reminder

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from labels.models import Label
from django.db.models import Q


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
                note for note in cached_notes if not note.get('is_archive') and not note.get('is_trash') or request.user.id in note.get('collaborators')
                ]
                logger.info("Returning notes from cache.")
                return Response({
                    "message": "Successfully fetched notes for user from cache.",
                    "status": "success", 
                    "data": filtered_cached_notes
                }, status=status.HTTP_200_OK)

            notes = Note.objects.filter(
                Q(user=request.user) | Q(collaborators=request.user),
                is_archive=False,
                is_trash=False
            ).distinct()
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
            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key)

            if cached_notes is not None:
                # Filter cached notes for archived notes
                archived_notes = [
                    note for note in cached_notes if note.get('is_archive') and not note.get('is_trash')
                ]
                if archived_notes:
                    logger.info("Retrieved archived notes from cache.")
                    return Response({
                        "message": "Successfully fetched archived notes.",
                        "status": "success",
                        "data": archived_notes
                    }, status=status.HTTP_200_OK)

            # If no cache or no archived notes in cache, fetch from the database
            archived_notes = Note.objects.filter(user=request.user, is_archive=True, is_trash=False)
            serializer = NoteSerializer(archived_notes, many=True)
            
            # Update cache with the latest notes data
            RedisUtils.save(cache_key, serializer.data)

            logger.info("Successfully fetched archived notes from database and updated cache.")
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
            cache_key = RedisUtils.get_cache_key(request.user.id)
            cached_notes = RedisUtils.get(cache_key)

            if cached_notes is not None:
                # Filter cached notes for trashed notes
                trashed_notes = [note for note in cached_notes if note.get('is_trash')]
                if trashed_notes:
                    logger.info("Retrieved trashed notes from cache.")
                    return Response({
                        "message": "Successfully fetched trashed notes.",
                        "status": "success",
                        "data": trashed_notes
                    }, status=status.HTTP_200_OK)

            # If no cache or no trashed notes in cache, fetch from the database
            trashed_notes = Note.objects.filter(user=request.user, is_trash=True)
            serializer = NoteSerializer(trashed_notes, many=True)
            
            # Update cache with the latest notes data
            RedisUtils.save(cache_key, serializer.data)

            logger.info("Successfully fetched trashed notes from database and updated cache.")
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
        
    @swagger_auto_schema(
        operation_description="Add collaborator.",
        request_body=AddCollaboratorSerializer,
    )
    @action(detail=False, methods=['POST'])
    def add_collaborator(self, request):
        """
        Description:
            Add a collaborator to a specific note by its ID. 
            Only the note owner can add collaborators.
        Parameter:
            request (Request): The request object containing the note ID and list of users to add as a collaborator with access_type.
        Returns:
            Response: A response with a success message and details of the collaborator added.
        """
        serializer = AddCollaboratorSerializer(data=request.data)
        if serializer.is_valid():
            note_id = serializer.validated_data['note_id']
            user_ids = serializer.validated_data['user_ids']
            access_type = serializer.validated_data['access_type']

            try:
                note = Note.objects.get(id=note_id, user=request.user)
                
                if request.user.id in user_ids:
                    return Response(
                        {'message': 'Owner cannot be added as a collaborator', 'status': 'error'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                users = CustomUser.objects.filter(pk__in=user_ids)
                valid_user_ids = {user.id for user in users}
                invalid_user_ids = set(user_ids) - valid_user_ids

                existing_collaborators = Collaborator.objects.filter(note=note, user__in=users)
                existing_user_ids = {collab.user.id for collab in existing_collaborators}

                new_collaborators = [
                    Collaborator(note=note, user=user, access_type=access_type)
                    for user in users if user.id not in existing_user_ids
                ]

                logger.info(f"Created new collaborators  {new_collaborators}.")
                Collaborator.objects.bulk_create(new_collaborators)

                for collaborator in existing_collaborators:
                    if collaborator.access_type != access_type:
                        collaborator.access_type = access_type
                        collaborator.save(update_fields=['access_type'])
                        logger.info(f"Updated collaborator access type for user_id {collaborator.user.id} on note_id {note_id}.")

                if invalid_user_ids:
                    logger.error(f"Invalid user IDs: {invalid_user_ids}")
                    return Response(
                        {
                            "message": f"Invalid user IDs: {invalid_user_ids}",
                            "status": "error"
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response(
                    {
                        "message": "Collaborators processed successfully",
                        "status": "success"
                    }, status=status.HTTP_200_OK)

            except Note.DoesNotExist:
                logger.error(f"Note with ID {note_id} not found.")
                return Response({"message": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        logger.error(f"Invalid serializer data: {serializer.errors}")
        return Response(
            {
                "message": "Invalid serializer data", 
                "status": "error", 
                "error": serializer.errors
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(
        operation_description="Remove collaborator.",
        request_body=RemoveCollaboratorSerializer,
    )
    @action(detail=False, methods=['POST'])
    def remove_collaborator(self, request):
        """
        Description:
            Remove the collaborator
        Parameter:
            request (Request): The request object containing the note ID and list of collaborators to remove.
        Returns:
            Response: A response with a success message if collaborator is removed.
        """
        serializer = RemoveCollaboratorSerializer(data=request.data)
        if serializer.is_valid():
            note_id = serializer.validated_data['note_id']
            collaborator_ids = serializer.validated_data['collaborator_ids']

            try:
                note = Note.objects.get(id=note_id, user=request.user)

                deleted_count, _ = Collaborator.objects.filter(note=note, user__id__in=collaborator_ids).delete()

                if deleted_count == 0:
                    logger.error(f"No collaborators were removed. None of the provided user IDs are collaborators on note_id {note_id}.")
                    return Response(
                        {
                            "message": "No collaborators were removed. The provided user IDs may not be collaborators on this note.",
                            "status": "error"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                logger.info("Collaborators removed successfully")
                return Response(
                    {
                        "message": "Collaborators removed successfully",
                        "status": "success"
                    },
                    status=status.HTTP_200_OK
                )

            except Note.DoesNotExist:
                logger.error(f"Note with ID {note_id} not found.")
                return Response(
                    {"message": "Note not found", "status": "error"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
        logger.error(f"Invalid serializer data: {serializer.errors}")
        return Response(
            {
                "message": "Invalid serializer data", 
                "status": "error", 
                "error": serializer.errors
            }, 
                status=status.HTTP_400_BAD_REQUEST
        )
    

    @swagger_auto_schema(
        method='post',
        operation_description="add labels from a note",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'label_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
            }
        )
    )
    @action(detail=False, methods=['post'])
    def add_labels(self, request):
        """
        desc: Adds labels to a specific note.
        params: request (Request): The HTTP request object with note ID and list of label IDs.
        return: Response: Success message or error message.
        """

        note_id = request.data.get('note_id')
        label_ids = request.data.get('label_ids', [])

        if not isinstance(label_ids, list):
            return Response(
                {'message': 'Invalid input data', 'status': 'error'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            note = Note.objects.get(pk=note_id, user=request.user)
            labels = Label.objects.filter(id__in=label_ids)
            note.labels.add(*labels)

            # cache_key = RedisUtils.get_cache_key(request.user.id)
            # cached_notes = RedisUtils.get(cache_key)
            
            # if cached_notes:
            #     for cached_note in cached_notes:
            #         if cached_note['id'] == note_id:
            #             cached_note['labels'] = [label.id for label in note.labels.all()]
            #             RedisUtils.save(cache_key, cached_notes)
            #             logger.info(f"Cache updated for note_id {note_id} after adding labels.")
            #             break

            # Collect all user IDs that need cache updates
            collaborators = note.collaborators.values_list('id', flat=True)
            user_ids_to_update = [request.user.id] + list(collaborators)

            # Prepare updated label list once to avoid recalculating it
            updated_labels = [label.id for label in note.labels.all()]

            # Update each user's cache for this note
            for user_id in user_ids_to_update:
                cache_key = RedisUtils.get_cache_key(user_id)
                cached_notes = RedisUtils.get(cache_key)

                if cached_notes:
                    # Find the note and update its labels
                    for cached_note in cached_notes:
                        if cached_note['id'] == note_id:
                            cached_note['labels'] = updated_labels
                            RedisUtils.save(cache_key, cached_notes)
                            logger.info(f"Cache updated for user_id {user_id} on note_id {note_id} after modifying labels.")
                            break
            
            logger.info("Labels added successfully")
            return Response(
                {'message': 'Labels added successfully', 'status': 'success'},
                status=status.HTTP_200_OK
            )

        except Note.DoesNotExist:
            logger.error("The requested note does not exist")
            return Response(
                {'message': 'Note not found', 'status': 'error', 'errors': 'The requested note does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error while adding labels: {e}")
            return Response(
                {'message': 'An unexpected error occurred', 'status': 'error', 'errors': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    
    @swagger_auto_schema(
        method='post',
        operation_description="remove labels from a note",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'label_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER))
            }
        )
    )
    @action(detail=False,methods=['post'])    
    def remove_labels(self,request):
        """
        desc: Remove labels from a specific note.
        params: request (Request): The HTTP request object with note ID and list of label IDs.
        return: Response: Success message or error message.
        """
        note_id = request.data.get('note_id')
        label_ids = request.data.get('label_ids')

        if not note_id and not isinstance(label_ids, list):
            logger.error("Invalid input data")
            return Response(
                {'message': 'Invalid input data', 'status': 'error'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            note = Note.objects.get(pk=note_id,user=request.user)
            labels = Label.objects.filter(id__in=label_ids)
            note.labels.remove(*labels)

            # cache_key = RedisUtils.get_cache_key(request.user.id)
            # cached_notes = RedisUtils.get(cache_key)
            
            # if cached_notes:
            #     for cached_note in cached_notes:
            #         if cached_note['id'] == note_id:
            #             cached_note['labels'] = [label.id for label in note.labels.all()]
            #             RedisUtils.save(cache_key, cached_notes)
            #             logger.info(f"Cache updated for note_id {note_id} after removing labels.")
            #             break

            # Collect all user IDs that need cache updates
            collaborators = note.collaborators.values_list('id', flat=True)
            user_ids_to_update = [request.user.id] + list(collaborators)

            # Prepare updated label list once to avoid recalculating it
            updated_labels = [label.id for label in note.labels.all()]

            # Update each user's cache for this note
            for user_id in user_ids_to_update:
                cache_key = RedisUtils.get_cache_key(user_id)
                cached_notes = RedisUtils.get(cache_key)

                if cached_notes:
                    # Find the note and update its labels
                    for cached_note in cached_notes:
                        if cached_note['id'] == note_id:
                            cached_note['labels'] = updated_labels
                            RedisUtils.save(cache_key, cached_notes)
                            logger.info(f"Cache updated for user_id {user_id} on note_id {note_id} after modifying labels.")
                            break
                        
            logger.info("Labels removed successfully")
            return Response(
                {'message': 'Labels removed successfully', 'status': 'success'},
                status=status.HTTP_200_OK
            )
        
        except Note.DoesNotExist:
            logger.error('The requested note does not exist.')
            return Response(
                {'message': 'Note not found', 'status': 'error', 'errors': 'The requested note does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error while removing labels: {e}")
            return Response(
                {'message': 'An unexpected error occurred', 'status': 'error', 'errors': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        