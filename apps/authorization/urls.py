from django.urls import path
from . import views

urlpatterns = [
    path('v1/permissions/', views.PermissionView.as_view(),
         name="permission_view"),
    path('v1/permissions/<int:id>/', views.PermissionDetailView.as_view(),
         name="permission_detail_view"),
    path('v1/role_permissions/', views.RolePermissionView.as_view(),
         name="role_permission_view"),
    path('v1/role_permissions/<int:id>/', views.RoleDetailsView.as_view(),
         name="role_details_view"),
    path('v1/role_permissions/data/',
         views.RolePermissionViewV2.as_view(), name="role_permissions"),
    path('v1/single_role_permissions/<int:role_id>/',
         views.SpecificRolePermissionView.as_view(), name="role_permission_operations"),
    path('v1/assign_role_user/', views.AssignRolePermissionView.as_view(),
         name="assign_role"),
    path('v1/assign_role_users/', views.AssignRolePermissionView2.as_view(),
         name="assign_role_in_multiple_users"),
    path('v1/view_all_users/', views.ViewAllUserView.as_view(),
         name="view_all_users"),
    path('v1/me/', views.ViewSingleUserRolesPermissionsView.as_view(),
         name="user_roles_permissions_detail"),
#    onboarding urls
    path('v1/onboarding/staff/', views.OnboardingStaffView.as_view(),
         name="onboarding_staff"),
    path('v1/onboarding/staff/verify/', views.OnboardingStaffVerifyView.as_view(),
         name="onboarding_staff_verify"),
    path('v1/onboarding/staff/register/', views.OnboardingStaffRegisterView.as_view(),
         name="onboarding_staff_register"),
    # list of customers, vendors, store owners, staff
    path('v1/staffs/list/', views.AllStaffListView.as_view(),
         name="staffs_list"),
    path('v1/vendors/list/', views.AllVendorListView.as_view(),
         name="vendors_list"),
    path('v1/store_owners/list/', views.AllStoreOwnerListView.as_view(),
         name="store_owner_list"),
    path('v1/customers/list/', views.AllCustomerListView.as_view(),
         name="customer_list"),
    
]