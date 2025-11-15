from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import requests
from plaid.model.transactions_recurring_get_request import TransactionsRecurringGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
import datetime
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid import Configuration, ApiClient
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest

configuration = Configuration(
    host=os.environ.get("PLAID_ENV_URL", "https://sandbox.plaid.com"),
    api_key={
        "clientId": os.environ["PLAID_CLIENT_ID"],
        "secret": os.environ["PLAID_SECRET"],
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)
# Endpoint to fetch recurring transactions for a given access_token (for testing)
@csrf_exempt
def get_recurring_transactions(request):
    print("DEBUG: get_recurring_transactions called")
    # Toggle mock via query param (?mock=1) or POST field (mock: true)
    use_mock = False
    # Always check query param first for mock toggle
    data = {}
    if request.GET.get('mock') == '1':
        use_mock = True
        data = json.loads(request.body)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        print("DEBUG: POST data received:", data)
        use_mock = data.get('mock') in [True, '1', 1]
    if use_mock:
        print("DEBUG: Entered mock branch, data:", data)
        from .models import Subscription, SubscriptionDetail
        from django.contrib.auth.models import User
        from .subscription_serializers import SubscriptionSerializer
        # Always use username from POST data if provided
        username = data.get('username')
        print("DEBUG: Username received in mock branch:", username)
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None
        print("DEBUG: Mock user:", user)
        if not user:
            # Fallback to request.user if available
            user = getattr(request, 'user', None)
        mock_streams = [
            {
                "id": 11,
                "name": "StubHub",
                "merchant_name": "StubHub",
                "description": "Delivery subscription",
                "first_date": "2023-01-01",
                "last_date": "2025-11-02",
                "frequency": "monthly",
                "average_amount": {"amount": 12.99},
                "last_amount": {"amount": 12.99},
                "is_active": True,
                "predicted_next_date": "2025-11-01",
                "last_user_modified_datetime": "2023-10-01T12:00:00Z",
                "status": "active"
            },
            {
                "id": 12,
                "name": "WMMR",
                "merchant_name": "WMMR",
                "description": "Streaming subscription",
                "first_date": "2023-02-15",
                "last_date": "2023-10-20",
                "frequency": "monthly",
                "average_amount": {"amount": 10.99},
                "last_amount": {"amount": 10.99},
                "is_active": True,
                "predicted_next_date": "2025-11-15",
                "last_user_modified_datetime": "2023-10-15T12:00:00Z",
                "status": "active"
            },
            {
                "id": 13,
                "name": "WWE Network",
                "merchant_name": "WWE Network",
                "description": "Streaming service",
                "first_date": "2023-03-01",
                "last_date": "2025-10-15",
                "frequency": "monthly",
                "average_amount": {"amount": 21.00},
                "last_amount": {"amount": 21.00},
                "is_active": False,
                "predicted_next_date": "2025-11-20",
                "last_user_modified_datetime": "2023-10-01T12:00:00Z",
                "status": "active"
            }
        ]
        # Update or create in DB
        for stream in mock_streams:
            sub, _ = Subscription.objects.get_or_create(name=stream["merchant_name"])
            # Link subscription to user
            print("DEBUG: Linking subscription to user:", user)
            if user and getattr(user, 'id', None):
                sub.users.add(user)
                sub.save()
            detail, _ = SubscriptionDetail.objects.get_or_create(subscription=sub)
            detail.description = stream["description"]
            detail.first_date = stream["first_date"]
            detail.last_date = stream["last_date"]
            detail.frequency = stream["frequency"]
            detail.average_amount = stream["average_amount"]["amount"]
            detail.last_amount = stream["last_amount"]["amount"]
            # Mark inactive if last_date > 1 month ago
            last_date_obj = None
            try:
                last_date_obj = datetime.datetime.strptime(stream["last_date"], "%Y-%m-%d").date()
            except Exception as e:
                print(f"DEBUG: Could not parse last_date for {stream['merchant_name']}: {e}")
            is_active = stream["is_active"]
            if last_date_obj:
                days_since_last = (datetime.date.today() - last_date_obj).days
                if days_since_last > 31:
                    is_active = False
                else:
                    is_active = True
            detail.is_active = is_active
            detail.predicted_next_date = stream["predicted_next_date"]
            detail.last_user_modified_time = stream["last_user_modified_datetime"]
            detail.status = stream["status"]
            # Attach transaction_ids if present in mock
            if "transaction_ids" in stream:
                detail.transaction_ids = stream["transaction_ids"]
            detail.save()
        # Fetch and return all subscriptions for the user from the DB
        if user and getattr(user, 'id', None):
            subs = user.subscriptions.all()
            serializer = SubscriptionSerializer(subs, many=True)
            return JsonResponse({"subscriptions": serializer.data})
        else:
            return JsonResponse({"subscriptions": []})
    # Otherwise, fetch from Plaid
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    access_token = data.get('access_token')
    if not access_token:
        return JsonResponse({'error': 'access_token required'}, status=400)
    req = TransactionsRecurringGetRequest(access_token=access_token)
    response = client.transactions_recurring_get(req)
    plaid_data = response.to_dict()
    # Update or create in DB for Plaid data
    from .models import Subscription, SubscriptionDetail
    from django.contrib.auth.models import User
    # Always use username from POST data if provided
    user = None
    username = data.get('username')
    if username:
        try:
            user = User.objects.get(username=username)
            print(f"DEBUG: Found user by username '{username}': id={user.id}")
        except User.DoesNotExist:
            print(f"DEBUG: No user found for username '{username}'")
            user = None
    if not user:
        # Fallback to request.user if available
        user = getattr(request, 'user', None)
        print(f"DEBUG: Fallback to request.user: {user} (id={getattr(user, 'id', None)})")
    streams = plaid_data.get("outflow_streams", [])
    for stream in streams:
        merchant = stream.get("merchant_name")
        if not merchant:
            continue
        sub, _ = Subscription.objects.get_or_create(name=merchant)
        # Always link subscription to user
        print(f"DEBUG: Attempting to link subscription '{merchant}' to user: {user} (id={getattr(user, 'id', None)})")
        if user and getattr(user, 'id', None):
            sub.users.add(user)
            sub.save()
            print(f"DEBUG: Linked subscription '{merchant}' to user id {user.id}")
        else:
            print(f"DEBUG: No valid user found for subscription '{merchant}'")
        detail, _ = SubscriptionDetail.objects.get_or_create(subscription=sub)
        detail.description = stream.get("description")
        detail.first_date = stream.get("first_date")
        detail.last_date = stream.get("last_date")
        detail.frequency = stream.get("frequency")
        avg_amt = stream.get("average_amount")
        if isinstance(avg_amt, dict):
            detail.average_amount = avg_amt.get("amount")
        else:
            detail.average_amount = avg_amt
        last_amt = stream.get("last_amount")
        if isinstance(last_amt, dict):
            detail.last_amount = last_amt.get("amount")
        else:
            detail.last_amount = last_amt
        # Mark inactive if last_date > 1 month ago
        last_date_obj = None
        try:
            last_date_val = stream.get("last_date")
            if last_date_val:
                last_date_obj = datetime.datetime.strptime(last_date_val, "%Y-%m-%d").date()
        except Exception as e:
            print(f"DEBUG: Could not parse last_date for {merchant}: {e}")
        is_active = stream.get("is_active", True)
        if last_date_obj:
            days_since_last = (datetime.date.today() - last_date_obj).days
            if days_since_last > 31:
                is_active = False
        detail.is_active = is_active
        detail.predicted_next_date = stream.get("predicted_next_date")
        detail.last_user_modified_time = stream.get("last_user_modified_datetime")
        detail.status = stream.get("status")
        # Attach transaction_ids if present in Plaid stream
        if "transaction_ids" in stream:
            detail.transaction_ids = stream["transaction_ids"]
        # Always set merchant_name for Plaid subscriptions
        detail.merchant_name = stream.get("merchant_name") or stream.get("name")
        detail.save()
    return JsonResponse(plaid_data)

# Endpoint to fetch transactions for a given access_token (for testing)
@csrf_exempt
def get_transactions(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    access_token = data.get('access_token')
    transaction_ids = data.get('transaction_ids')  # Expecting a list of IDs
    print(f"DEBUG: get_transactions received access_token: {access_token}")
    print(f"DEBUG: get_transactions received transaction_ids: {transaction_ids}")
    if not access_token:
        return JsonResponse({'error': 'access_token required'}, status=400)
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    end_date = datetime.date.today()
    req = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(count=100)
    )
    response = client.transactions_get(req)
    transactions = response.to_dict().get('transactions', [])
    if transaction_ids:
        # Filter transactions by transaction_id
        transactions = [tx for tx in transactions if tx['transaction_id'] in transaction_ids]
    return JsonResponse({'transactions': transactions})

# Endpoint to fetch account balances for a given access_token (for testing)
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def get_account_balances(request):
    import json
    if request.method == 'POST':
        data = json.loads(request.body)
        access_token = data.get('access_token')
        if not access_token:
            return JsonResponse({'error': 'access_token required'}, status=400)
        req = AccountsBalanceGetRequest(access_token=access_token)
        response = client.accounts_balance_get(req)
        return JsonResponse(response.to_dict())
    return JsonResponse({'error': 'POST required'}, status=405)

@csrf_exempt
def create_link_token(request):
    user_id = str(getattr(request.user, 'id', 'anonymous'))
    req = LinkTokenCreateRequest(
        user={"client_user_id": user_id},
        client_name="Your App Name",
        products=[Products("auth"), Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en"
    )
    response = client.link_token_create(req)
    return JsonResponse(response.to_dict())

@csrf_exempt
def exchange_public_token(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    public_token = data.get("public_token")
    if not public_token:
        return JsonResponse({'error': 'public_token required'}, status=400)
    req = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(req)
    access_token = response.to_dict().get("access_token")
    # Save access_token securely in your DB, associated with the user
    return JsonResponse({"access_token": access_token})