from rest_framework import serializers
from .models import Subscription, SubscriptionDetail

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'name']


# Serializer for SubscriptionDetail
class SubscriptionDetailSerializer(serializers.ModelSerializer):
    transaction_ids = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionDetail
        fields = [
            'id', 'subscription', 'description', 'first_date', 'last_date', 'frequency',
            'average_amount', 'last_amount', 'is_active', 'predicted_next_date',
            'last_user_modified_time', 'status', 'website_url', 'transaction_ids'
        ]

    def get_transaction_ids(self, obj):
        # Try to get transaction_ids from Plaid recurring stream if available
        # Assume you store them in a custom field or fetch from Plaid
        # For now, try to get from a custom attribute or fallback to None
        if hasattr(obj, 'transaction_ids') and obj.transaction_ids:
            return obj.transaction_ids
        # If not stored, try to fetch from Plaid (pseudo-code, replace with actual logic)
        # Example: return obj.plaid_stream_transaction_ids if hasattr(obj, 'plaid_stream_transaction_ids') else []
        return []
