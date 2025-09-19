from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView


from .serializers import RegisterSerializer, LoginSerializer, ChangePasswordSerializer
from rest_framework import status



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

class ReceiveListItemsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        items = request.data.get('items', None)
        if items is None or not isinstance(items, list):
            return Response({
                'message': 'Invalid data. Expected a list of items under the key "items".',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        saved = []
        for name in items:
            if isinstance(name, str) and name.strip():
                obj, created = Subscription.objects.get_or_create(name=name.strip())
                saved.append(obj.name)

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
             