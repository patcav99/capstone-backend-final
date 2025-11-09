import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from Account.models import Subscription, SubscriptionDetail

class PastSubscriptionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        # Create active subscription
        sub_active = Subscription.objects.create(name='ActiveSub')
        sub_active.users.add(self.user)
        SubscriptionDetail.objects.create(
            subscription=sub_active,
            first_date='2023-01-01',
            last_date=(datetime.date.today() - datetime.timedelta(days=10)).isoformat(),
            is_active=True
        )
        # Create inactive subscription (last_date > 31 days ago)
        sub_inactive = Subscription.objects.create(name='InactiveSub')
        sub_inactive.users.add(self.user)
        SubscriptionDetail.objects.create(
            subscription=sub_inactive,
            first_date='2023-01-01',
            last_date=(datetime.date.today() - datetime.timedelta(days=40)).isoformat(),
            is_active=False
        )

    def test_past_subscriptions_list(self):
        # Simulate fetching subscriptions for the user
        self.client.force_login(self.user)
        response = self.client.get(reverse('user-subscriptions-list'))
        self.assertEqual(response.status_code, 200)
        subs = response.json()
        # Filter inactive subs
        past_subs = [sub for sub in subs if sub.get('is_active') is False]
        self.assertTrue(len(past_subs) > 0, 'Past subscriptions list should be populated')
        # Check last_date for each past subscription
        for sub in past_subs:
            detail = SubscriptionDetail.objects.filter(subscription_id=sub['id']).first()
            self.assertIsNotNone(detail)
            last_date = detail.last_date
            last_date_obj = datetime.datetime.strptime(str(last_date), '%Y-%m-%d').date()
            days_ago = (datetime.date.today() - last_date_obj).days
            self.assertTrue(days_ago > 31, f"Subscription {sub['name']} last_date should be > 31 days ago")
