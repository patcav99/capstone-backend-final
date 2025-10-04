# Delete subscription view
from rest_framework.decorators import api_view
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from selenium import webdriver
from selenium.webdriver.common.by import By
from rest_framework.decorators import api_view
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


class DeleteSubscriptionView(APIView):

    def delete(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        subscription.delete()
        return Response({'detail': 'Subscription deleted.'}, status=status.HTTP_200_OK)

@api_view(["POST"])
def check_subscription_login_selenium(request):
    result["message"] = f"Error checking login with Selenium: {str(e)}"
    return Response(result, status=status.HTTP_200_OK if result["success"] else status.HTTP_401_UNAUTHORIZED)

# Generalized Selenium login check using subscription name
class SubscriptionSeleniumLoginView(APIView):
    def post(self, request):
        name = request.data.get('subscription_name')
        email = request.data.get('email')
        password = request.data.get('password')
        result = {'success': False, 'message': ''}

        login_url = SUBSCRIPTION_LOGIN_URLS.get(name)
        if not login_url:
            result['message'] = f"No login URL found for subscription: {name}"
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        try:
            import tempfile
            import logging
            try:
                import undetected_chromedriver as uc
                use_uc = True
                driver_type = "undetected-chromedriver"
            except ImportError:
                use_uc = False
                driver_type = "selenium-chrome"
            result['driver_type'] = driver_type
            from selenium.webdriver.chrome.options import Options
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # Remove headless and use a real user profile directory
            # Example: use default Chrome profile (update path as needed)
            try:
                import tempfile, random
                try:
                    import undetected_chromedriver as uc
                    use_uc = True
                except ImportError:
                    use_uc = False
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--headless')
                options.add_argument('--window-size=1200,800')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_argument('--disable-infobars')
                options.add_argument('--lang=en-US')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                import shutil
                chrome_path = shutil.which('chromium-browser') or shutil.which('chromium') or shutil.which('google-chrome')
                if chrome_path:
                    options.binary_location = chrome_path
                else:
                    result['message'] = 'No Chrome/Chromium binary found on system.'
                    return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                try:
                    if use_uc:
                        driver = uc.Chrome(options=options)
                    else:
                        driver = webdriver.Chrome(options=options)
                    try:
                        driver.get(login_url)
                        # Randomized delay for stealth
                        time.sleep(random.uniform(2.5, 7.5))
                        # Simulate human-like scrolling and mouse movement
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                        time.sleep(random.uniform(0.5, 1.5))
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                        time.sleep(random.uniform(0.5, 1.5))
                    except Exception as e:
                        import traceback, base64
                        page_source = driver.page_source if driver else ''
                        stack = traceback.format_exc()
                        screenshot_b64 = None
                        try:
                            screenshot = driver.get_screenshot_as_png()
                            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
                        except Exception:
                            screenshot_b64 = None
                        result['message'] = (
                            f"Network error: {type(e).__name__}: {str(e)}\n"
                            f"Stacktrace:\n{stack}\n"
                            f"Page source (truncated):\n{page_source[:2000]}"
                        )
                        result['page_source'] = page_source[:20000]
                        result['screenshot_b64'] = screenshot_b64
                        driver.quit()
                        return Response(result, status=status.HTTP_400_BAD_REQUEST)
                    # Example selectors, may need to be customized per service
                    try:
                        # Try case-insensitive search for email field
                        email_field = None
                        # Try by name 'email' (case-insensitive)
                        try:
                            email_field = driver.find_element(By.NAME, "email")
                        except Exception:
                            pass
                        # Try id selectors first
                        password_field = None
                        if name:
                            try:
                                email_field = driver.find_element(By.ID, "userIdentifier") 
                            except Exception:
                                pass
                            try:
                                password_field = driver.find_element(By.ID, "password")
                            except Exception:
                                pass
                        # Fallback to generic alternatives if not found
                        if not email_field:
                            try:
                                email_field = driver.find_element(By.ID, "login-username")
                            except Exception:
                                pass
                        if not password_field:
                            try:
                                 password_field = driver.find_element(By.ID, "login-password")
                            except Exception:
                                pass
                        if not email_field:
                            try:
                                email_field = driver.find_element(By.NAME, "email")
                            except Exception:
                                pass
                        # Try by type='email' if still not found
                        if not email_field:
                            try:
                                email_field = driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
                            except Exception:
                                pass
                        if not password_field:
                            try:
                                password_field = driver.find_element(By.NAME, "password")
                            except Exception:
                                pass
                        # Always get all input elements for fallback searches
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        # Try by name/id username/user for email
                        if not email_field:
                            for inp in inputs:
                                name_attr = inp.get_attribute("name")
                                id_attr = inp.get_attribute("id")
                                if name_attr and name_attr.lower() in ["email", "username", "user"]:
                                    email_field = inp
                                    break
                                if id_attr and id_attr.lower() in ["email", "username", "user"]:
                                    email_field = inp
                                    break
                        # Try by name/id password for password
                        if not password_field:
                            for inp in inputs:
                                name_attr = inp.get_attribute("name")
                                id_attr = inp.get_attribute("id")
                                if name_attr and name_attr.lower() == "password":
                                    password_field = inp
                                    break
                                if id_attr and id_attr.lower() == "password":
                                    password_field = inp
                                    break
                        # Try by type='password' if still not found
                        if not password_field:
                            try:
                                password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                            except Exception:
                                pass
                        if not email_field:
                            raise Exception("Email field not found (tried Peacock and common alternatives case-insensitive)")
                        if not password_field:
                            raise Exception("Password field not found (tried Peacock and common alternatives case-insensitive)")
                        from selenium.webdriver.support.ui import WebDriverWait
                        from selenium.webdriver.support import expected_conditions as EC
                        wait = WebDriverWait(driver, 15)
                        # Generalized two-step login flow
                        # If password field is not visible after loading, assume two-step login
                        wait.until(EC.visibility_of(email_field))
                        wait.until(EC.element_to_be_clickable(email_field))
                        driver.execute_script("arguments[0].scrollIntoView();", email_field)
                        email_field.send_keys(email)
                        # Try to find and click a 'Continue' or 'Next' button
                        next_btn = None
                        for selector in [
                            (By.ID, "continue"),
                            (By.ID, "next"),
                            (By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), 'Next')]")
                        ]:
                            try:
                                next_btn = driver.find_element(*selector)
                                wait.until(EC.visibility_of(next_btn))
                                wait.until(EC.element_to_be_clickable(next_btn))
                                driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                                next_btn.click()
                                break
                            except Exception:
                                continue
                        # After clicking, wait for password field
                        try:
                            password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
                        except Exception:
                            # Fallback to previous password_field if already found
                            pass
                        wait.until(EC.element_to_be_clickable(password_field))
                        driver.execute_script("arguments[0].scrollIntoView();", password_field)
                        password_field.send_keys(password)
                        # Try to find and click a 'Sign-In' or 'Login' button
                        login_btn = None
                        for selector in [
                            (By.ID, "signInSubmit"),
                            (By.XPATH, "//button[contains(text(), 'Sign In') or contains(text(), 'Login') or contains(text(), 'Log In')]")
                        ]:
                            try:
                                login_btn = driver.find_element(*selector)
                                wait.until(EC.visibility_of(login_btn))
                                wait.until(EC.element_to_be_clickable(login_btn))
                                driver.execute_script("arguments[0].scrollIntoView();", login_btn)
                                login_btn.click()
                                break
                            except Exception:
                                continue
                        time.sleep(15)
                    except Exception as e:
                        import traceback
                        page_source = driver.page_source if driver else ''
                        stack = traceback.format_exc()
                        result['message'] = (
                            f"Error interacting with login form: {type(e).__name__}: {str(e)}\n"
                            f"Stacktrace:\n{stack}\n"
                            f"Page source (truncated):\n{page_source[:2000]}"
                        )
                        driver.quit()
                        return Response(result, status=status.HTTP_400_BAD_REQUEST)
                    # Check for login success (Peacock: URL contains 'upgrade-now' or does NOT contain 'log-in'/'sign-in')
                    url = driver.current_url
                    url_lower = url.lower()
                    screenshot_b64 = None
                    try:
                        import base64
                        screenshot = driver.get_screenshot_as_png()
                        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
                    except Exception:
                        screenshot_b64 = None
                    if (
                        "login" not in url_lower and "signin" not in url_lower
                    ):
                        result['success'] = True
                        result['message'] = f"Login successful!"
                    else:
                        result['message'] = f"Login failed or needs more checks."
                    result['final_url'] = url
                    result['screenshot_b64'] = screenshot_b64
                    driver.quit()
                except Exception as e:
                    result['message'] = f"Error during browser launch or navigation: {type(e).__name__}: {str(e)}"
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                result['message'] = f"Error: {type(e).__name__}: {str(e)}"
        except Exception as e:
            result['message'] = f"Unexpected error: {type(e).__name__}: {str(e)}"
        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_401_UNAUTHORIZED)

