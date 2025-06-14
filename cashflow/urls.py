from django.urls import path
from .import views

urlpatterns=[
    
    #Parent flows
    path('api/parent/signup/email/', views.ParentEmailVerifyView.as_view(), name='parent-email-verify'),
    path('api/parent/signup/verify-code/', views.ParentVerificationCodeView.as_view(), name='parent-signup-verify-code'),
    path('api/parent/signup/confirm/', views.ParentSignupView.as_view(), name='parent-signup-confirm'),
    path('api/parent/login/', views.ParentLoginView.as_view(), name='parent-login'),
    
    
    
    # Child flows
    path('api/child/signup/email/', views.ChildEmailVerifyView.as_view(), name='child-email-verify'),
    path('api/child/signup/verify-code/', views.ChildVerificationCodeView.as_view(), name='child-signup-verify-code'),
    path('api/child/signup/confirm/', views.ChildSignupView.as_view(), name='child-signup-confirm'),
    path('api/child/login/', views.ChildLoginView.as_view(), name='child-login'),
    
    #Cost & Detail
    path('api/costs', views.CostView.as_view(), name='child-costs'),
    path('api/costs/<int:pk>/', views.CostDeleteUpdateAPIView().as_view(), name='cost-delete-update'),
    path('api/details', views.DetailsView.as_view(), name='child-details'),
    
    #Goal
    path('api/goals/', views.GoalAPIView.as_view(), name='goals-api'),  # GET, POST
    path('api/goals/<int:pk>/', views.GoalDetailAPIView.as_view(), name='goal-detail-api'), # PATCH, DELETE
    
    #Dashboards
    path('api/child/dashboard', views.ChildDashboardAPIView.as_view(), name='child-dashboard-api'),
    path('api/parent/dashboard', views.ParentDashboardAPIView.as_view(), name='parent-dashboard-api'),
    
    #Education
    path('api/education', views.EducationAPIView.as_view(), name='education-api'),
    
]



