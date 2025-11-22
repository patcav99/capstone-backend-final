# REST framework imports first
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
# Django imports
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
# Password reset request endpoint
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email required'}, status=400)
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists
        return Response({'message': 'If your email is registered, you will receive a password reset link.'})
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    # Use frontend URL for password reset link
    frontend_url = 'http://patcav.shop/password-reset-confirm'
    reset_url = f'{frontend_url}?uid={uid}&token={token}'
    subject = 'RateMate Password Reset'
    message = f'Click the link to reset your password: {reset_url}'
    print(f"DEBUG: Sending password reset email to {email} with subject '{subject}' and message '{message}'")
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    return Response({'message': 'If your email is registered, you will receive a password reset link.'})

# Password reset confirm endpoint
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    if not (uid and token and new_password):
        return Response({'error': 'Missing parameters'}, status=400)
    User = get_user_model()
    try:
        uid_int = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid_int)
    except Exception:
        return Response({'error': 'Invalid user'}, status=400)
    if not default_token_generator.check_token(user, token):
        return Response({'error': 'Invalid or expired token'}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password has been reset successfully.'})
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
from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes


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
            data = request.data
            serializer = RegisterSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    'data': serializer.errors,
                    'message': 'something went wrong'
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            # Generate JWT token for the new user
            from django.contrib.auth import authenticate
            from rest_framework_simplejwt.tokens import RefreshToken
            user = authenticate(username=data['username'].lower(), password=data['password'])
            if user:
                refresh = RefreshToken.for_user(user)
                token_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
            else:
                token_data = None
            return Response({
                'data': {'token': token_data},
                'message': 'Your Account is created'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'data': {},
                'message': 'something went wrong'
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # Google Custom Search API to find cancellation page
        def get_cancel_page_url(subscription_name):
            GOOGLE_API_KEY = 'AIzaSyCy3ICt7bHta6kYrd9KOc8UAiMSDc1k4Zo'
            CSE_ID = '97d2ed807210143f9'
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'q': f"{subscription_name} cancel subscription",
                'key': GOOGLE_API_KEY,
                'cx': CSE_ID,
                'num': 1
            }
            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"[Google Custom Search] Cancel API response for {subscription_name}: {data}")
                    if 'items' in data and data['items']:
                        return data['items'][0]['link']
                else:
                    print(f"[Google Custom Search] Cancel API FAILED for {subscription_name}: status={resp.status_code}, text={resp.text}")
            except Exception as e:
                print(f"[Google Custom Search] Exception: {e}")
            return None

        def get_reactivate_page_url(subscription_name):
            GOOGLE_API_KEY = 'AIzaSyCy3ICt7bHta6kYrd9KOc8UAiMSDc1k4Zo'
            CSE_ID = '97d2ed807210143f9'
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'q': f"{subscription_name} how to reactivate subscription",
                'key': GOOGLE_API_KEY,
                'cx': CSE_ID,
                'num': 1
            }
            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"[Google Custom Search] Reactivate API response for {subscription_name}: {data}")
                    if 'items' in data and data['items']:
                        return data['items'][0]['link']
                else:
                    print(f"[Google Custom Search] Reactivate API FAILED for {subscription_name}: status={resp.status_code}, text={resp.text}")
            except Exception as e:
                print(f"[Google Custom Search] Exception: {e}")
            return None

        cancel_url = get_cancel_page_url(subscription.name)
        print(f"DEBUG: Cancel URL for {subscription.name}: {cancel_url}")
        reactivate_url = get_reactivate_page_url(subscription.name)
        print(f"DEBUG: Reactivate URL for {subscription.name}: {reactivate_url}")

        from .subscription_serializers import SubscriptionDetailSerializer
        serializer = SubscriptionDetailSerializer(detail)
        response_data = serializer.data
        response_data['cancel_url'] = cancel_url
        response_data['reactivate_url'] = reactivate_url
        return Response(response_data, status=status.HTTP_200_OK)

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
                            'website_url': website_url,
                            'merchant_name': item.get('merchant_name') or item.get('name')
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

# Backtracking algorithm to select subscriptions to keep under budget
def select_subscriptions_under_budget(subscriptions, budget):
    # subscriptions: list of dicts with 'id', 'name', 'average_amount', 'is_active'
    # budget: Decimal
    n = len(subscriptions)
    best = {'total': Decimal('0'), 'keep': []}

    def backtrack(i, current_total, current_keep):
        if current_total > budget:
            return
        if i == n:
            if current_total > best['total']:
                best['total'] = current_total
                best['keep'] = current_keep[:]
            return
        # Option 1: keep this subscription
        amt = subscriptions[i]['average_amount'] or Decimal('0')
        backtrack(i+1, current_total+amt, current_keep+[subscriptions[i]['id']])
        # Option 2: skip this subscription
        backtrack(i+1, current_total, current_keep)

    backtrack(0, Decimal('0'), [])
    return best['keep']

