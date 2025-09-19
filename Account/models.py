from django.db import models


# Model to store subscription names
class Subscription(models.Model):
	name = models.CharField(max_length=255, unique=True)

	def __str__(self):
		return self.name
