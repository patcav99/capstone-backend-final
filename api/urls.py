from django.urls import path, include

urlpatterns = [
    path('account/', include('Account.urls')),
    path('blog/', include('blogapp.urls')),
]



