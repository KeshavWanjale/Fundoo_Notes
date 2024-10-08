from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
import json

from .models import CustomUser
from .utils import *

# Create your views here.

@csrf_exempt
def register_user(request):
    """
    Description:
    Handles user registration by creating a new user account with a valid email, username, and password. 
    Validates input data and returns appropriate responses for missing or invalid data.
    Parameters:
    request (HttpRequest): The HTTP request object containing POST data with 'email', 'username', and 'password'.
    Returns:
    JsonResponse: A JSON response indicating success or failure of user registration.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            username = data.get('username')
            if not all([email, password, username]):
                return JsonResponse({"error": "Missing fields"}, status=400)
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already in use"}, status=400)
            if not validate_username(username):
                return JsonResponse({"error": "Invalid Username format"}, status=400)
            if not validate_email(email):
                return JsonResponse({"error": "Invalid Email format"}, status=400)
            if not validate_password(password):
                return JsonResponse({"error": "Invalid Password format"}, status=400)
            user = CustomUser.objects.create_user(
                email=email,
                username=username,
                password=password
            )
            return JsonResponse({"message": "User registered successfully!", "status": "success", "data": {"email": email, "username": username}}, status=201)
        except:
            return JsonResponse({"messege": "Unexpected error occured.", "status": "error"}, status ="error")
    else:
        return JsonResponse({"error": "Only POST request is allowed"}, status=405)


@csrf_exempt
def login_user(request):
    """
    Description:
    Handles user login by authenticating the user with the provided email and password. 
    Returns success if the user credentials are valid, otherwise an error message.
    Parameters:
    request (HttpRequest): The HTTP request object containing POST data with 'email' and 'password'.
    Returns:
    JsonResponse: A JSON response indicating success or failure of user login.
    """
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            email = body.get('email')
            password = body.get('password')

            if not email or not password:
                return JsonResponse({"error": "Email and password are required"}, status=400)
            
            user = authenticate(email=email, password=password)

            if user is not None:
                return JsonResponse({"message": "Login successful!"}, status=200)
            else:
                return JsonResponse({"error": "Invalid email or password"}, status=400)

        except:
            return JsonResponse({"messege": "Unexpected error occured.", "status": "error"}, status ="error")
    else:
        return JsonResponse({"error": "Only POST request is allowed"}, status=405)
