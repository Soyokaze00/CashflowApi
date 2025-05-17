from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth.hashers import check_password
from .models import Child, Cost, Parent, Goals
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
import jdatetime
from rest_framework.permissions import AllowAny
import secrets
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import (
    EmailVerificationSerializer,
    ParentSignupSerializer,
    ChildSignupSerializer,
    ParentLoginSerializer,
    ChildLoginSerializer,
    ParentVerificationCodeSerializer,
    ChildVerificationCodeSerializer,
    CostSerializer,
    GoalSerializer,
)


#*****************************************************************************************************

from datetime import timedelta
import json
import random

from django import forms
from decimal import Decimal
from django.contrib import messages
from .forms import *
from django.shortcuts import render, redirect

from django.utils.timezone import now

from django.conf import settings




from django.core.validators import validate_email
from django.core.exceptions import ValidationError

#*****************************************************************************************************


# Step 1: Send code
class ParentEmailVerifyView(generics.CreateAPIView):
    serializer_class = EmailVerificationSerializer
    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.is_child = False 
        return serializer
    

class ChildEmailVerifyView(generics.CreateAPIView):
    serializer_class = EmailVerificationSerializer
    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.is_child = True  
        return serializer
    
    
# Step 2: Confirm code
class ParentVerificationCodeView(generics.CreateAPIView):
    serializer_class = ParentVerificationCodeSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
      
        request.session['verified_email'] = serializer.validated_data['email']
        return Response({"message": "کد تایید با موفقیت بررسی شد"})
    
    
class ChildVerificationCodeView(generics.CreateAPIView):
    serializer_class = ChildVerificationCodeSerializer
    serializer_class = ChildVerificationCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Store verified email in session
        request.session['child_verified_email'] = serializer.validated_data['email']
        
        return Response(
            {
                "message": "ایمیل فرزند با موفقیت تایید شد"
            }
        )

    
# Step 3: Confirm username and password + create ==> SIGN UP
class ParentSignupView(generics.CreateAPIView):
    serializer_class = ParentSignupSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    

