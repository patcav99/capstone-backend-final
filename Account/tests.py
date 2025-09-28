from django.urls import reverse
from rest_framework.test import APIClient
from django.test import TestCase

#TestID 13: deletes a subscription and ensures it's removed from the database
class SubscriptionDeleteTest(TestCase):
	def test_delete_subscription_removes_from_db(self):
		sub = Subscription.objects.create(name='DeleteMe')
		self.assertTrue(Subscription.objects.filter(name='DeleteMe').exists())
		client = APIClient()
		url = reverse('subscription-delete', args=[sub.id])
		response = client.delete(url)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(Subscription.objects.filter(name='DeleteMe').exists())

from django.test import TestCase
from .models import Subscription

#TestID 1: creates a subscription and verifies it exists in the database
class SubscriptionModelTest(TestCase):
	def test_create_subscription(self):
		# Create a new subscription
		sub = Subscription.objects.create(name='Test Subscription')
		# Fetch from DB
		fetched = Subscription.objects.get(name='Test Subscription')
		self.assertEqual(fetched.name, 'Test Subscription')
