from django.test import TestCase
from django.contrib.auth.models import User

class UserRegistrationTest(TestCase):
    def test_create_new_user_account(self):
        username = 'newuser'
        password = 'newpass123'
        first_name = 'Test'
        last_name = 'User'
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        # Check user exists
        self.assertTrue(User.objects.filter(username=username).exists())
        # Check user fields
        created_user = User.objects.get(username=username)
        self.assertEqual(created_user.first_name, first_name)
        self.assertEqual(created_user.last_name, last_name)
        self.assertTrue(created_user.check_password(password))
