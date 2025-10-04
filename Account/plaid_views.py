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
# Endpoint to fetch recurring transactions for a given access_token (for testing)
@csrf_exempt
def get_recurring_transactions(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    access_token = data.get('access_token')
    if not access_token:
        return JsonResponse({'error': 'access_token required'}, status=400)
    req = TransactionsRecurringGetRequest(access_token=access_token)
    response = client.transactions_recurring_get(req)
    return JsonResponse(response.to_dict())

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
    return JsonResponse(response.to_dict())

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


# Set up Plaid configuration
configuration = Configuration(
    host=os.environ.get("PLAID_ENV_URL", "https://sandbox.plaid.com"),
    api_key={
        "clientId": os.environ["PLAID_CLIENT_ID"],
        "secret": os.environ["PLAID_SECRET"],
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

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