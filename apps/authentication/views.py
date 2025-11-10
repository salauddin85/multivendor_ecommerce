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
from apps.authentication.tasks import send_register_confirmation_email, send_otp_mail_to_email
from apps.authentication.utils.function import generate_random_token


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


class VendorRegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        """
            Register a new vendor user.
        """
        data = request.data
        serializer = serializers.RegistrationVendorSerializer(
            data=data) 
        if serializer.is_valid():
            vendor = serializer.save()  
            register_verify = models.RegisterVerificationSuccessfulEmail.objects.filter(email=vendor.email)
            if register_verify.exists():
                register_verify.delete()
     
            # initiate CELERY to send mail
            send_register_confirmation_email.delay_on_commit(
                email=vendor.email,
                context={
                    "email": vendor.email,
                    "first_name": vendor.first_name,
                    "last_name": vendor.last_name,
                    "user_type": vendor.user_type
                }
            )
            log_request(request, "Vendor registered successfully", "info", f"Vendor {vendor.id} registered", response_status_code=status.HTTP_201_CREATED)
            return Response({
                "status": "success",
                'code': status.HTTP_201_CREATED,
                'message': "Vendor registered successfully",
                "data": {
                    "email": vendor.email,
                    "first_name": vendor.first_name,
                    "last_name": vendor.last_name
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "failed",
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "invalid request",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)      

class StoreOwnerRegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        """
            Register a new store owner user.
        """
        data = request.data
        serializer = serializers.RegistrationStoreOwnerSerializer(
            data=data) 
        if serializer.is_valid():
            store_owner = serializer.save()  
            register_verify = models.RegisterVerificationSuccessfulEmail.objects.filter(email=store_owner.email)
            if register_verify.exists():
                register_verify.delete()
     
            # initiate CELERY to send mail
            send_register_confirmation_email.delay_on_commit(
                email=store_owner.email,
                context={
                    "email": store_owner.email,
                    "first_name": store_owner.first_name,
                    "last_name": store_owner.last_name,
                    "user_type": store_owner.user_type
                }
            )
            log_request(request, "Store owner registered successfully", "info", f"Store owner {store_owner.id} registered", response_status_code=status.HTTP_201_CREATED)
            return Response({
                "status": "success",
                'code': status.HTTP_201_CREATED,
                'message': "Store owner registered successfully",
                "data": {
                    "email": store_owner.email,
                    "first_name": store_owner.first_name,
                    "last_name": store_owner.last_name
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "failed",
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "invalid request",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            

class CustomerRegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        """
            Register a new customer user.
        """
        data = request.data
        serializer = serializers.RegistrationCustomerSerializer(
            data=data) 
        if serializer.is_valid():
            customer = serializer.save()  
            register_verify = models.RegisterVerificationSuccessfulEmail.objects.filter(email=customer.email)
            if register_verify.exists():
                register_verify.delete()
     
            # initiate CELERY to send mail
            send_register_confirmation_email.delay_on_commit(
                email=customer.email,
                context={
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "user_type": customer.user_type
                }
            )
            log_request(request, "Customer registered successfully", "info", f"Customer {customer.id} registered", response_status_code=status.HTTP_201_CREATED)
            return Response({
                "status": "success",
                'code': status.HTTP_201_CREATED,
                'message': "Customer registered successfully",
                "data": {
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "failed",
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "invalid request",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
            
class ForgetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
            Set OTP to the OTP model if user with email exist
        """
        data = request.data
        serializer = serializers.ForgetPasswordSerializer(
            data=data) 
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = randint(100000, 999999)  # Generate OTP
            # Checking if a user with OTP Exist
            is_exist = models.ForgetPasswordOTP.objects.filter(
                email=email).exists()
            if is_exist:

                otp_model = models.ForgetPasswordOTP.objects.get(email=email)
                otp_model.expire_time = timezone.now()
                otp_model.otp = otp  
                otp_model.save()
                send_otp_mail_to_email.delay_on_commit(otp, email)
            else:
                # If new user Create OTP Model
                models.ForgetPasswordOTP.objects.create(email=email, otp=otp)
                # initiate CELERY to send mail
                send_otp_mail_to_email.delay_on_commit(otp, email)
            return Response({
                "status": "success",
                'code': status.HTTP_200_OK,
                'message': "OTP has been created successfully",
                "details": "OTP send successful"
            }, status=status.HTTP_200_OK)
        else:

            return Response({
                "status": "failed",
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "invalid request",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)



class VerifyOtpView(APIView):
    def post(self, request):
        """
            Verify OTP with given email here
        """
        try:
            data = request.data
            serializer = serializers.VerifyOtpSerializer(data=data)
            if serializer.is_valid():
                email = serializer.validated_data["email"]
                otp = serializer.validated_data['otp']
                forget_password_otp_obj = get_object_or_404(
                    models.ForgetPasswordOTP, email=email)
                if forget_password_otp_obj.otp != otp:  # check if OTP matched

                    return Response({
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed while verifying OTP",
                        "status": "failed",
                        "can_change_pass": False,
                        "details": "OTP didn't match"
                    }, status=status.HTTP_400_BAD_REQUEST)

                if forget_password_otp_obj.is_expired():  # check if OTP has expired

                    return Response({
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "Failed while verifying OTP",
                        "status": "failed",
                        "can_change_pass": False,
                        "details": "OTP expired generate a new OTP"
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    token = generate_random_token()
                    forget_password_otp_obj.token = token
                    forget_password_otp_obj.save(update_fields=['token'])

                    return Response({
                        "code": status.HTTP_200_OK,
                        "message": "Operation successful",
                        "status": "success",
                        "can_change_pass": True,
                        "details": "Generated new Token for changing password",
                        "token": token
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.exception(str(e))

                    return Response({
                        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "Error occurred",
                        "status": "failed",
                        'errors': {'server_error': [str(e)]}

                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:

                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    "status": "failed",
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Something went wrong",
                'status': "failed",
                'errors': {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ResetPasswordView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated()]
        else:
            return [AllowAny()]

    def post(self, request):
        """
            Reset password for valid user with valid email address
        """
        try:
            data = request.data
            serializer = serializers.ResetPasswordSerializer(
                data=data)  # validate the request
            if serializer.is_valid():
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']
                pass_change_token = serializer.validated_data['token']
                forget_password_otp_obj = get_object_or_404(
                    models.ForgetPasswordOTP, email=email)

                if pass_change_token != forget_password_otp_obj.token:

                    return Response({
                        'code': status.HTTP_400_BAD_REQUEST,
                        'status': 'failed',
                        'message': "Error while matching token",
                        'detail': 'Token did not match',
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    try:
                        with transaction.atomic():
                            user = get_user_model().objects.get(email=email)
                            user.set_password(password)  # Change password
                            user.save()
                            # Create new token and return
                            refresh = RefreshToken.for_user(user)
                            access_token = refresh.access_token
                            forget_password_otp_obj.delete()
                            response = Response({
                                "status": "success",
                                "code": status.HTTP_200_OK,
                                "message": "Operation successful",
                                "access_token": str(access_token),
                                "refresh_token": str(refresh)
                            }, status=status.HTTP_200_OK)
                            # set cookie
                          
                            response.set_cookie(
                                settings.SIMPLE_JWT["AUTH_COOKIE"],
                                str(access_token),
                                httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                                secure=os.getenv("COOKIE_SECURE") == "True",
                                max_age=timedelta(
                                    days=7).total_seconds()
                            )
                            
                            response.set_cookie(
                                settings.SIMPLE_JWT["AUTH_COOKIE_USER_TYPE"],
                                user.user_type,
                                httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                                secure=os.getenv("COOKIE_SECURE") == "True",
                                max_age=timedelta(
                                    days=7).total_seconds()
                            )

                            return response
                    except Exception as e:
                        logger.exception(str(e))

                        return Response({
                            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "message": "Error occurred",
                            'status': 'failed', 'detail': str(e),
                            "errors": {
                                'server_error': [str(e)]
                            }
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:

                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request",
                    'status': "failed",
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Something went wrong",
                'status': "failed",
                'errors': {
                    "server_error": [str(e)]
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):

        user = request.user
        serializer = serializers.UpdatePasswordSerializer(
            data=request.data, context={"user": user})

        if serializer.is_valid():
            serializer.update(user, serializer.validated_data)

            return Response({
                "code": status.HTTP_200_OK,
                "message": "Password Updated successfully",
                "status": "success"
            }, status=status.HTTP_200_OK)
        else:

            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request data",
                "status": "failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