# Backtracking algorithm to select subscriptions to keep under budget, prioritizing by user ranking
# subscriptions: list of dicts with 'id', 'name', 'average_amount', 'is_active', 'rank'
def select_subscriptions_under_budget_ranked(subscriptions, budget):
    # Sort subscriptions by rank (lower rank = higher priority)
    subscriptions_sorted = sorted(subscriptions, key=lambda x: x['rank'])
    n = len(subscriptions_sorted)
    best = {'total': Decimal('0'), 'keep': [], 'ranksum': float('inf')}
    all_solutions = []

    def backtrack(i, current_total, current_keep, current_ranksum):
        if current_total > budget:
            return
        if i == n:
            # Prefer solutions with the most subscriptions, then lowest ranksum, then highest total
            score = (len(current_keep), -current_ranksum, current_total)
            best_score = (len(best['keep']), -best['ranksum'], best['total'])
            if score > best_score:
                best['total'] = current_total
                best['keep'] = current_keep[:]
                best['ranksum'] = current_ranksum
                all_solutions.clear()
                all_solutions.append({'keep': current_keep[:], 'total': current_total, 'ranksum': current_ranksum})
            elif score == best_score:
                # Only add unique solutions
                if not any(set(sol['keep']) == set(current_keep) for sol in all_solutions):
                    all_solutions.append({'keep': current_keep[:], 'total': current_total, 'ranksum': current_ranksum})
            return
        # Option 1: keep this subscription
        amt = subscriptions_sorted[i]['average_amount'] or Decimal('0')
        rank = subscriptions_sorted[i]['rank']
        backtrack(i+1, current_total+amt, current_keep+[subscriptions_sorted[i]['id']], current_ranksum+rank)
        # Option 2: skip this subscription
        backtrack(i+1, current_total, current_keep, current_ranksum)

    backtrack(0, Decimal('0'), [], 0)
    return all_solutions if all_solutions else [{'keep': best['keep'], 'total': best['total'], 'ranksum': best['ranksum']}]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_subscriptions_to_keep(request):
    """
    Receives: { "budget": 100.00, "access_token": "...", "ranks": [id1, id2, ...] }
    Returns: { "keep": [ids], "cancel": [ids], "total": sum, "other_transactions": sum, "all_spending": sum }
    Considers active subscriptions and all other transactions for the user in the last month. Prioritizes by user ranking.
    """
    user = request.user
    budget = request.data.get('budget')
    access_token = request.data.get('access_token')
    ranks = request.data.get('ranks', [])  # Array of subscription IDs in priority order
    try:
        budget = Decimal(str(budget))
    except Exception:
        return Response({'error': 'Invalid budget'}, status=400)
    subs = user.subscriptions.all()
    sub_details = SubscriptionDetail.objects.filter(subscription__in=subs, is_active=True)
    subscriptions = []
    # Assign rank based on position in ranks array (lower index = higher priority)
    id_to_rank = {int(sub_id): idx for idx, sub_id in enumerate(ranks)}
    for detail in sub_details:
        amt = detail.average_amount if detail.average_amount else Decimal('0')
        sub_id = detail.subscription.id
        rank = id_to_rank.get(sub_id, len(ranks))  # Unranked go last
        subscriptions.append({
            'id': sub_id,
            'name': detail.subscription.name,
            'average_amount': amt,
            'is_active': detail.is_active,
            'rank': rank
        })
    # Fetch all transactions for the user for the last month using Plaid
    other_transactions_total = Decimal('0')
    if access_token:
        import datetime
        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
        from plaid.api import plaid_api
        from plaid import Configuration, ApiClient
        import os
        configuration = Configuration(
            host=os.environ.get("PLAID_ENV_URL", "https://sandbox.plaid.com"),
            api_key={
                "clientId": os.environ["PLAID_CLIENT_ID"],
                "secret": os.environ["PLAID_SECRET"],
            }
        )
        api_client = ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        end_date = datetime.date.today()
        req = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(count=100)
        )
        try:
            response = client.transactions_get(req)
            transactions = response.to_dict().get('transactions', [])
            sub_merchants = set([s['name'] for s in subscriptions])
            for tx in transactions:
                merchant = tx.get('merchant_name') or tx.get('name')
                amount = abs(Decimal(str(tx.get('amount', 0))))
                if merchant not in sub_merchants:
                    other_transactions_total += amount
        except Exception as e:
            print(f"DEBUG: Error fetching transactions for budget: {e}")
    solutions = select_subscriptions_under_budget_ranked(subscriptions, budget - other_transactions_total)
    response_list = []
    for sol in solutions:
        keep_ids = sol['keep']
        cancel_ids = [s['id'] for s in subscriptions if s['id'] not in keep_ids]
        total_subs = sum([s['average_amount'] for s in subscriptions if s['id'] in keep_ids])
        all_spending = total_subs + other_transactions_total
        response_list.append({
            'keep': keep_ids,
            'cancel': cancel_ids,
            'total_subscriptions': str(total_subs),
            'other_transactions': str(other_transactions_total),
            'all_spending': str(all_spending)
        })
    from rest_framework.response import Response
    # Return a list of solutions if more than one, else a single dict for compatibility
    if len(response_list) == 1:
        return Response(response_list[0])
    return Response(response_list)
