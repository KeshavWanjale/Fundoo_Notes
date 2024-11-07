from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login

from .serializer import *
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.reverse import reverse

from .tasks import send_verification_mail

from rest_framework.permissions import AllowAny

from drf_yasg.utils import swagger_auto_schema

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
   
@api_view(['GET'])
@permission_classes([AllowAny]) # Allow unauthenticated access
@throttle_classes([AnonRateThrottle])
def verify_registered_user(request, token):
    """
    Description:
        API view to verify a registered user by decoding the provided JWT token. 
        If the token is valid, the user's `is_verified` status is updated.
    Parameter:
        request (Request): The request object containing the user's verification token.
        token (str): The JWT token sent to verify the user.
    Returns:
        Response:
            - On success: A response with a success message and status code 200 if 
              the user is successfully verified.
            - On failure: A response with an error message and status code 400 
              if the token is invalid or expired.
    """
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = CustomUser.objects.get(id=user_id)

        if not user.is_verified:
            user.is_verified = True
            user.save()
        return Response({"message": "User verification successful", "status": "success"}, status=status.HTTP_200_OK)
    except:
        return Response({"message": "Invalid or expired token", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
    
    

class RegisterUser(APIView):
    """
    Description:
        API view to handle user registration. Registers a user using the data provided 
        in the POST request, generates a verification JWT token, and sends a verification 
        email(using celery) with a link to verify the user's account.
    Parameter:
        request (Request): The request object containing user registration data.
    Returns:
        Response:
            - On success: A response with a success message, user data, and a prompt 
              to verify the user's email. Status code 201.
            - On failure: A response with an error message detailing validation issues or 
              other errors. Status code 400.
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_description="API to register a new user and send a verification email.",
        request_body=UserRegistrationSerializer
    )
    def post(self,request):

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # create token
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            # Create verifiaction url using reverse
            verification_url = request.build_absolute_uri(
                reverse('verify_user',kwargs={'token': token})
            )
            # send verification mail
            subject = 'Verify your account'
            message = f'Hi {user.username},\n\nPlease verify your account using the link below:\n{verification_url}'
            recipient_list = [user.email]
              
            send_verification_mail.delay(subject, message, recipient_list)

            return Response({
                "message": "User registered successfully! Please verify your email.",
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
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
    permission_classes = [AllowAny]  # Allow unauthenticated access
    throttle_classes = [AnonRateThrottle, UserRateThrottle] 

    @swagger_auto_schema(
        operation_description="API to authenticate a user and return JWT tokens (access and refresh).",
        request_body=UserLoginSerializer
    )
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
    
class LoginForm(View):

    def get(self, request):
        return render(request, 'user/login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index_view')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'user/login.html') 
        
class RegisterForm(View):

    def get(self, request):
        return render(request=request,template_name='user/register.html')
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.POST)
        
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect('login_user')
        else:
            messages.error(request, "Registration failed. Please try again.")

        return render(request, 'user/register.html')
    
class IndexView(View):

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_user')
        # get- gives single user object, filter- gives queryset with user objects
        user_details = CustomUser.objects.get(id=request.user.id)
        return render(request, 'user/index.html', {'user_details': user_details}) 