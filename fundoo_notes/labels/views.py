from .models import Label
from .serializer import LabelSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from loguru import logger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class LabelViewSet(GenericAPIView, ListModelMixin, CreateModelMixin):
    """
    Description:
        A viewset that allows authenticated users to create and fetch labels. 
        It ensures that the operations are performed within the context of the logged-in user.
    Permissions:
        Requires JWT authentication to access label-related operations.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = LabelSerializer
    queryset = Label.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Label.objects.none()
        return self.queryset.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        Description:
            Retrieves a list of labels that belong to the currently authenticated user.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response containing the list of labels and a success message.
        """
        response = super().list(request, *args, **kwargs)
        return Response({
            "message": "Successfully fetched labels.",
            "status": "success",
            "data": response.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new label.",
        request_body=LabelSerializer
    )
    def post(self, request, *args, **kwargs):
        """
        Description:
            Validates and saves a new label associated with the authenticated user.
        Parameter:
            request (Request): The request object containing the label data to be created.
        Returns:
            Response: A response with the created label data and a success message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            "message": "Label created successfully.",
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class LabelViewSetByID(GenericAPIView, UpdateModelMixin, DestroyModelMixin):
    """
    Description:
        A viewset that allows authenticated users to update or delete a specific label
        based on the provided ID. It ensures that the operations are performed within the 
        context of the logged-in user.
    Permissions:
        Requires JWT authentication to access label-related operations.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = LabelSerializer
    queryset = Label.objects.all()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Label.objects.none()
        return self.queryset.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Update a specific label.",
        request_body=LabelSerializer,
        manual_parameters=[openapi.Parameter('id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)]
    )
    def put(self, request, *args, **kwargs):
        """
        Description:
            Validates and updates the label identified by the provided ID.
        Parameter:
            request (Request): The request object containing the updated label data.
        Returns:
            Response: A response with the updated label data and a success message.
        """
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Label updated successfully.",
            "status": "success",
            "data": response.data
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Description:
            Deletes the label identified by the provided ID.
        Parameter:
            request (Request): The request object from the authenticated user.
        Returns:
            Response: A response with a success message after the label has been deleted.
        """
        response = super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Label deleted successfully.",
            "status": "success"
        }, status=status.HTTP_200_OK)
