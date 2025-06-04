from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth.hashers import check_password
from .models import Child, Cost, Parent, Goals
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
import jdatetime
from rest_framework.permissions import AllowAny
import secrets
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from decimal import Decimal
from django.utils.timezone import now
from django.core.exceptions import ValidationError
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
        parent = child.parent
        children = parent.children.all()
        
        return Response(
            {
                "message": "فرزند با موفقیت ثبت شد.",
                "child_id": child.id,
                "parent_id": parent.id,
                "child_username": child.username,
                "parent": parent.username,
                'children': [{'id': c.id, 'username': c.username} for c in children],
            },
            status=status.HTTP_201_CREATED
        )


#Login
class ParentLoginView(generics.GenericAPIView):
    serializer_class = ParentLoginSerializer
    authentication_classes = ()  
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


### Getting the Expense sum by category(needs, wants, others)
def get_expense_sum_by_cate(child):
    persian_today = jdatetime.date.today()
        
    start_month = persian_today.replace(day=1)
    start_month_str = start_month.strftime('%Y-%m-%d')
    
    def get_sum(category):
        return Cost.objects.filter(
            child=child,
            type='expense',
            cate_choices=category,
            date__gte=start_month_str
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
    return {
        'needs': get_sum('needs'),
        'wants': get_sum('wants'),
        'others': get_sum('else')
    }


###Getting child from token that is in headers
def get_child_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    print("Authorization headerrrrrrrrrr:", auth_header)
    if  not auth_header.startswith('Token '):
        raise ValidationError("توکن نامعتبر لطفا دوباره وارد شوید.")
        
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


###Getting parent from token that is in headers
def get_parent_from_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Token '):
        raise ValidationError("توکن نامعتبر لطفا دوباره وارد شوید.")
    
    token = auth_header.split(' ')[1]
    parent_id = cache.get(f"parent_token_{token}")
    
    if not parent_id:
        raise ValidationError("احراز هویت نامعتبر - لطفا دوباره وارد شوید.")
    
    try:
        return Parent.objects.get(id=parent_id)
    except Parent.DoesNotExist:
        raise ValidationError("والد یافت نشد.")


#DetailAPIView
class DetailsView(APIView):
    authentication_classes = ()
    permission_classes = ()
    
    def get(self, request):

        child = get_child_from_token(request)   
  
        #Fetch their costs categorized
        total_expenses = get_expense_sum_by_cate(child)
        total_needs = total_expenses['needs']
        total_wants = total_expenses['wants']
        total_others = total_expenses['others']
        
        persian_today = jdatetime.date.today()
        
        start_month = persian_today.replace(day=1)
        start_month_str = start_month.strftime('%Y-%m-%d')
    
        
        needs = Cost.objects.filter(child=child, type='expense', date__gte=start_month_str, cate_choices='needs').order_by('-date')
        wants = Cost.objects.filter(child=child, type='expense', date__gte=start_month_str,  cate_choices='wants').order_by('-date')
        others=Cost.objects.filter(child=child, type='expense', date__gte=start_month_str,  cate_choices='else').order_by('-date')
        #Return the JSON 
        return Response(
            {
                'child': {
                    'id': child.id,
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
    
    def get(self, request):
        child = get_child_from_token(request)
        goals = child.goals.all().order_by('-id')
        serializer = GoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        child = get_child_from_token(request)
        serializer = GoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(child=child)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
   
#GoalsUpdateAPIview
class GoalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GoalSerializer
    authentication_classes = ()
    permission_classes = ()

    def get_object(self):
        child = get_child_from_token(self.request)
        goal = get_object_or_404(Goals, id=self.kwargs['pk'], child=child)
        return goal   
    
    
#Child_DashboardAPIView
class ChildDashboardAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request):       
        child = get_child_from_token(request)
        
        persian_today = jdatetime.date.today()
        start_day = persian_today
        start_week = persian_today - jdatetime.timedelta(days=persian_today.weekday())
        start_month = persian_today.replace(day=1)
        
        start_day_str = start_day.strftime('%Y-%m-%d')
        start_week_str = start_week.strftime('%Y-%m-%d')
        start_month_str = start_month.strftime('%Y-%m-%d')
        
        total_expenses = get_expense_sum_by_cate(child)
        
        needs = total_expenses['needs']
        wants = total_expenses['wants']
        others = total_expenses['others']
        
        daily_costs = child.costs.filter(date=start_day_str, type='expense')
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
            'needs': needs,
            'wants': wants,
            'others': others,
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

    def get(self, request):
        child = get_child_from_token(request)
        
        persian_today = jdatetime.date.today()
        
        start_month = persian_today.replace(day=1)
        start_month_str = start_month.strftime('%Y-%m-%d')
        
        total_expenses = get_expense_sum_by_cate(child)
        
        #The actual amount spent in every category in the current month
        needs = total_expenses['needs']
        wants = total_expenses['wants']
        others = total_expenses['others']
        
        
        income = Cost.objects.filter(
            child = child,
            type = 'income',
            date__gte = start_month_str
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        #The supposed amount for every category that the child should spend
        supposed_needs_amount = (Decimal(income) * Decimal(50)) / Decimal(100)
        supposed_wants_amount = (Decimal(income) * Decimal(30)) / Decimal(100)
        supposed_others_amount = (Decimal(income) * Decimal(20)) / Decimal(100)
        
        if(income>0):
            needs_percent = round((needs / supposed_needs_amount) * 100) if supposed_needs_amount > 0 else 0
            wants_percent = round((wants / supposed_wants_amount) * 100) if supposed_wants_amount > 0 else 0
            others_percent = round((others / supposed_wants_amount) * 100) if income > 0 else 0
        else:
            needs_percent = 0
            wants_percent = 0
            others_percent = 0
        
        print("needs_percent", needs_percent)
        print("wants_percent", wants_percent)
        print("others_percent", others_percent)
        
        #the difference between the supposed amount and the actual amount spent for every category
        needs_difference = abs(needs - supposed_needs_amount)
        wants_difference = abs(wants - supposed_wants_amount)
        others_difference = abs(others - supposed_others_amount)
        
        return Response({
            'child_id': child.id,
            'income': float(income),
            'needs': float(needs),
            'wants': float(wants),
            'others': float(others),
            'supposed_needs_amount': float(supposed_needs_amount),
            'supposed_wants_amount': float(supposed_wants_amount),
            'supposed_others_amount': float(supposed_others_amount),
            'needs_percent': needs_percent,
            'wants_percent': wants_percent,
            'others_percent': others_percent,
            'needs_difference': float(needs_difference),
            'wants_difference': float(wants_difference),
            'others_difference': float(others_difference),
        })
        
        
#ParentDashboardAPIView
class ParentDashboardAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    
    def get(self, request):
        parent = get_parent_from_token(request)
        children = parent.children.all()
        if not children:
            return Response({"detail": "کودکی برای این والد ثبت نشده است."}, status=404)

        child = children.first() 
  
        persian_today = jdatetime.date.today()
        start_day = persian_today
        start_week = persian_today - jdatetime.timedelta(days=persian_today.weekday())
        start_month = persian_today.replace(day=1)

        start_day_str = start_day.strftime('%Y-%m-%d')
        start_week_str = start_week.strftime('%Y-%m-%d')
        start_month_str = start_month.strftime('%Y-%m-%d')

        daily_total = child.costs.filter(date=start_day_str, type='expense').aggregate(total=Sum('amount'))['total'] or Decimal(0)
        weekly_total = child.costs.filter(date__gte=start_week_str, type='expense').aggregate(total=Sum('amount'))['total'] or Decimal(0)
        monthly_total = child.costs.filter(date__gte=start_month_str, type='expense').aggregate(total=Sum('amount'))['total'] or Decimal(0)
        
        now = jdatetime.datetime.now()
        current_month_start = now.replace(day=1)
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        two_months_ago_start = (prev_month_start - timedelta(days=1)).replace(day=1)

        total_income = Cost.objects.filter(child=child, type='income').aggregate(total_income=Sum('amount'))['total_income'] or 0
        persian_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        months = [
            persian_months[two_months_ago_start.month - 1],
            persian_months[prev_month_start.month - 1],
            persian_months[current_month_start.month - 1]
        ]
        
        total_expenses = get_expense_sum_by_cate(child)
        needs = total_expenses['needs']
        wants = total_expenses['wants']
        others = total_expenses['others']
        
        recent_costs = Cost.objects.filter(child_id=child.id).order_by('-date')[:6]
        recent_costs_data = [
            {
                'id': cost.id,
                'description': cost.description,
                'amount': float(cost.amount),
                'type': cost.type,
                'date': cost.date,  
            }
            for cost in recent_costs
        ]
        savings = Goals.objects.filter(child=child).aggregate(Sum('savings'))['savings__sum']
        savings = float(f"{savings:.1f}") if savings else 0
        
        income_expense_data = []
        for start_date in [two_months_ago_start, prev_month_start, current_month_start]:
            end_date = ((start_date + timedelta(days=31)).replace(day=1)) - timedelta(days=1)
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            total_income_period = Cost.objects.filter(child=child, date__gte=start_date_str, date__lte=end_date_str, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
            total_expense_period = Cost.objects.filter(child=child, date__gte=start_date_str, date__lte=end_date_str, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

            income_expense_data.append({
                'income': float(total_income_period),
                'expense': float(total_expense_period),
            })
        return Response({
            'child_id': child.id,
            'child_username': child.username,
            'parent_id': parent.id,
            'income': float(total_income),
            'recent_costs': recent_costs_data,
            'daily_total': float(daily_total),
            'weekly_total': float(weekly_total),
            'monthly_total': float(monthly_total),
            'persian_today': persian_today.strftime('%Y-%m-%d'),
            'savings': savings,
            'needs': float(needs),
            'wants': float(wants),
            'others': float(others),
            'children': [{'id': c.id, 'username': c.username} for c in children],
            'months': months,
            'income_expense_data': income_expense_data,
        }, status=status.HTTP_200_OK)
        