from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class UserLoginTest(TestCase):
    def setUp(self):
        self.username = 'existinguser'
        self.password = 'securepass123'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            first_name='Existing',
            last_name='User'
        )

    def test_existing_user_can_login(self):
        # Attempt to authenticate with correct credentials
        user = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(user, 'User should be authenticated successfully')
        self.assertEqual(user.username, self.username)
        self.assertTrue(user.check_password(self.password))


