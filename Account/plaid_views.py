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
# Django view to search for a merchant's website using Selenium
@csrf_exempt
@require_POST
def get_merchant_website(request):
    import json
    try:
        data = json.loads(request.body)
        merchant_name = data.get('merchant_name')
        if not merchant_name:
            return JsonResponse({'error': 'merchant_name required'}, status=400)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    url = None
    try:
        driver.get('https://www.google.com')
        time.sleep(1)
        # Accept cookies if prompted
        try:
            consent = driver.find_element(By.XPATH, "//button[contains(., 'I agree') or contains(., 'Accept all')]")
            consent.click()
            time.sleep(1)
        except Exception:
            pass
        search_box = driver.find_element(By.NAME, 'q')
        search_box.send_keys(merchant_name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        results = driver.find_elements(By.CSS_SELECTOR, 'div.yuRUbf > a')
        if results:
            url = results[0].get_attribute('href')
    finally:
        driver.quit()
    if url:
        return JsonResponse({'website_url': url})
    else:
        return JsonResponse({'error': 'No website found'}, status=404)


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
    # Toggle mock via query param (?mock=1) or POST field (mock: true)
    use_mock = False
    # Always check query param first for mock toggle
    if request.GET.get('mock') == '1':
        use_mock = True
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        use_mock = data.get('mock') in [True, '1', 1]
    else:
        data = {}
    if use_mock:
        mock_data = {
            "outflow_streams": [
                {
                    "merchant_name": "Netflix",
                    "description": "Monthly subscription",
                    "first_date": "2023-01-01",
                    "last_date": "2023-10-01",
                    "frequency": "monthly",
                    "average_amount": {
                        "amount": 15.99
                    },
                    "last_amount": { 
                        "amount": 15.99
                    },
                    "is_active": True,
                    "predicted_next_date": "2023-11-01",
                    "last_user_modified_datetime": "2023-10-01T12:00:00Z",
                    "status": "active"
                },
                {
                    "merchant_name": "Spotify",
                    "description": "Music subscription",
                    "first_date": "2023-02-15",
                    "last_date": "2023-10-15",
                    "frequency": "monthly",
                    "average_amount": {
                        "amount": 9.99
                    },
                    "last_amount": { 
                        "amount": 9.99
                    },
                    "is_active": True,
                    "predicted_next_date": "2023-11-15",
                    "last_user_modified_datetime": "2023-10-15T12:00:00Z",
                    "status": "active"
                },
                {
                    "merchant_name": "Planet Fitness",
                    "description": "Fitness membership",
                    "first_date": "2023-03-01",
                    "last_date": "2023-10-01",
                    "frequency": "monthly",
                    "average_amount": {
                        "amount": 40.00
                    },
                    "last_amount": { 
                        "amount": 40.00
                    },
                    "is_active": True,
                    "predicted_next_date": "2023-11-01",
                    "last_user_modified_datetime": "2023-10-01T12:00:00Z",
                    "status": "active"
                }
            ]
        }
        return JsonResponse(mock_data)
    # Otherwise, fetch from Plaid
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
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