SUBSCRIPTION_LOGIN_URLS = {
    "Peacock": "https://www.peacocktv.com/signin",
    "peacock": "https://www.peacocktv.com/signin",
    "Netflix": "https://www.netflix.com/login",
    "netflix": "https://www.netflix.com/login",
    "Hulu": "https://www.hulu.com/login",
    "hulu": "https://www.hulu.com/login",
    "Disney+": "https://www.disneyplus.com/login",
    "disney+": "https://www.disneyplus.com/login",
    "Fubo": "https://www.fubo.tv/signin",
    "fubo": "https://www.fubo.tv/signin",
    "playstation": "https://my.account.sony.com/sonyacct/signin/?duid=000000070009010085f0bccffad9e2662fa4bc3b157345eb7e7e27b1b0da75394910ebe57898f2ff&response_type=code&client_id=e4a62faf-4b87-4fea-8565-caaabb3ac918&scope=web%3Acore&access_type=offline&state=bff965675bb143e92e4c1151678c2c4b758790dbe0c21cb7188eb2819a8f6e30&service_entity=urn%3Aservice-entity%3Apsn&ui=pr&smcid=web%3Apdc&redirect_uri=https%3A%2F%2Fweb.np.playstation.com%2Fapi%2Fsession%2Fv1%2Fsession%3Fredirect_uri%3Dhttps%253A%252F%252Fio.playstation.com%252Fcentral%252Fauth%252Flogin%253Flocale%253Den_US%2526postSignInURL%253Dhttps%25253A%25252F%25252Fwww.playstation.com%25252Fen-us%25252Fplaystation-network%25252F%2526cancelURL%253Dhttps%25253A%25252F%25252Fwww.playstation.com%25252Fen-us%25252Fplaystation-network%25252F%26x-psn-app-ver%3D%2540sie-ppr-web-session%252Fsession%252Fv5.41.1&auth_ver=v3&error=login_required&error_code=4165&error_description=User+is+not+authenticated&no_captcha=true&cid=1e86060e-8330-48e0-a3ba-24ba1b23ab7d#/signin/input/id",
    "PlayStation": "https://my.account.sony.com/sonyacct/signin/?duid=000000070009010085f0bccffad9e2662fa4bc3b157345eb7e7e27b1b0da75394910ebe57898f2ff&response_type=code&client_id=e4a62faf-4b87-4fea-8565-caaabb3ac918&scope=web%3Acore&access_type=offline&state=bff965675bb143e92e4c1151678c2c4b758790dbe0c21cb7188eb2819a8f6e30&service_entity=urn%3Aservice-entity%3Apsn&ui=pr&smcid=web%3Apdc&redirect_uri=https%3A%2F%2Fweb.np.playstation.com%2Fapi%2Fsession%2Fv1%2Fsession%3Fredirect_uri%3Dhttps%253A%252F%252Fio.playstation.com%252Fcentral%252Fauth%252Flogin%253Flocale%253Den_US%2526postSignInURL%253Dhttps%25253A%25252F%25252Fwww.playstation.com%25252Fen-us%25252Fplaystation-network%25252F%2526cancelURL%253Dhttps%25253A%25252F%25252Fwww.playstation.com%25252Fen-us%25252Fplaystation-network%25252F%26x-psn-app-ver%3D%2540sie-ppr-web-session%252Fsession%252Fv5.41.1&auth_ver=v3&error=login_required&error_code=4165&error_description=User+is+not+authenticated&no_captcha=true&cid=1e86060e-8330-48e0-a3ba-24ba1b23ab7d#/signin/input/id",
    "amazon": "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0",
    "spotify": "https://accounts.spotify.com/en/login?login_hint=pat.cavalieri.99%40gmail.com&allow_password=1&continue=https%3A%2F%2Faccounts.spotify.com%2Fen%2Fstatus&flow_ctx=c924b6d5-2aa3-4370-baf6-3e24a19d7b45%3A1759032933"
    # Add more as needed
}

# API endpoint to get login URL for a subscription name
@api_view(["GET"])
def get_subscription_login_url(request):
    name = request.query_params.get("name")
    url = SUBSCRIPTION_LOGIN_URLS.get(name)
    if url:
        return Response({"login_url": url})
    else:
        return Response({"error": "Login URL not found for this subscription."}, status=404)

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
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only allow access if the user is subscribed
        if not subscription.users.filter(id=request.user.id).exists():
            return Response({'detail': 'You are not subscribed to this account.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReceiveListItemsView(APIView):
    permission_classes = [AllowAny]

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
                    subscription, _ = Subscription.objects.get_or_create(name=name.strip())
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
                    }
                    SubscriptionDetail.objects.update_or_create(
                        subscription=subscription,
                        defaults=detail_data
                    )
                    saved.append(subscription.name)
            elif isinstance(item, str) and item.strip():
                subscription, _ = Subscription.objects.get_or_create(name=item.strip())
                saved.append(subscription.name)

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
             