class ChildSignupView(generics.CreateAPIView):
    serializer_class = ChildSignupSerializer
    authentication_classes = ()  
    permission_classes = ()
    
    def post(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        child = serializer.save()
        
        return Response(
            {
                "message": "فرزند با موفقیت ثبت شد.",
                "child_id": child.id,
                "parent_id": child.parent.id,
                "child_username": child.username,
                "parent_username": child.parent.username,
            },
            status=status.HTTP_201_CREATED
        )



#Login
class ParentLoginView(generics.GenericAPIView):
    serializer_class = ParentLoginSerializer
    authentication_classes = ()  # No auth needed to login
    permission_classes = ()
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        parent = serializer.validated_data['user']
        
        token = secrets.token_urlsafe(32) 
        cache.set(f"parent_token_{token}", parent.id, timeout=60*60*24*7)
        
        print(f"Generated token: {token}")
        print(f"STORED IN CACHE: parent_token_{token} -> {parent.id}")  # Debug
      
            
        return Response(
            {
                "message": "ورود با موفقیت انجام شد.",
                "parent_id": parent.id,
                "token": token,
                "email": parent.email,
                "username": parent.username
            },
            status=status.HTTP_200_OK
        )


class ChildLoginView(generics.GenericAPIView):
    serializer_class = ChildLoginSerializer
    authentication_classes = ()  # No auth needed to login
    permission_classes = ()
    
    def post(self, request, *args, **kwargs):
       
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            child = Child.objects.get(email=email)
        except Child.DoesNotExist:
            return Response({"detail": "ایمیل اشتباه است."}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not check_password(password, child.password):
            return Response({"details": "رمز عبور اشتباه است"}, status=status.HTTP_401_UNAUTHORIZED)
        
        child = serializer.validated_data['user']
        token = secrets.token_urlsafe(32) 
        cache.set(f"child_token_{token}", child.id, timeout=60*60*24*7) #for 7 days
        print("CACHED RIGHT AFTER SET?", cache.get(f"child_token_{token}"))
        
        print(f"Generated token: {token}")
        print(f"STORED IN CACHE: child_token_{token} -> {child.username}")  
        
        return Response(
            {
                "child_username": child.username,
                "message": "ورود با موفقیت انجام شد.",
                "child_id": child.id,
                "token": token,
                "email": child.email,
               
            },
            status=status.HTTP_200_OK
        )



#CostAPIView
class CostView(generics.ListCreateAPIView):
    serializer_class = CostSerializer
    authentication_classes = ()  
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        print("$$$$$$$$$$$$$$$$")
        #Getting the token from the header
        
        auth_header = self.request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Cost.objects.none()
        
        token = auth_header.split(' ')[1]
        print("THISSS ISSS THE STOREDDD TOOKEENNViewwww: \n", token)
        child_id = cache.get(f"child_token_{token}")
        
        if not child_id:
            return Cost.objects.none()
        
        child = Child.objects.get(id=child_id)
        
        filter_option = self.request.query_params.get('filter', 'all')
        
        persian_today = jdatetime.date.fromgregorian(date=now().date())
        
        if filter_option == 'day':
            start_date = persian_today
            end_date = persian_today
        elif filter_option == 'month':
            start_date = persian_today.replace(day=1)
            end_date = persian_today
        elif filter_option == 'week':
            start_date = persian_today - jdatetime.timedelta(days=persian_today.weekday())
            end_date = persian_today
        else:  # all
            start_date = None
            end_date = None
            
        if start_date and end_date:
            return child.costs.filter(
                Q(date__gte=start_date.strftime('%Y-%m-%d')) & Q(date__lte=end_date.strftime('%Y-%m-%d'))
            ).order_by('-date')
        else:
            return child.costs.all().order_by('-date')
        
    def perform_create(self, serializer):
        print("PERRFORRRMMM_CREEEATTE")

        persian_date = self.request.data.get('date')
        try:
            jdatetime.datetime.strptime(persian_date, '%Y-%m-%d')
        except Exception:
            raise ValidationError({"date": "فرمت تاریخ اشتباه است!"})

        serializer.save()


#DetailAPIView
class DetailsView(APIView):
    authentication_classes = ()
    permission_classes = ()
    
    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith("Token "):
            return Response(
                {
                    "error": "توکن نامعتبر لطفا دوباره وارد شوید.",
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = auth_header.split(" ")[1]
        child_id = cache.get(f"child_token_{token}")
        if not child_id:
            return Response({"error": "احراز هویت نامعتبر - لطفا دوباره وارد شوید."}, status=status.HTTP_401_UNAUTHORIZED)
            
            
        child=get_object_or_404(Child, id=child_id)
  
        #Fetch their costs categorized
        
        needs = Cost.objects.filter(child=child, type='expense', cate_choices='needs',).order_by('-date')
        wants = Cost.objects.filter(child=child, type='expense', cate_choices='wants',).order_by('-date')
        others = Cost.objects.filter(child=child, type='expense', cate_choices='else',).order_by('-date')
        
        # Calculate total sums
        total_needs = needs.aggregate(Sum('amount'))['amount__sum'] or 0
        total_wants = wants.aggregate(Sum('amount'))['amount__sum'] or 0
        total_others = others.aggregate(Sum('amount'))['amount__sum'] or 0
        
        #Return the JSON
        
        return Response(
            {
                'child': {
                    'id': child_id,
                    'username': child.username,
                    'email': child.email,
                },
                'needs': [
                    {
                        'id': cost.id,
                        'amount': cost.amount,
                        'description': cost.description,
                        'date': cost.date,
                        'type': cost.type
                    } for cost in needs
                ],
                'wants': [
                    {
                        'id': cost.id,
                        'amount': cost.amount,
                        'description': cost.description,
                        'date': cost.date,
                        'type': cost.type
                    } for cost in wants
                ],
                'others': [
                    {
                        'id': cost.id,
                        'amount': cost.amount,
                        'description': cost.description,
                        'date': cost.date,
                        'type': cost.type
                    } for cost in others
                ],
                'total_needs': total_needs,
                'total_wants': total_wants,
                'total_others': total_others
            },
            status=status.HTTP_200_OK
        )



#GoalsAPIview
class GoalAPIView(APIView):
    serializer_class = GoalSerializer
    authentication_classes = ()
    permission_classes = ()
    
    def get_child_from_token(self):
        auth_header = self.request.headers.get('Authorization', '')
        print("Authorization headerrrrrrrrrr:", auth_header)
        if  not auth_header.startswith('Token '):
            raise AuthenticationFailed("توکن نامعتبر لطفا دوباره وارد شوید.")
        
        token = auth_header.split(' ')[1]
        print("Extracted tokeeeeeeeeeen:", token)
        child_id = cache.get(f"child_token_{token}")
        print("Found child IDDDDDDDDDD:", child_id)
        
        if not child_id:
            raise ValidationError("احراز هویت نامعتبر - لطفا دوباره وارد شوید.")
        try:
            return Child.objects.get(id=child_id)
        except Child.DoesNotExist:
            raise ValidationError("کودک یافت نشد.")
    
    def get(self, request):
        child = self.get_child_from_token()
        goals = child.goals.all().order_by('-id')
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        child = self.get_child_from_token()
        serializer = GoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(child=child)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   

class GoalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GoalSerializer
    authentication_classes = ()
    permission_classes = ()

    def get_child_from_token(self):
        auth_header = self.request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            raise ValidationError("توکن نامعتبر لطفا دوباره وارد شوید.")

        token = auth_header.split(' ')[1]
        child_id = cache.get(f"child_token_{token}")
        if not child_id:
            raise ValidationError("احراز هویت نامعتبر - لطفا دوباره وارد شوید.")
        try:
            return Child.objects.get(id=child_id)
        except Child.DoesNotExist:
            raise ValidationError("کودک یافت نشد.")

    def get_object(self):
        child = self.get_child_from_token()
        goal = get_object_or_404(Goals, id=self.kwargs['pk'], child=child)
        return goal
    
    
    
#Child_DashboardAPIView
class ChildDashboardAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    
    def get_child_from_token(self):
        auth_header = self.request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            raise ValidationError("توکن نامعتبر لطفا دوباره وارد شوید.")
        
        
        token = auth_header.split(' ')[1]
        child_id = cache.get(f'child_token_{token}')
        if not child_id:
            raise ValidationError("احراز هویت نامعتبر\nلطفا دوباره وارد شوید.")
        try:
            return Child.objects.get(id=child_id)
        except Child.DoesNotExist:
            raise ValidationError("کودک یافت نشد.")
        
        
    def get(self, request):
        
        child = self.get_child_from_token()
        
        persian_today = jdatetime.date.today()
        start_day = persian_today
        start_week = persian_today - jdatetime.timedelta(days=persian_today.weekday())
        start_month = persian_today.replace(day=1)
        
        start_day_str = start_day.strftime('%Y-%m-%d')
        start_week_str = start_week.strftime('%Y-%m-%d')
        start_month_str = start_month.strftime('%Y-%m-%d')
        print("start_day_strrrrrrrrrrrrr", start_day_str)
        
        daily_costs = child.costs.filter(date=start_day_str, type='expense')
        print("DAILYYYY:", daily_costs)
        weekly_costs = child.costs.filter(date__gte=start_week_str, type='expense')
        monthly_costs = child.costs.filter(date__gte=start_month_str, type='expense')
        
        daily_total = daily_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
        weekly_total = weekly_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
        monthly_total = monthly_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)      
        
        recent_costs = Cost.objects.filter(child=child).order_by('-date')[:10]
        recent_costs_serialized = CostSerializer(recent_costs, many=True).data
        
        top_goals = child.goals.all()[:3]
        goals_data = []
        for goal in top_goals:
            goals_data.append({
                'id': goal.id,
                'goal': goal.goal,
                'goal_amount': goal.goal_amount,
                'savings': goal.savings,
            })
            
        return Response({
            'persian_today': persian_today.strftime('%Y-%m-%d'),
            'daily_total': daily_total,
            'weekly_total': weekly_total,
            'monthly_total': monthly_total,
            'recent_costs': recent_costs_serialized,
            'top_goals': goals_data,
        })
    
#EducationAPIView
class EducationAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    
    def get_child_from_token(self):
        auth_header = self.request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            raise ValidationError("توکن نامعتبر لطفا دوباره وارد شوید.")
        
        token = auth_header.split(' ')[1]
        child_id = cache.get(f'child_token_{token}')
        
        if not child_id:
            raise ValidationError("احراز هویت نامعتبر - لطفا دوباره وارد شوید.")
        
        try:
            return Child.objects.get(id=child_id)
        except Child.DoesNotExist:
            raise ValidationError("فرزند موجود نیست.")
    
    def get(self, request):
        child = self.get_child_from_token()
        
        persian_today = jdatetime.date.today()
        
        start_month = persian_today.replace(day=1)
        start_month_str = start_month.strftime('%Y-%m-%d')
        
        needs = Cost.objects.filter(
            child = child,
            type = 'expense',
            cate_choices = 'needs',
            date__gte = start_month_str
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        wants = Cost.objects.filter(
            child = child,
            type = 'expense',
            cate_choices = 'wants',
            date__gte = start_month_str
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        other = Cost.objects.filter(
            child = child,
            type = 'expense',
            cate_choices = 'else',
            date__gte = start_month_str
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        income = Cost.objects.filter(
            child = child,
            type = 'income',
            date__gte = start_month_str
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        supposed_needs_amount = (Decimal(income) * Decimal(50)) / Decimal(100)
        supposed_wants_amount = (Decimal(income) * Decimal(30)) / Decimal(100)
        supposed_other_amount = (Decimal(income) * Decimal(20)) / Decimal(100)
        
        if(income>0):
            actual_needs_perce = round((needs / income) * 100) if income > 0 else 0
            actual_wants_perce = round((wants / income) * 100) if income > 0 else 0
            actual_other_perce = round((other / income) * 100) if income > 0 else 0
        else:
            total_sum = needs + wants + other
            if total_sum > 0: 
                actual_needs_perce = round((needs / total_sum) * 100, 0)
                actual_wants_perce = round((wants / total_sum) * 100, 0)
                actual_other_perce = round((other / total_sum) * 100, 0)
            else:
                actual_needs_perce = 0
                actual_wants_perce = 0
                actual_other_perce = 0
                
        print("***************************************************")
        print("income:", income)
        print("needs", needs)
        print("wants", wants)
        print("other", other)
        print("actual_needs_perce", actual_needs_perce)
        print("actual_wants_perce", actual_wants_perce)
        print("actual_other_perce", actual_other_perce)
        
        needs_difference = abs(needs - supposed_needs_amount)
        wants_difference = abs(wants - supposed_wants_amount)
        other_difference = abs(other - supposed_other_amount)
        
        return Response({
            'child_id': child.id,
            'income': float(income),
            'needs': float(needs),
            'wants': float(wants),
            'other': float(other),
            'supposed_needs_amount': float(supposed_needs_amount),
            'supposed_wants_amount': float(supposed_wants_amount),
            'supposed_other_amount': float(supposed_other_amount),
            'actual_needs_perce': actual_needs_perce,
            'actual_wants_perce': actual_wants_perce,
            'actual_other_perce': actual_other_perce,
            'needs_difference': float(needs_difference),
            'wants_difference': float(wants_difference),
            'other_difference': float(other_difference),
        })
        


#..........................................................................................................................



def education(request, child_id):
    child=get_object_or_404(Child, id=child_id)
    persian_today=jdatetime.date.today()

    current_month_start=persian_today.replace(day=1)
    next_month_start = (current_month_start + timedelta( days = 31 )).replace(day=1)
    current_month_end = next_month_start - timedelta( days = 1 )

    needs = Cost.objects.filter(
        child = child,
        type = 'expense',
        cate_choices = 'needs',
        date__gte = current_month_start,
        date__lte = current_month_end,
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    wants = Cost.objects.filter(
        child = child,
        type = 'expense',
        cate_choices = 'wants',
        date__gte = current_month_start,
        date__lte = current_month_end,
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    other = Cost.objects.filter(
        child = child,
        type = 'expense',
        cate_choices = 'else',
        date__gte = current_month_start,
        date__lte = current_month_end,
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    income = Cost.objects.filter(
        child=child,
        type = 'income',
        date__gte = current_month_start,
        date__lte = current_month_end,
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    supposed_needs_amount = (Decimal(income) * Decimal(50)) / Decimal(100)
    supposed_wants_amount = (Decimal(income) * Decimal(30)) / Decimal(100)
    supposed_other_amount = (Decimal(income) * Decimal(20)) / Decimal(100)
    if(income>0):
        actual_needs_perce = round((needs / income) * 100) if income > 0 else 0
        actual_wants_perce = round((wants / income) * 100) if income > 0 else 0
        actual_other_perce = round((other / income) * 100) if income > 0 else 0
    else:
        total_sum = needs + wants + other
        if total_sum > 0: 
            actual_needs_perce = round((needs / total_sum) * 100, 0)
            actual_wants_perce = round((wants / total_sum) * 100, 0)
            actual_other_perce = round((other / total_sum) * 100, 0)
        else:
            actual_needs_perce = 0
            actual_wants_perce = 0
            actual_other_perce = 0
    print("***************************************************")
    print("income:", income)
    print("needs", needs)
    print("wants", wants)
    print("other", other)
    print("actual_needs_perce", actual_needs_perce)
    print("actual_wants_perce", actual_wants_perce)
    print("actual_other_perce", actual_other_perce)

    needs_difference = abs(needs - supposed_needs_amount)
    wants_difference = abs(wants - supposed_wants_amount)
    other_difference = abs(other - supposed_other_amount)

    

    

    context = {
        'child': child,
        'needs': needs,
        'wants': wants,
        'other': other,
        'income': income,
        'supposed_needs_amount': supposed_needs_amount,
        'supposed_wants_amount': supposed_wants_amount,
        'supposed_other_amount': supposed_other_amount,
        'actual_needs_perce': actual_needs_perce,
        'actual_wants_perce': actual_wants_perce,
        'actual_other_perce': actual_other_perce,
        'needs_difference': needs_difference,
        'wants_difference': wants_difference,
        'other_difference': other_difference,
    }

    return render(request, 'cashflow/education.html', context)
    


#..........................................................................................................................



def landing(request):
    return render(request, 'cashflow/landing.html')


#.........................................................................................................................


def goals(request, child_id):
    child=get_object_or_404(Child, id=child_id)
    goals=child.goals.all()
    

    goal_to_edit=None
    edit_goal_id=request.POST.get("edit_goal_id")

    if edit_goal_id:
        goal_to_edit=goals.filter(id=edit_goal_id).first()
        if not goal_to_edit:
            messages.error(request, "Goal not found")
            return redirect('goals', child_id = child_id)
        
        
    goal_form = goalsForm()
    update_form = GoalUpdateForm(instance=goal_to_edit)
        

        
    if request.method == "POST":
        print("Form submitted with POST data:", request.POST) 

        if 'add_goal' in request.POST:
            goal_form = goalsForm(request.POST)
            if goal_form.is_valid():
                goal = goal_form.save(commit=False)
                goal.child=child
                print("Goals for child:", child.goals.all())
                goal.save()
                messages.success(request, "Goal added successfully.")
                return redirect('goals', child_id=child_id)
            else:
                messages.error(request, "Failed to add goal. Please fix the errors below.")

        elif 'update_savings' in request.POST and goal_to_edit:
            update_form=GoalUpdateForm(request.POST, instance=goal_to_edit)
            if update_form.is_valid():
                update_form.save()
                messages.success(request, "Savings updated successfully.")
                return redirect('goals', child_id=child_id)
            else:
                messages.error(request, "Failed to update savings. Please fix the errors below.")
  
        delete_goal_id = request.POST.get("delete_goal_id") 
       
        if delete_goal_id:
            goal = goals.filter(id=delete_goal_id).first()
            if  goal:
                goal.delete()
                messages.success(request, "Goal deleted successfully.")
            else:
                messages.error(request, "Goal not found.")
            return redirect('goals', child_id=child_id)
        
    # else:      
    #     goal_form = goalsForm()
    #     update_form = GoalUpdateForm(instance = goal_to_edit)
    chart_data = [    
        {
            'name': goal.goal,
            'progress': round((goal.savings / goal.goal_amount) * 100) if goal.goal_amount > 0 else 0,
        }
        for goal in goals
    ]
    for goal in goals:
        goal.progress_percentage = round((goal.savings / goal.goal_amount) * 100) if goal.goal_amount > 0 else 0
    print("Chart Data:", chart_data)


    context = {
        'goal_form': goal_form, 
        'update_form': update_form, 
        'child': child,
        'goal_to_edit': goal_to_edit,
        'goals': goals,
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'cashflow/goals.html', context)


#.........................................................................................................................

def child_dashboard(request, child_id):
   
   child=get_object_or_404(Child, id=child_id)
   print(request.session.get('child_id'))

   persian_today = jdatetime.date.today()
    
   

   start_day = persian_today
   start_week = persian_today - jdatetime.timedelta(days=persian_today.weekday())
   start_month = persian_today.replace(day=1)

   start_day_str = start_day.strftime('%Y-%m-%d')
   start_week_str = start_week.strftime('%Y-%m-%d')
   start_month_str = start_month.strftime('%Y-%m-%d')

   daily_costs = child.costs.filter(date=start_day_str, type='expense')
   weekly_costs = child.costs.filter(date__gte=start_week_str, type='expense')
   monthly_costs = child.costs.filter(date__gte=start_month_str, type='expense')

   daily_total = daily_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
   weekly_total = weekly_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
   monthly_total = monthly_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)

   CATEGORY_TRANSLATIONS = {key: value for key, value in Cost.EXPENSE_CATEGORIES}

   top_categories = (
       Cost.objects.filter(child = child, type='expense', date__gte = start_month_str)
       .values('cate_choices')
       .annotate(total_spending=Sum('amount'))
       .order_by('-total_spending')[:6]
   )
   total_income = (
    Cost.objects.filter(child=child, type='income')
    .aggregate(total_income=Sum('amount'))
)

   categories = [CATEGORY_TRANSLATIONS[item['cate_choices']] for item in top_categories]

   amount = [float(item['total_spending']) for item in top_categories]

   income = total_income['total_income'] if total_income['total_income'] else 0
   recent_costs=Cost.objects.filter(child_id=child_id).order_by('-date')[:10]

   top_goals = child.goals.all()[:3]
   for goal in top_goals:
       goal.progress_percentage = ((goal.savings/goal.goal_amount) * 100) 
       if goal.progress_percentage == 100:
        goal.border_radius = "10px"
       else:
        goal.border_radius = "0"


   print("Categories:", categories)
   print("Amounts:", amount)
   print("Income:", income)


   context = {
       'child' : child,
       'categories' : categories,
       'amount' : amount,
       'income': income,
       'recent_costs': recent_costs,
       'daily_total': daily_total,
       'weekly_total': weekly_total,
       'monthly_total': monthly_total,
       'persian_today': persian_today.strftime('%Y-%m-%d'),
       'top_goals': top_goals,
   }


   return render(request, 'cashflow/child_dashboard.html', context)


#.........................................................................................................................

def parent_dashboard(request, child_id):
    child=get_object_or_404(Child, id=child_id)
    parent=child.parent
    print(request.session.get('child_id'))
    children=parent.children.all()



    persian_today = jdatetime.date.today()

    # filter_options = request.GET.get('filter', 'all')

    start_day = persian_today
    start_week = persian_today - jdatetime.timedelta(days=persian_today.weekday())
    start_month = persian_today.replace(day=1)

    start_day_str = start_day.strftime('%Y-%m-%d')
    start_week_str = start_week.strftime('%Y-%m-%d')
    start_month_str = start_month.strftime('%Y-%m-%d')

    daily_costs = child.costs.filter(date=start_day_str, type='expense')
    weekly_costs = child.costs.filter(date__gte=start_week_str, type='expense')
    monthly_costs = child.costs.filter(date__gte=start_month_str, type='expense')

    daily_total = daily_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    weekly_total = weekly_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    monthly_total = monthly_costs.aggregate(total=Sum('amount'))['total'] or Decimal(0)


    now=jdatetime.datetime.now()

    current_month_start=now.replace(day=1)
    prev_month_start=(current_month_start - timedelta(days=1)).replace(day=1)
    two_months_ago_start = (prev_month_start - timedelta(days=1)).replace(day=1)
    
    next_month_start = (current_month_start + jdatetime.timedelta(days=31)).replace(day=1)
    current_month_end = next_month_start - jdatetime.timedelta(days=1)
    current_month_end_str = current_month_end.strftime('%Y-%m-%d')

    CATEGORY_TRANSLATIONS = {key: value for key, value in Cost.EXPENSE_CATEGORIES}

    top_categories = (
       Cost.objects.filter(
           child = child, 
           type='expense',
           date__gte=start_month_str, 
           date__lte=current_month_end_str,   
           )
       .values('cate_choices')
       .annotate(total_spending=Sum('amount'))
       .order_by('-total_spending')[:6]
    )
    total_income = (
     Cost.objects.filter(child=child, type='income')
    .aggregate(total_income=Sum('amount'))
    )

        # The calculation needed for the bar diagram:

   

    #get their names in persian:

    persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    months = [
        persian_months[two_months_ago_start.month - 1],
        persian_months[prev_month_start.month - 1],
        persian_months[current_month_start.month - 1]
    ]

    

    
    needs = Cost.objects.filter(
        child=child,
        date__gte=start_month_str, 
        date__lte=current_month_end_str,
        type='expense', 
        cate_choices='needs'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    wants = Cost.objects.filter(
        child=child, 
        date__gte=start_month_str,
        date__lte=current_month_end_str, 
        type='expense', 
        cate_choices='wants'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    other = Cost.objects.filter(
        child=child, 
        date__gte=start_month_str, 
        date__lte=current_month_end_str,
        type='expense', 
        cate_choices='else'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

    categories = [CATEGORY_TRANSLATIONS[item['cate_choices']] for item in top_categories] 

    amount = [float(item['total_spending']) for item in top_categories] 

    income = total_income['total_income'] if total_income['total_income'] else 0
    recent_costs=Cost.objects.filter(child_id=child_id).order_by('-date')[:6]

    CA_pairs = zip(categories, amount)
    periods = ['روز', 'هفته', 'ماه', 'همه']

    savings=Goals.objects.filter(child=child).aggregate(Sum('savings'))['savings__sum'] 
    if savings:
        savings = float(f"{savings:.1f}")






    income_expense_data = []

    for start_date in [two_months_ago_start, prev_month_start, current_month_start]:

        end_date = ((start_date + timedelta(days=31)).replace(day=1))- timedelta(days=1)

        start_date_str = start_date.strftime('%Y-%m-%d') 
        end_date_str = end_date.strftime('%Y-%m-%d') 
        print("Start date:", start_date_str, "End date:", end_date_str)

        total_income = (
            Cost.objects.filter(
                child=child,
                date__gte=start_date_str,
                date__lte = end_date_str,
                type='income',
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        )

        total_expense = (
            Cost.objects.filter(
                child=child,
                date__gte = start_date_str,
                date__lte = end_date_str,
                type = 'expense'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        )

        income_expense_data.append(
           { 
               'income': float(total_income),  
               'expense': float(total_expense) 
            }
        )


        print("mmmmmmmmm: ", months)
        print("incomExpeneeee: ", income_expense_data)




    context = {
        'child': child,
        'parent': parent,
        'categories': categories,
        'amount': amount,
        'income': income,
        'recent_costs': recent_costs,
        'CA_pairs': CA_pairs,
        'periods': periods,
        'daily_total': daily_total,
        'weekly_total': weekly_total,
        'monthly_total': monthly_total,
        'persian_today': persian_today.strftime('%Y-%m-%d'),
        'children': children,
        'savings': savings,
        'needs': needs,
        'wants': wants,
        'other':other,
        'months': json.dumps(months),
        'income_expense_data': json.dumps(income_expense_data), 
    }
    return render(request, 'cashflow/parent_dashboard.html', context)

#.........................................................................................................................







    