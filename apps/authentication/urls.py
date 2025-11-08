from django.urls import path, include
from . import views

urlpatterns = [
    path('v1/login/', views.LoginLogoutView.as_view(), name="login_view"),
    path('v1/logout/', views.LoginLogoutView.as_view(), name="logout_view"),

    # path('v1/register/vendor/', views.RegistrationTrainerView.as_view(), name="register_vendor_view"),
    # path('v1/register/store_owner/', views.CandidateRegisterView.as_view(), name="register_store_owner_view"),
    # path('v1/register/customer/', views.CandidateRegisterView.as_view(), name="register_customer_view"),
    # path('v1/register/email/', views.CandidateTrainerRegisterEmailView.as_view(), name="register_candidate_email_view"),
    # path('v1/register/email/verify/', views.CandidateTrainerRegisterOtpVerifyView.as_view(), name="register_candidate_email_verify_view"),
    # path('v1/forget_password/', views.ForgetPasswordView.as_view(),
    #      name="account_forget_password"),
    # path('v1/reset_password/', views.ResetPasswordView.as_view(),
    #      name="account_reset_password"),
    # path('v1/verify_otp/', views.VerifyOtpView.as_view(), name="verify_otp"),
]