from rest_framework import serializers
from .models import Subscription, SubscriptionDetail

class SubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'name', 'is_active']

    def get_is_active(self, obj):
        # Get is_active from related SubscriptionDetail
        detail = SubscriptionDetail.objects.filter(subscription=obj).first()
        return detail.is_active if detail else None


# Serializer for SubscriptionDetail
class SubscriptionDetailSerializer(serializers.ModelSerializer):
    transaction_ids = serializers.SerializerMethodField()
    merchant_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = SubscriptionDetail
        fields = [
            'id', 'subscription', 'description', 'first_date', 'last_date', 'frequency',
            'average_amount', 'last_amount', 'is_active', 'predicted_next_date',
            'last_user_modified_time', 'status', 'website_url', 'transaction_ids', 'merchant_name'
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
