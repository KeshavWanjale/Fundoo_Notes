from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate

from .serializer import *
from rest_framework_simplejwt.tokens import RefreshToken

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
        the user. Upon successful authentication, it returns JWT tokens (refresh 
        and access tokens).
    Parameter:
        request (Request): The request object containing user login credentials 
        (email and password).
    Returns:
        Response: 
            - On success: A response with a success message, user data, 
              refresh token, and access token.
            - On failure: A response with an error message for invalid credentials 
              or validation errors.
    """
    def post(self,request):

        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Login successful!", 
                    "status": "success", 
                    "data": serializer.data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            
            return Response({"message": "Unexpected error occured", "error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Unexpected error occured", "status": "error", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

