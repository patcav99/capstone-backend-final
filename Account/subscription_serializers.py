from rest_framework import serializers
from .models import Subscription, SubscriptionDetail

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'name']


# Serializer for SubscriptionDetail
class SubscriptionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionDetail
        fields = [
            'id', 'subscription', 'description', 'first_date', 'last_date', 'frequency',
            'average_amount', 'last_amount', 'is_active', 'predicted_next_date',
            'last_user_modified_time', 'status'
        ]
