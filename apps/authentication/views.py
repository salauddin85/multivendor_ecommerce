from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
# from .tasks import send_otp_mail_to_email, send_register_confirmation_email
from datetime import timedelta
import os
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import serializers
from . import models
from random import randint
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from apps.activity_log.utils.functions import log_request
# from .utils.function import generate_random_token
logger = logging.getLogger("myapp")
from rest_framework_simplejwt.exceptions import TokenError
from apps.authorization.tasks import send_otp_email
from apps.authorization.models import OTP, VerifySuccessfulEmail


class LoginLogoutView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        """
        Login to the system with valid credentials.
        Generates JWT (access + refresh) tokens and sets them as secure HttpOnly cookies.
        """
        try:
            serializer = serializers.LoginSerializer(data=request.data)
            if not serializer.is_valid():
                log_request(request, "Login failed: invalid data",
                            "error", "Invalid serializer data", response_status_code=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "code": 400,
                    "status": "failed",
                    "message": "Invalid data.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            remember_me = request.data.get('remember_me', False)
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            user = authenticate(email=email, password=password)

            if not user:
                log_request(request, "Login failed: invalid credentials",
                            "error", "Invalid email or password", response_status_code=status.HTTP_401_UNAUTHORIZED)
                return Response({
                    "code": 401,
                    "status": "failed",
                    "message": "Invalid email or password"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            user_type = user.user_type

            # Build response
            response = Response({
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "Login successful",
                "access_token": access_token,
                "user_type": user_type,
            }, status=status.HTTP_200_OK)

            # Prevent caching
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

            # Set HttpOnly cookies for both tokens
            cookie_lifetime_days = 15 if remember_me == True else 7

            cookie_max_age = timedelta(days=cookie_lifetime_days).total_seconds()

            response.set_cookie(
                settings.SIMPLE_JWT["AUTH_COOKIE"],
                access_token,
                httponly=True,
                secure=os.getenv("COOKIE_SECURE", "False") == "True",
                max_age=cookie_max_age,
                # samesite='Lax',
            )
            response.set_cookie(
                settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"],
                refresh_token,
                httponly=True,
                secure=os.getenv("COOKIE_SECURE", "False") == "True",
                max_age=cookie_max_age,
                # samesite='Lax',
            )
            response.set_cookie(
                settings.SIMPLE_JWT["AUTH_COOKIE_USER_TYPE"],
                user_type,
                httponly=True,
                secure=os.getenv("COOKIE_SECURE", "False") == "True",
                max_age=cookie_max_age,
                # samesite='Lax',
            )

            # Log successful login
            log_request(request, "User logged in successfully", "info",
                        f"User {user.id} logged in", response_status_code=status.HTTP_200_OK)
            return response

        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Login failed: server error", "error",
                        str(e), response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": 500,
                "status": "failed",
                "message": "Something went wrong.",
                "errors": {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """
        Logout: blacklist refresh token and delete cookies.
        """
        try:
            refresh_cookie_name = settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"]
            refresh_token = request.COOKIES.get(refresh_cookie_name)

            # Prepare response
            response = Response({
                'code': status.HTTP_200_OK,
                'status': "success",
                'message': "Logout successful"
            }, status=status.HTTP_200_OK)

            # Delete both cookies
            response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
            response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
            response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE_USER_TYPE"])


            # No-cache headers
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

            # Blacklist refresh token if available
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()  # works if blacklist app is enabled
                    logger.info("Refresh token blacklisted on logout.")
                except TokenError:
                    logger.warning("Invalid refresh token on logout; skipping blacklist.")

            log_request(request, "User logged out", "info",
                        "User logged out successfully", response_status_code=status.HTTP_200_OK)
            return response

        except Exception as e:
            logger.exception(str(e))
            log_request(request, "Logout failed: server error", "error",
                        str(e), response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'status': "failed",
                'message': "Error occurred",
                'errors': {"server_error": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class  CommonRegisterEmailView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        try:
            data = request.data
            serializer = serializers.CommonRegisterEmailSerializer(
                data=data)
            if serializer.is_valid():
                serializer.save()
                with transaction.atomic():
                    email = serializer.validated_data["email"]
                    try:
                        otp = OTP.objects.get(email=email)
                        otp_value = otp.otp
                        send_otp_email.delay_on_commit(email, otp_value)

                    except OTP.DoesNotExist:
                        return Response({
                            "code": status.HTTP_404_NOT_FOUND,
                            "message": "Invalid request",
                            "status": "failed",
                            "errors": {
                                'otp': ["OTP for the provided email does not exist."]
                            }}, status=status.HTTP_404_NOT_FOUND)
                    response = Response({
                        "code": status.HTTP_201_CREATED,
                        "message": "Operation successful",
                        "status": "success",
                        "message": "OTP sent successfully",
                        "to": {
                            "email": email,
                        }
                    }, status=status.HTTP_201_CREATED)
                    # log the request
                    log_request(request, "Registration OTP sent", "info", f"OTP sent successfully to '{email}' for  registration", response_status_code=status.HTTP_201_CREATED)
                    return response
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Registration OTP sending failed", "error", "OTP sending for registration failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 
class CommonRegisterOtpVerifyView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        try:
            data = request.data
            serializer = serializers.CommonRegisterOtpVerifySerializer(
                data=data)
            if serializer.is_valid():
                email = serializer.validated_data["email"]
                otp = serializer.validated_data["otp"]
                otp_object = OTP.objects.get(email=email, otp=otp)
                otp_object.delete()
                try:
                    models.RegisterVerificationSuccessfulEmail.objects.create(email=email)
                except Exception as e:
                    logger.exception(str(e))
                    # log the request
                    log_request(request, "Email verification failed", "error", "Email verification failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    return Response({
                        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "Invalid request",
                        "status": "failed",
                        "errors": {
                            'email': [str(e)]
                        }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                # log the request
                response = Response({
                                    "code": status.HTTP_200_OK,
                                    "message": "Email verified successfully",
                                    "status": "success",
                                    "email": email,
                                    }, status=status.HTTP_200_OK)
                log_request(request, "Email verified", "info", f"Email '{email}' verified successfully", response_status_code=status.HTTP_200_OK)
                return response
            
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request",
                "status": "failed",
                "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(str(e))
            # log the request
            log_request(request, "Email verification failed", "error", "Email verification failed due to server error", response_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Error occurred",
                "status": "failed",
                'errors': {
                    'server_error': [str(e)]
                }}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

