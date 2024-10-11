import re
def validate_username(username):
    """
    Description:
        Validates the user name based on specific rules:
        - The first name must start with a capital letter.
        - The first name must have a minimum of 3 characters.
    Parameters:
        username (str): The user name to be validated.
    Return:
        bool: Returns True if the user name is valid, otherwise False.
    """
    pattern = re.compile(r"^[A-Z][a-zA-Z]{2,}$")

    if pattern.match(username) :
        return True
    else:
        return False
    
def validate_email(email):
    """
    Description:
        Validates that the given email follows the general format of an email address:
        a combination of letters and numbers, followed by an optional dot (.), an '@',
        a domain name, and a top-level domain (TLD). The domain and TLD must be alphabetic.
    Parameters:
        email (str): The email string to validate.
    Returns:
        bool: Returns True if the email is valid, otherwise False.
    """
    pattern = re.compile(r'^([a-zA-Z0-9]{3,})+(\.[a-zA-Z0-9]+)?@[a-zA-Z]{2,}\.[a-z]{2,}(?:\.[a-zA-Z]{2,})?$')
    if pattern.match(email):
        return True
    else:
        return False

def validate_password(password):
    """
    Description:
        Validates that the given password meets the following criteria:
        - Contains at least one uppercase letter.
        - Contains at least one digit.
        - Contains at least one special character from !@#$%^&*()_+.
        - Has a minimum length of 8 characters.
    Parameters:
        password (str): The password string to validate.
    Returns:
        bool: Returns True if the password is valid, otherwise False.
    """
    pattern = re.compile(
        r'^(?=.*[A-Z])'           
        r'(?=.*\d)'               
        r'(?=.*[!@#$%^&*()_+])'  
        r'[A-Za-z\d!@#$%^&*()_+]{8,}$'
    )

    if pattern.match(password):
        return True
    else:
        return False