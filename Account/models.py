from django.db import models


# Model to store subscription names

from django.contrib.auth.models import User

# Model to store subscription names
class Subscription(models.Model):
	name = models.CharField(max_length=255, unique=True)
	users = models.ManyToManyField(User, related_name='subscriptions', blank=True)

	def __str__(self):
		return self.name
