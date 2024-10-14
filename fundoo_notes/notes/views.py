from rest_framework import status
from rest_framework.viewsets import ViewSet 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Note
from .serializer import NoteSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

class NoteViewSet(ViewSet):
    """
    ViewSet for performing CRUD operations on the Note model.
    """
    permission_classes = [IsAuthenticated] 
    authentication_classes = [JWTAuthentication]

    def list(self, request):
        # GET: List all notes for the authenticated user

        try: 
            notes = Note.objects.filter(user=request.user)
            serializer = NoteSerializer(notes, many=True)
            return Response({
                "message": "Successfully fetched notes for user.", 
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "message": "Unexpected error occured", 
                "status": "error", 
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
        
    def create(self, request):
        # POST: Create a new note for the authenticated user

        try: 
            serializer = NoteSerializer(data=request.data)
            serializer.is_valid(raise_exception= True)
            serializer.save(user=request.user)
            return Response({
                "message": "Successfully created note for user.",
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except:
            return Response({
                "message": "Unexpected error occured", 
                "status": "error", 
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    

    def retrieve(self, request, pk=None):
        # GET: Retrieve a single note by its ID

        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note)
            return Response({
                "message": "Successfully fetched a note for user using note id.", 
                "status": "success", 
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "message": "Unexpected error occured", 
                "status": "error", 
                "error": str(e)
            },  status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


    def update(self, request, pk=None):
        # PUT: Update an existing note

        try:
            note = Note.objects.get(pk=pk, user=request.user)
            serializer = NoteSerializer(note, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                "message": "Note Updates Successfully", 
                "status": "success", 
            }, status=status.HTTP_200_OK)
            return Response({
                "message": "Unexpected error occured", 
                "status": "error", 
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
            "message": "Unexpected error occured", 
            "status": "error", 
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def destroy(self, request, pk=None):
        # DELETE: Delete an existing note
        
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            note.delete()
            return Response({
                "message": "Note deleted successfully.",
                "status": "success"
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "message": "An unexpected error occurred.",
                "status": "failed",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)