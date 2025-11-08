from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Subscription, SubscriptionDetail
from rest_framework.permissions import AllowAny

class SubscriptionAveragesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Get all subscriptions and their average_amount (if any)
        data = []
        for sub in Subscription.objects.all():
            avg = None
            predicted_next_date = None
            try:
                avg = sub.detail.average_amount
                predicted_next_date = sub.detail.predicted_next_date
                # Only return predicted_next_date if it is today or in the future
                from datetime import date
                if predicted_next_date:
                    if isinstance(predicted_next_date, str):
                        try:
                            predicted_next_date_obj = date.fromisoformat(predicted_next_date)
                        except Exception:
                            predicted_next_date_obj = None
                    else:
                            predicted_next_date_obj = predicted_next_date
                if predicted_next_date_obj and predicted_next_date_obj < date.today():
                            predicted_next_date = None
            except SubscriptionDetail.DoesNotExist:
                avg = None
                predicted_next_date = None
            data.append({
                'id': sub.id,
                'name': sub.name,
                'average_amount': float(avg) if avg is not None else None,
                'predicted_next_date': str(predicted_next_date) if predicted_next_date else None,
                'is_active': sub.detail.is_active if hasattr(sub, 'detail') else None
            })
        return Response({'subscriptions': data}, status=status.HTTP_200_OK)
