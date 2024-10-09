from rest_framework import serializers
from .models import CustomUser
from .utils import validate_email,validate_password,validate_username

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Description:
        Serializer for registering a new user. Validates the email, username,
        and password, and creates a new user upon successful validation.
    Parameter:
        username (CharField): The username of the user to be registered.
        email (EmailField): The email of the user to be registered.
        password (CharField): The password of the user to be registered.
    Returns:
        A CustomUser instance created with the validated data.
    """

    username = serializers.CharField(validators=[])
    # This defines a username field as a CharField (string field) but overrides the default validation by passing 
    # an empty list to validators, meaning no default validation is applied.

    class Meta:
        model = CustomUser
        fields = ["email", "username", "password"]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        """
        Description:
            Validates the user-provided data for email, username, and password.
        Parameter:
            data (dict): Dictionary containing email, username, and password.
        Returns:
            dict: Validated data for user registration.
        """

        email = data.get("email")
        username = data.get("username")
        password = data.get("password")

        if not validate_email(email):
            raise serializers.ValidationError("Invalid Email format")
        if not validate_username(username):
            raise serializers.ValidationError("Invalid Username format")
        if not validate_password(password):
            raise serializers.ValidationError("Invalid Password format")

        return data
    
    def create(self, validated_data):
        """
        Description:
            Creates and returns a new user instance with the validated data.
        Parameter:
            validated_data (dict): Validated data to create the user.
        Returns:
            CustomUser: A newly created user instance.
        """

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
    
class UserLoginSerializer(serializers.Serializer):
    """
    Description:
        Serializer for user login. Validates the user's email and password 
        fields.
    Parameter:
        email (EmailField): The email of the user attempting to log in.
        password (CharField): The password of the user attempting to log in.
    Returns:
        dict: Validated data containing email and password for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Description:
            Validates that both email and password fields are provided for login.
        Parameter:
            data (dict): Dictionary containing email and password.
        Returns:
            dict: Validated data for login.
        """
        email = data.get("email")
        password = data.get("password")

        if not email:
            raise serializers.ValidationError("Email is required")
        if not password:
            raise serializers.ValidationError("Password is required")

        return data