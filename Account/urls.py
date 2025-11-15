from django.urls import path

from Account.views import RegisterView, LoginView, ChangePasswordView, ReceiveListItemsView, SubscriptionDetailView, JoinSubscriptionView, SubscriptionListView,  DeleteSubscriptionView, UserSubscriptionListView
from Account.subscription_averages_view import SubscriptionAveragesView
    
from . import plaid_views

urlpatterns = [
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('my_subscriptions/', UserSubscriptionListView.as_view(), name='user-subscription-list'),
    # In Account/urls.py
    path('subscriptions/', UserSubscriptionListView.as_view(), name='user-subscriptions-list'),
    path('subscription-averages/', SubscriptionAveragesView.as_view(), name='subscription-averages'),
    path('register/', RegisterView.as_view() , name='register'),
    path('login/', LoginView.as_view() , name='login'),
    path('update-password/', ChangePasswordView.as_view() , name='update-password'),
    path('receive-list/', ReceiveListItemsView.as_view(), name='receive-list'),
    path('subscription/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscription/<int:pk>/join/', JoinSubscriptionView.as_view(), name='subscription-join'),
    path('subscription/<int:pk>/delete/', DeleteSubscriptionView.as_view(), name='subscription-delete'),
    path('create_link_token/', plaid_views.create_link_token, name='create_link_token'),
    path('exchange_public_token/', plaid_views.exchange_public_token, name='exchange_public_token'),
    path('get_account_balances/', plaid_views.get_account_balances, name='get_account_balances'),
    path('get_transactions/', plaid_views.get_transactions, name='get_transactions'),
    path('get_recurring_transactions/', plaid_views.get_recurring_transactions, name='get_recurring_transactions'),
    path('recommend_subscriptions_to_keep/', __import__('Account.views').views.recommend_subscriptions_to_keep, name='recommend_subscriptions_to_keep')
]



