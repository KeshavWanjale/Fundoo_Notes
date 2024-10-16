from .models import Lable
from .serializer import LabelSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from loguru import logger


class LabelViewSet(GenericAPIView, ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    """
    Description:
        A ViewSet to handle CRUD operations for the Label model. It includes actions 
        to list, create, update, and delete labels for an authenticated user.
    Permissions:
        - Requires authentication using JWT.
        - Only authenticated users can access the label-related operations.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = LabelSerializer
    queryset = Lable.objects.all()

    def get_queryset(self):
        """
        Description:
            Fetches only the labels belonging to the logged-in user.
        Returns:
            QuerySet: A queryset containing the labels for the authenticated user.
        """
        return self.queryset.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        Description:
            Fetch all labels for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with a list of labels and a success message.
        """
        try:
            response = super().list(request, *args, **kwargs)
            logger.info("Successfully fetched labels for user")
            return Response({
                "message": "Successfully fetched labels for user.",
                "status": "success",
                "data": response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return Response({
                "message": "Unexpected error occurred",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """
        Description:
            Create a new label for the authenticated user.
        Parameter:
            request (Request): The request object containing the label data to be created.
        Returns:
            Response: A response with the created label data and a success message.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            logger.info("Successfully created label for user.")
            return Response({
                "message": "Label created",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return Response({
                "message": "Unexpected error occurred",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        """
        Description:
            Update a specific label by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object containing the updated label data.
        Returns:
            Response: A response with a success message after updating the label.
        """
        try:
            logger.info("Updating label with ID")
            response = super().update(request, *args, **kwargs)
            logger.info("Successfully updated label with ID")
            return Response({
                "message": "Label updated successfully.",
                "status": "success",
                "data": response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return Response({
                "message": "Unexpected error occurred",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        """
        Description:
            Delete a specific label by its primary key for the authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with a success message after deleting the label.
        """
        try:
            logger.info("Deleting label with ID")
            response = super().destroy(request, *args, **kwargs)
            logger.info("Successfully deleted label with ID")
            return Response({
                "message": "Label deleted successfully.",
                "status": "success",
                "data": response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return Response({
                "message": "Unexpected error occurred",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)