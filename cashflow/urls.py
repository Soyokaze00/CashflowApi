from django.urls import path, include
from .import views

urlpatterns=[
    
    #Parent flows
    path('api/parent/signup/email/', views.ParentEmailVerifyView.as_view(), name='parent-email-verify'),
    path('api/parent/signup/verify-code/', views.ParentVerificationCodeView.as_view(), name='parent-signup-verify-code'),
    path('api/parent/signup/confirm/', views.ParentSignupView.as_view(), name='parent-signup-confirm'),
    path('api/parent/login/', views.ParentLoginView.as_view(), name='parent-login'),
    
    
    
    # Child flows
    path('api/child/signup/email/', views.ChildEmailVerifyView.as_view(),    name='child-email-verify'),
    path('api/child/signup/verify-code/', views.ChildVerificationCodeView.as_view(), name='child-signup-verify-code'),
    path('api/child/signup/confirm/', views.ChildSignupView.as_view(),  name='child-signup-confirm'),
    path('api/child/login/', views.ChildLoginView.as_view(), name='child-login'),
    
    
    path('api/costs', views.CostView.as_view, name='child-costs'),
    
    
    
    
    path("", views.landing, name="landing"),
    path("parent/signup/", views.parent_signup, name="parent_signup"),
    path("parent/login/", views.parent_login, name="parent_login"),
    path("child/signup/<int:parent_id>/", views.child_signup, name="child_signup"),
    path("child/login/", views.child_login, name="child_login"),
    path("costs/<int:child_id>/", views.costs, name="costs"),
    path("child/dashboard/<int:child_id>/", views.child_dashboard, name="child_dashboard"),
    path("parent/dashboard/<int:child_id>/", views.parent_dashboard, name="parent_dashboard"),
    path("goals/<int:child_id>/", views.goals, name="goals" ),
    path("details/<int:child_id>/", views.details, name="details"),
    path('education/<int:child_id>/', views.education, name='education'),
    path('api-auth/', include('rest_framework.urls')),

]



