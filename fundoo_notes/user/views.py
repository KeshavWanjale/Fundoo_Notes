from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate

from .serializer import *

# Create your views here.


class RegisterUser(APIView):
    """
    Description:
        API view to handle user registration. Receives user data via POST 
        request, validates it using `UserRegistrationSerializer`, and creates 
        a new user if validation is successful.
    Parameter:
        request (Request): The request object containing user registration data.
    Returns:
        Response: A response with a success message and user data if 
        registration is successful, or an error message with validation errors.
    """
    def post(self,request):

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!", "status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        
        return Response({"message": "Unexpected error occured", "status": "error", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    


class LoginUser(APIView):
    """
    Description:
        API view to handle user login. Receives email and password via POST 
        request, validates them using `UserLoginSerializer`, and authenticates 
        the user.
    Parameter:
        request (Request): The request object containing user login credentials.
    Returns:
        Response: A response with a success message if login is successful, or 
        an error message for invalid credentials or validation errors.
    """
    def post(self,request):

        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)

            if user is not None:
                return Response({"message": "Login successful!", "status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Unexpected error occured", "error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Unexpected error occured", "status": "error", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

