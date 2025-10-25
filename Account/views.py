# Return only subscriptions for the logged-in user
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer, ChangePasswordSerializer
from .subscription_serializers import SubscriptionSerializer
from .models import Subscription, SubscriptionDetail
import time
from rest_framework.permissions import IsAuthenticated


class UserSubscriptionListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        subscriptions = user.subscriptions.all()
        from .subscription_serializers import SubscriptionSerializer
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteSubscriptionView(APIView):
    def delete(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        subscription.delete()
        return Response({'detail': 'Subscription deleted.'}, status=status.HTTP_200_OK)

# List all subscriptions
class SubscriptionListView(generics.ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]

# Endpoint for user to join a subscription
class JoinSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        subscription.users.add(request.user)
        subscription.save()
        return Response({'detail': 'Successfully joined subscription.'}, status=status.HTTP_200_OK)


# Create your views here.
# The RegisterView class is a subclass of APIView. It has a post method that takes in a request
# object. It then tries to serialize the data in the request object. If the serialization is
# successful, it saves the data and returns a response with a message. If the serialization is not
# successful, it returns a response with an error message

class RegisterView(APIView):

    def post(self, request):
        try:
            data =request.data

            serializer = RegisterSerializer(data= data)

            if not serializer.is_valid():
                return Response({
                   'data' : serializer.errors,
                   'message' : 'something went wrong'
                }, status= status.HTTP_400_BAD_REQUEST)

            serializer.save()

            return Response({
                'data' : {},
                'message': 'Your Account is created'
            }, status= status.HTTP_201_CREATED)   

        except Exception as e:
            return Response({
                   'data' : {},
                   'message' : 'something went wrong'
                }, status= status.HTTP_400_BAD_REQUEST)

# It takes in a request, validates the request, and returns a response

class LoginView(APIView):

    def post(self, request):
        try:
            
            data = request.data
            serializer = LoginSerializer(data = data)

            if not serializer.is_valid():
                return Response({
                    'data': serializer.errors,
                    'message': "something went wrong"
                }, status= status.HTTP_400_BAD_REQUEST)
                
            response= serializer.get_jwt_token(serializer.data) 
            
            return Response(response, status= status.HTTP_200_OK)   

            
        except Exception as e:
            print(e)
            return Response({
                   'data' : {},
                   'message' : 'something went wrong bb'
                }, status= status.HTTP_400_BAD_REQUEST)     
            
            
# View to receive a list of items and store them in the database
from rest_framework.permissions import AllowAny
from .models import Subscription
# Authenticated view to get subscription details
class SubscriptionDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


        # Try to get SubscriptionDetail
        try:
            detail = subscription.detail
        except SubscriptionDetail.DoesNotExist:
            return Response({'detail': 'No details found for this subscription.'}, status=status.HTTP_404_NOT_FOUND)

        from .subscription_serializers import SubscriptionDetailSerializer
        serializer = SubscriptionDetailSerializer(detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReceiveListItemsView(APIView):
    
    
    def post(self, request):
        print('DEBUG: /receive-list/ endpoint was called!')
        import logging
        logger = logging.getLogger(__name__)
        logger.info('Incoming POST data: %s', request.data)
        print('DEBUG: Incoming POST data:', request.data)
        items = request.data.get('items', None)
        if items is None or not isinstance(items, list):
            return Response({
                'message': 'Invalid data. Expected a list of items under the key "items".',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        saved = []
        for item in items:
            # item can be a dict with all fields or just a string (backward compatible)
            if isinstance(item, dict):
                name = item.get('merchant_name') or item.get('name')
                if name and name.strip():
                    subscription, created = Subscription.objects.get_or_create(name=name.strip())
                    # Link subscription to user
                    if request.user.is_authenticated:
                        subscription.users.add(request.user)
                        subscription.save()
                    # Google Custom Search API website lookup
                    def get_website_url_from_google(merchant_name):
                        GOOGLE_API_KEY = 'AIzaSyCy3ICt7bHta6kYrd9KOc8UAiMSDc1k4Zo'
                        CSE_ID = '97d2ed807210143f9'
                        url = 'https://www.googleapis.com/customsearch/v1'
                        params = {
                            'q': merchant_name,
                            'key': GOOGLE_API_KEY,
                            'cx': CSE_ID,
                            'num': 1
                        }
                        try:
                            resp = requests.get(url, params=params, timeout=5)
                            if resp.status_code == 200:
                                data = resp.json()
                                if 'items' in data and data['items']:
                                    return data['items'][0]['link']
                        except Exception as e:
                            print(f"[Google Custom Search] Exception: {e}")
                        return None

                    website_url = get_website_url_from_google(name)
                    # Save or update SubscriptionDetail
                    detail_data = {
                        'description': item.get('description'),
                        'first_date': item.get('first_date'),
                        'last_date': item.get('last_date'),
                        'frequency': item.get('frequency'),
                        'average_amount': item.get('average_amount'),
                        'last_amount': item.get('last_amount'),
                        'is_active': item.get('is_active', True),
                        'predicted_next_date': item.get('predicted_next_date'),
                        'last_user_modified_time': item.get('last_user_modified_time'),
                        'status': item.get('status'),
                        'website_url': website_url
                    }
                    SubscriptionDetail.objects.update_or_create(
                        subscription=subscription,
                        defaults=detail_data
                    )
                    saved.append({
                        'id': subscription.id,
                        'name': subscription.name,
                        **detail_data
                    })
            elif isinstance(item, str) and item.strip():
                subscription, created = Subscription.objects.get_or_create(name=item.strip())
                # Link subscription to user
                if request.user.is_authenticated:
                    subscription.users.add(request.user)
                    subscription.save()
                # Always ensure a SubscriptionDetail exists
                SubscriptionDetail.objects.get_or_create(subscription=subscription)
                saved.append({
                    'id': subscription.id,
                    'name': subscription.name
                })

        return Response({
            'message': 'List received and stored successfully.',
            'data': {'saved_items': saved}
        }, status=status.HTTP_200_OK)

class ChangePasswordView(generics.UpdateAPIView):
        """
        An endpoint for changing password.
        """
        
        serializer_class = ChangePasswordSerializer
        #model = User
        #permission_classes = (IsAuthenticated,)
        permission_classes = [IsAuthenticated]
        authentication_classes =[JWTAuthentication]

        def get_object(self, queryset=None):
            obj = self.request.user
            return obj

        def update(self, request, *args, **kwargs):
            self.object = self.get_object()
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                # Check old password
                if not self.object.check_password(serializer.data.get("old_password")):
                    return Response({"old_password": ["You have entered Wrong Old Password."]}, status=status.HTTP_400_BAD_REQUEST)
                # set_password also hashes the password that the user will get
                self.object.set_password(serializer.data.get("new_password"))
                self.object.save()
                response = {
                    'status': 'success',
                    'code': status.HTTP_200_OK,
                    'message': 'Password updated successfully',
                    'data': []
                }

                return Response(response)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            
             