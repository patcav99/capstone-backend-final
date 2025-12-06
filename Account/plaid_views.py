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

import os

# Determine Plaid environment
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")
if PLAID_ENV == "production":
    PLAID_ENV_URL = "https://production.plaid.com"
    PLAID_SECRET = os.environ.get("PLAID_PROD_SECRET")
else:
    PLAID_ENV_URL = "https://sandbox.plaid.com"
    PLAID_SECRET = os.environ.get("PLAID_SANDBOX_SECRET")

configuration = Configuration(
    host=PLAID_ENV_URL,
    api_key={
        "clientId": os.environ["PLAID_CLIENT_ID"],
        "secret": PLAID_SECRET,
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
                print(f"DEBUG: No user found for username '{username}'")
                user = None
        if not user:
            # Fallback to request.user if available
            user = getattr(request, 'user', None)
            print(f"DEBUG: Fallback to request.user: {user} (id={getattr(user, 'id', None)})")
        if not user or not getattr(user, 'id', None):
            print("ERROR: No valid user found for linking subscriptions. Aborting subscription linking.")
            return JsonResponse({'error': 'No valid user found for linking subscriptions.'}, status=400)
        mock_streams = [
            {
                "id": 20,
                "name": "Target",
                "merchant_name": "Target",
                "description": "Delivery subscription",
                "first_date": "2023-01-01",
                "last_date": "2025-11-02",
                "frequency": "monthly",
                "average_amount": {"amount": 23.99},
                "last_amount": {"amount": 23.99},
                "is_active": True,
                "predicted_next_date": "2025-11-01",
                "last_user_modified_datetime": "2023-10-01T12:00:00Z",
                "status": "active"
            },
            {
                "id": 15,
                "name": "Hulu",
                "merchant_name": "Hulu",
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
                "id": 17,
                "name": "Netflix",
                "merchant_name": "Netflix",
                "description": "Streaming service",
                "first_date": "2023-03-01",
                "last_date": "2025-11-15",
                "frequency": "monthly",
                "average_amount": {"amount": 27.00},
                "last_amount": {"amount": 27.00},
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
            detail.description = stream.get("description")
            detail.first_date = stream.get("first_date")
            detail.last_date = stream.get("last_date")
            detail.frequency = stream.get("frequency")
            detail.average_amount = stream.get("average_amount", {}).get("amount")
            detail.last_amount = stream.get("last_amount", {}).get("amount")
            detail.predicted_next_date = stream.get("predicted_next_date")
            # last_user_modified_time: handle both possible keys
            detail.last_user_modified_time = stream.get("last_user_modified_time") or stream.get("last_user_modified_datetime")
            detail.status = stream.get("status")
            detail.merchant_name = stream.get("merchant_name")
            # Mark inactive if last_date > 30 days ago
            last_date_obj = None
            try:
                last_date_obj = datetime.datetime.strptime(stream["last_date"], "%Y-%m-%d").date()
            except Exception as e:
                print(f"DEBUG: Could not parse last_date for {stream['merchant_name']}: {e}")
            is_active = stream["is_active"]
            if last_date_obj:
                days_since_last = (datetime.date.today() - last_date_obj).days
                print(f"DEBUG: {stream['merchant_name']} last_date={stream['last_date']} days_since_last={days_since_last} is_active(before)={stream['is_active']} is_active(after)={'False' if days_since_last > 30 else 'True'}")
                if days_since_last > 30:
                    is_active = False
                else:
                    is_active = True
            detail.is_active = is_active
            # --- Website URL lookup using Google Custom Search for mock subscriptions ---
            def get_website_url_from_google(merchant_name):
                GOOGLE_API_KEY = 'AIzaSyAX9Xd6l0euv5doG9nXHEcqFK-2Nf4lpi0'
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
                    print(f"[Google Custom Search] (Mock) Response status: {resp.status_code}")
                    print(f"[Google Custom Search] (Mock) Response text: {resp.text}")
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'items' in data and data['items']:
                            print(f"[Google Custom Search] (Mock) Found website URL: {data['items'][0]['link']}")
                            return data['items'][0]['link']
                except Exception as e:
                    print(f"[Google Custom Search] (Mock) Exception: {e}")
                return None

            print(f"[Google Custom Search] (Mock) About to call get_website_url_from_google with merchant name: {stream['merchant_name']}")
            website_url = get_website_url_from_google(stream['merchant_name'])
            print(f"[Google Custom Search] (Mock) Final website_url to save: {website_url}")
            if website_url:
                detail.website_url = website_url
            detail.save()
    # Otherwise, fetch from Plaid
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    access_token = data.get('access_token')
    if not access_token:
        return JsonResponse({'error': 'access_token required'}, status=400)
    req = TransactionsRecurringGetRequest(access_token=access_token)
    try:
        response = client.transactions_recurring_get(req)
        plaid_data = response.to_dict()
    except Exception as e:
        print(f"PLAID ERROR: {e}")
        return JsonResponse({'error': f'Plaid internal error: {str(e)}'}, status=500)
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
            print("DEBUG: No merchant_name in stream, skipping.")
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
        # Mark inactive if last_date > 30 days ago
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
            print(f"DEBUG: {merchant} last_date={last_date_val} days_since_last={days_since_last} is_active(before)={is_active} is_active(after)={'False' if days_since_last > 30 else 'True'}")
            if days_since_last > 30:
                is_active = False
            else:
                is_active = True
        detail.is_active = is_active
        detail.predicted_next_date = stream.get("predicted_next_date")
        detail.last_user_modified_time = stream.get("last_user_modified_datetime")
        detail.status = stream.get("status")
        # Attach transaction_ids if present in Plaid stream
        if "transaction_ids" in stream:
            detail.transaction_ids = stream["transaction_ids"]
        # Always set merchant_name for Plaid subscriptions
        detail.merchant_name = stream.get("merchant_name") or stream.get("name")
        # --- Website URL lookup using Google Custom Search ---
        def get_website_url_from_google(merchant_name):
            GOOGLE_API_KEY = 'AIzaSyAX9Xd6l0euv5doG9nXHEcqFK-2Nf4lpi0'
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
                print(f"[Google Custom Search] Response status: {resp.status_code}")
                print(f"[Google Custom Search] Response text: {resp.text}")
                if resp.status_code == 200:
                    data = resp.json()
                    if 'items' in data and data['items']:
                        print(f"[Google Custom Search] Found website URL: {data['items'][0]['link']}")
                        return data['items'][0]['link']
            except Exception as e:
                print(f"[Google Custom Search] Exception: {e}")
            return None

        print(f"[Google Custom Search] About to call get_website_url_from_google with merchant name: {merchant}")
        website_url = get_website_url_from_google(merchant)
        print(f"[Google Custom Search] Final website_url to save: {website_url}")
        if website_url:
            detail.website_url = website_url
        detail.save()
    # Fetch and return all subscriptions for the user from the DB (with inactivity check)
    if user and getattr(user, 'id', None):
        from .subscription_serializers import SubscriptionSerializer
        subs = check_db_subs_inactivity(user)
        print("DEBUG: Subscriptions and their is_active status after inactivity check:")
        for sub in subs:
            print(f"  id={sub.id}, name={sub.name}, is_active={getattr(sub, 'is_active', None)}")
        serializer = SubscriptionSerializer(subs, many=True)
        return JsonResponse({"subscriptions": serializer.data})
    else:
        return JsonResponse({"subscriptions": []})

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
    # Remove date filter to fetch all available transactions
    req = TransactionsGetRequest(
        access_token=access_token,
        start_date=datetime.date(2000, 1, 1),  # Earliest possible date as date object
        end_date=datetime.date.today(),
        options=TransactionsGetRequestOptions(count=500)
    )
    response = client.transactions_get(req)
    transactions = response.to_dict().get('transactions', [])
    # Print all merchant names and IDs from Plaid before filtering
    print('DEBUG: All Plaid transactions before filtering:')
    for tx in transactions:
        print(f"  transaction_id={tx.get('transaction_id')}, merchant_name={tx.get('merchant_name')}, name={tx.get('name')}")

    # Filter by merchant name if requested
    merchant_name = data.get('merchant_name')
    if merchant_name:
        merchant_name_lower = merchant_name.lower()
        print(f"DEBUG: Filtering for merchant_name='{merchant_name}' (lower='{merchant_name_lower}')")
        filtered = []
        for tx in transactions:
            tx_merchant = tx.get('merchant_name', '')
            tx_name = tx.get('name', '')
            tx_merchant_lower = tx_merchant.lower() if tx_merchant else ''
            tx_name_lower = tx_name.lower() if tx_name else ''
            print(f"  Checking tx_id={tx.get('transaction_id')}: merchant_name='{tx_merchant}' (lower='{tx_merchant_lower}'), name='{tx_name}' (lower='{tx_name_lower}')")
            if (merchant_name_lower in tx_merchant_lower) or (merchant_name_lower in tx_name_lower):
                print(f"    MATCHED!")
                filtered.append(tx)
        transactions = filtered
    elif transaction_ids:
        transactions = [tx for tx in transactions if tx['transaction_id'] in transaction_ids]
    # Debug print merchant names of all returned transactions
    print('DEBUG: Returned transaction merchant_names:')
    for tx in transactions:
        print(f"  transaction_id={tx.get('transaction_id')}, merchant_name={tx.get('merchant_name')}, name={tx.get('name')}")
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
    try:
        response = client.link_token_create(req)
        return JsonResponse(response.to_dict())
    except Exception as e:
        print(f"PLAID ERROR (create_link_token): {e}")
        return JsonResponse({'error': f'Plaid internal error: {str(e)}'}, status=500)

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
    try:
        response = client.item_public_token_exchange(req)
        access_token = response.to_dict().get("access_token")
        # Save access_token securely in your DB, associated with the user
        return JsonResponse({"access_token": access_token})
    except Exception as e:
        print(f"PLAID ERROR (exchange_public_token): {e}")
        return JsonResponse({'error': f'Plaid internal error: {str(e)}'}, status=500)

def check_db_subs_inactivity(user):
    subs = user.subscriptions.all()
    today = datetime.date.today()
    print(f"DEBUG: Running inactivity check for user id={getattr(user, 'id', None)}, username={getattr(user, 'username', None)}")
    for sub in subs:
        detail = getattr(sub, 'detail', None)
        last_date = None
        print(f"DEBUG: Checking sub id={sub.id}, name={sub.name}")
        if detail:
            print(f"DEBUG: Found SubscriptionDetail for sub id={sub.id}")
        else:
            print(f"DEBUG: No SubscriptionDetail for sub id={sub.id}")
        if detail and hasattr(detail, 'last_date') and detail.last_date:
            print(f"DEBUG: Raw last_date value for sub id={sub.id}: {detail.last_date}")
            try:
                last_date = detail.last_date if isinstance(detail.last_date, datetime.date) else datetime.datetime.strptime(str(detail.last_date), "%Y-%m-%d").date()
            except Exception as e:
                print(f"DEBUG: Could not parse last_date for {getattr(sub, 'name', sub.id)}: {e}")
            if last_date:
                days_since_last = (today - last_date).days
                print(f"DEBUG: sub id={sub.id}, name={sub.name}, last_date={last_date}, today={today}, days_since_last={days_since_last}")
                if days_since_last > 30:
                    detail.is_active = False
                    print(f"DEBUG: DB subscription {getattr(sub, 'name', sub.id)} last_date={last_date} days_since_last={days_since_last} is_active=False (saving)")
                else:
                    detail.is_active = True
                    print(f"DEBUG: DB subscription {getattr(sub, 'name', sub.id)} last_date={last_date} days_since_last={days_since_last} is_active=True (saving)")
                detail.save()
            else:
                print(f"DEBUG: No valid last_date for sub id={sub.id}")
        else:
            print(f"DEBUG: No last_date for sub id={sub.id}")
    return subs