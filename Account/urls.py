from django.urls import path

from Account.views import RegisterView, LoginView, ChangePasswordView, ReceiveListItemsView, SubscriptionDetailView, JoinSubscriptionView, SubscriptionListView, get_subscription_login_url, SubscriptionSeleniumLoginView, DeleteSubscriptionView


urlpatterns = [
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('register/', RegisterView.as_view() , name='register'),
    path('login/', LoginView.as_view() , name='login'),
    path('update-password/', ChangePasswordView.as_view() , name='update-password'),
    path('receive-list/', ReceiveListItemsView.as_view(), name='receive-list'),
    path('subscription/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('subscription/<int:pk>/join/', JoinSubscriptionView.as_view(), name='subscription-join'),
    path('subscription-login-url/', get_subscription_login_url, name='subscription-login-url'),
    path('subscription-selenium-login/', SubscriptionSeleniumLoginView.as_view(), name='subscription-selenium-login'),
    path('subscription/<int:pk>/delete/', DeleteSubscriptionView.as_view(), name='subscription-delete'),
]



