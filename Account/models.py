from django.db import models


# Model to store subscription names

from django.contrib.auth.models import User

# Model to store subscription names
class Subscription(models.Model):
	name = models.CharField(max_length=255, unique=True)
	users = models.ManyToManyField(User, related_name='subscriptions', blank=True)

	def __str__(self):
		return self.name


# Model to store detailed subscription fields from Plaid recurring transactions
class SubscriptionDetail(models.Model):
	subscription = models.OneToOneField(Subscription, on_delete=models.CASCADE, related_name='detail')
	description = models.CharField(max_length=512, blank=True, null=True)
	first_date = models.DateField(blank=True, null=True)
	last_date = models.DateField(blank=True, null=True)
	frequency = models.CharField(max_length=128, blank=True, null=True)
	average_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
	last_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
	is_active = models.BooleanField(default=True)
	predicted_next_date = models.DateField(blank=True, null=True)
	last_user_modified_time = models.DateTimeField(blank=True, null=True)
	status = models.CharField(max_length=128, blank=True, null=True)
	website_url = models.URLField(max_length=512, blank=True, null=True)

	def __str__(self):
		return f"Details for {self.subscription.name}"
