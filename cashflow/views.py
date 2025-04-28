from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth.hashers import check_password
from .models import Child, Cost, Parent, Goals
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
import jdatetime
import secrets
from django.utils.timezone import now
from rest_framework.views import APIView
from .serializers import (
    EmailVerificationSerializer,
    ParentSignupSerializer,
    ChildSignupSerializer,
    ParentLoginSerializer,
    ChildLoginSerializer,
    ParentVerificationCodeSerializer,
    ChildVerificationCodeSerializer,
    CostSerializer,
)


#*****************************************************************************************************

from datetime import timedelta
import json
import random
from khayyam import JalaliDate
from django import forms
from decimal import Decimal
from django.contrib import messages
from .forms import *
from django.shortcuts import render, redirect

from django.utils.timezone import now
from django.core.mail import send_mail
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
        cache.set(f"parent_token_{token}", parent.id, timeout=3600)
        
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
        cache.set(f"child_token_{token}", child.id, timeout=36000) #for 10 Hours
        
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



#CostApiView
class CostView(generics.ListCreateAPIView):
    serializer_class = CostSerializer
    authentication_classes = ()  
    permission_classes = ()
    
    def get_queryset(self):
        
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

        persian_date = self.request.data.get('date')
        try:
            jdatetime.datetime.strptime(persian_date, '%Y-%m-%d')
        except Exception:
            raise ValidationError({"date": "فرمت تاریخ اشتباه است!"})

        serializer.save()


#DetailApiView
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




#..........................................................................................................................



def landing(request):
    return render(request, 'cashflow/landing.html')

#..........................................................................................................................



def parent_signup(request):
    
    if "signup_stage" not in request.session:
        request.session["signup_stage"] = 1
    
    errors = {}
    allowed_domains = ['gmail.com']
    
    
    stage = request.session.get("signup_stage", 1)
    print("staaagggeeee: ", stage)
    print("Current stage:", request.session.get('signup_stage'))
    
    form = parentSignupForm()
    
    if request.method == "POST":
        print(form.errors)
        print("THIS ISS POSSTTTT")
        print("POST Data:", request.POST)
        
        if stage == 1:
            email = request.POST.get("email")
            print("THIS ISSS STAGEE ONEEEEEEEEE")
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "Invalid email format.")
                return redirect("parent_signup")

            
            if Parent.objects.filter(email=email).exists():
                messages.error(request, "This email is already registered.")
                return redirect("parent_signup")

            verification_code = secrets.randbelow(900000) + 100000
            print("verification_code", verification_code)
            

            # Save email and verification code in session
            if not email:
                errors['email'] = 'ایمیل الزامی است.'
            else:
                # Extract the email domain
                email_domain = email.split('@')[-1]
                # Check if the domain is allowed
                if email_domain not in allowed_domains:
                    errors['email'] = 'لطفاً فقط از ایمیل‌های معتبر استفاده کنید (مانند Gmail).'
          
                
            request.session['email'] = email
            request.session['verification_code'] = verification_code
            if email:
                request.session['signup_stage'] = 2  # Move to next stage
            print("Moved to stage 2.")
            request.session.set_expiry(300)  # Session expires after 5 minutes
            
            print("Stored email:", email)
            print("Stored code:", verification_code)
        
            print(f"Attempting to send verification code to {email}")
            try:
                send_mail(
                    ' کد تایید ثبت نام شما در کش فلو ☺️ ',
                    f'کد تایید شما: {verification_code}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                print("Email sent successfully!") 
                
            except Exception as e:
                print(f"خطا در ارسال ایمیل : {e}")
                messages.error(request, f"خطا در ارسال ایمیل : {e}")
                return redirect("parent_signup")
            # messages.success(request, "Verification code sent to your email.")
            return redirect("parent_signup")
        
        
        elif stage == 2:
            print("222222222222222222222222222")
            action = request.POST.get("action", None)
            if action == "prev_stage":
                # Go to the previous stage
                print("ACTIIONNNNNNNNNNNNNNNNNNNNNNNnnn")
                request.session["signup_stage"] = stage - 1 
                print("STAGE IN 2222: ", stage)
                return redirect("parent_signup")
            print("Stage 2 POST data:", request.POST)
            email = request.POST.get("email")
            entered_code = request.POST.get("verification_code")
            stored_code = request.session.get("verification_code")
            if not entered_code:
                errors['verification_code'] = 'کد تأیید الزامی است.'
            
            stored_email = request.session.get("email")
            print("Verification code:", request.POST.get("verification_code"))
            print("Stage 2 Debug:")
            print("Email entered:", email)
            print("Email stored:", stored_email)
            print("Code entered:", entered_code)
            print("Code stored:", stored_code)
            # print("WAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
            
            if str(stored_code) == str(entered_code):
                request.session['signup_stage'] = 3  # Move to final stage
                print("Verification successful, moving to stage 3.")
                return redirect("parent_signup")
            else:
                errors['verification_code'] = 'کد تأیید نامعتبر است.'
                request.session['signup_stage'] = 2  # Stay at stage 2
                print("Verification failed, staying at stage 2.")
                return redirect("parent_signup")    
                
        elif stage == 3:
            print("333333333333333333333333333333333333")
            action = request.POST.get("action", None)
            if action == "prev_stage":
                # Go to the previous stage
                print("ACTIIONNNNNNNNNNNNNNNNNNNNNNNnnn3333")
                request.session["signup_stage"] = stage - 1 
                print("STAGE IN 3333: ", stage)
                return redirect("parent_signup")
            # Get the email from the session
            stored_email = request.session.get("email")

            # Combine POST data with the session email
            post_data = request.POST.copy()
            post_data['email'] = stored_email

            form = parentSignupForm(post_data)
            
            print("IS THE FORM VALID: ", form.is_valid())
            if form.is_valid():
                print("Form is valid, saving...")
                form.save()
                # Clear session data
                request.session.flush()
                return redirect("landing")
            else:
               print(form.errors) 
               
        elif "prev_stage" in request.POST: 
            # Handle going back to the previous stage
            print("1111111111111111111111111111111")
            request.session["signup_stage"] = max(1, stage - 1)
            return redirect("parent_signup")
            

    else:
        print("THIS ISS NOOTTTTT POSSTTTT")
        print("Handling GET request")
        print("Form is invalid:", form.errors) 
    
        form = parentSignupForm()  # Provide a blank form for stage 3
        form._errors = {}

    return render(request, "cashflow/parent_signup.html", {'stage': stage, 'form': form, "errors": errors,})


    
    

#...........................................................................................................................

def parent_login(request):
    if request.method == 'POST':
        form=ParentLoginForm(request.POST)
        print("IN POOOOSSSSTTTTTTTTT")
        print("FORM VALID: ", form.is_valid)
        if form.is_valid():
            print("THE FOOORRMMM ISS VAALLIIDD")
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
        
            try:
                parent=Parent.objects.get(email=email)
                print("PPPPAAAAAAAAAAAARRRRENT EMAIL: ", parent)
                if check_password(password, parent.password):
                    request.session['user_type'] = 'Parent'
                    request.session['user_id'] = parent.id

                    child=parent.children.first()
                    if child:
                        return redirect('parent_dashboard', child.id)
                    else:
                        #in case the parent doesn't have any children they will be immediatly taken to the child sign up page
                        return redirect('child_signup', parent.id)
                else:
                    return render(request, 'cashflow/parent_login.html', {
                        'form':form,
                        'error': "رمز عبور اشتباه است. لطفاً دوباره تلاش کنید."
                    })
        
            except Parent.DoesNotExist:
                return render(request, 'cashflow/parent_login.html', {
                    'form':form,
                    'error': "هیچ کاربری با این ایمیل وجود ندارد. لطفاً ثبت نام کنید."
                })
        else:
            # Form is not valid (e.g., missing email or password)
            return render(request, 'cashflow/parent_login.html', {
                'form': form,
                'error': "لطفاً تمام فیلدهای مورد نیاز را پر کنید."
            })
    else:
        print("NOTT IN POOOOSSSSTTTTTTTTT")
        form=ParentLoginForm()

    return render(request, 'cashflow/parent_login.html', {'form':form})

#...........................................................................................................................

def child_signup(request, parent_id):
    parent=get_object_or_404(Parent, id=parent_id)
    children = parent.children.all()
    if "signup_stage" not in request.session:
        request.session["signup_stage"] = 1
        
    stage = request.session.get("signup_stage", 1)
    errors = {}
    allowed_domains = ['gmail.com']
    
    form = ChildSignupForm()
    
    if request.method=="POST":
        print("THIS ISS POSSTTTT")
        print("POST Data:", request.POST)
        
        
        if stage == 1:
            # Collect and validate child's email
            email = request.POST.get("email")
            print("THIS ISSS STAGEE ONEEEEEEEEE")
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "Invalid email format.")
                return redirect("child_signup", parent_id=parent.id)

            if Child.objects.filter(email=email).exists():
                messages.error(request, "This email is already registered.")
                return redirect("child_signup", parent_id=parent.id)

            verification_code = secrets.randbelow(900000) + 100000
            request.session["child_email"] = email
            request.session["child_verification_code"] = verification_code
            if email:
                request.session["signup_stage"] = 2
                print("Moved to stage 2.")
                
                request.session.set_expiry(300)
                
            else:
                email_domain = email.split('@')[-1]
                # Check if the domain is allowed
                if email_domain not in allowed_domains:
                    errors['email'] = 'لطفاً فقط از ایمیل‌های معتبر استفاده کنید (مانند Gmail).'
                    
            print("Stored email:", email)
            print("Stored code:", verification_code)
        
            print(f"Attempting to send verification code to {email}")
            # Send verification email
            try:
                send_mail(
                    ' کد تایید ثبت نام بچه شما در کش فلو ☺️ ',
                    f'کد تایید : {verification_code}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                print("Email sent successfully!") 
                
                messages.success(request, "Verification code sent to your email.")
            except Exception as e:
                messages.error(request, f"Error sending email: {e}")
                return redirect("child_signup", parent_id=parent.id)

            return redirect("child_signup", parent_id=parent.id)
        
        
        elif stage == 2:
            # Verify the code
            print("222222222222222222222222222")
            print("Stage 2 POST data:", request.POST)
            child_email = request.POST.get("child_email")
            entered_code = request.POST.get("verification_code")
            stored_code = request.session.get("child_verification_code")
            if not entered_code:
                errors['verification_code'] = 'کد تأیید الزامی است.'
                
            stored_email = request.session.get("child_email")
            print("Verification code:", request.POST.get("verification_code"))
            print("Stage 2 Debug:")
            print("Email entered:", child_email)
            print("Email stored:", stored_email)
            print("Code entered:", entered_code)
            print("Code stored:", stored_code)
           
        
            action = request.POST.get("action", None)
            if action == "prev_stage":
                # Go to the previous stage
                print("ACTIIONNNNNNNNNNNNNNNNNNNNNNNnnn")
                request.session["signup_stage"] = stage - 1 
                print("STAGE IN 2222: ", stage)
                return redirect("child_signup", parent_id=parent.id)
            

            if str(entered_code) == str(stored_code):
                request.session["signup_stage"] = 3
                print("Verification successful, moving to stage 3.")
                return redirect("child_signup", parent_id=parent.id)
            else:
                errors['verification_code'] = 'کد تأیید نامعتبر است.'
                request.session['signup_stage'] = 2  # Stay at stage 2
                print("Verification failed, staying at stage 2.")
                return redirect("child_signup", parent_id=parent.id)
        
        
        
        elif stage == 3:
            print("333333333333333333333333333333333333")
            action = request.POST.get("action", None)
            if action == "prev_stage":
                # Go to the previous stage
                print("ACTIIONNNNNNNNNNNNNNNNNNNNNNNnnn")
                request.session["signup_stage"] = stage - 1 
                print("STAGE IN 33333: ", stage)
                return redirect("child_signup", parent_id=parent.id)
            # Final stage: Save the child's information
            stored_email = request.session.get("child_email")
            post_data = request.POST.copy()
            post_data["email"] = stored_email

            form = ChildSignupForm(post_data)
            print("IS THE FORM VALID: ", form.is_valid())
            if form.is_valid():
                child = form.save(commit=False)
                child.parent = parent
                child.save()
                request.session.flush()  # Clear session data
                return redirect("parent_dashboard", child_id=child.id)
            
            else:
                messages.error(request, "Please correct the errors below.")
                return redirect("child_signup", parent_id=parent.id)
        
        
        # form=ChildSignupForm(request.POST)
        # if form.is_valid():
        #     child=form.save(commit=False)
        #     child.parent=parent
        #     child.save()
        #     print("CHILD_ID: ", child.id)
        #     return redirect("parent_dashboard", child_id = child.id)
        
    else:
        print("THIS ISS NOOTTTTT POSSTTTT")
        print("Handling GET request")
        print("Form is invalid:", form.errors)
        form = ChildSignupForm()  # Provide a blank form for stage 3
        form._errors = {}
        # return render(request, "child_signup.html", {
        #     'form': form, 
        #     "parent":parent, 
        #     'children': children,
        #     'stage': stage,
        #     'errors': errors,
        #     })
        
        
    print("PARENT_ID: ", parent.id, parent)
    
    
    return render(request, 'cashflow/child_signup.html', {
        'form': form, 
        "parent":parent, 
        'children': children,
        'stage': stage,
        'errors': errors,
        
        })

#..........................................................................................................................

def costs(request, child_id):
    child=get_object_or_404(Child, id=child_id)
    filter_option = request.GET.get('filter', 'all')

    persian_today = jdatetime.date.fromgregorian(date=now().date())

    if filter_option == 'day':
        start_date=persian_today
        end_date=persian_today
    elif filter_option == 'month':
        start_date=persian_today.replace(day=1)
        end_date=persian_today
    elif filter_option =='all':
        start_date=None
        end_date=None

    else: 
        start_date=persian_today - jdatetime.timedelta(days=persian_today.weekday())
        end_date=persian_today

    if start_date and end_date:
        costs=child.costs.filter(
        Q(date__gte=start_date.strftime('%Y-%m-%d')) &
        Q(date__lte=end_date.strftime('%Y-%m-%d'))
    ).order_by('-date')
    else:
        costs = child.costs.all().order_by('-date')
    
    if request.method=="POST":
        print("Form submitted with POST data:", request.POST) 
        delete_cost_id = request.POST.get("delete_cost_id") 
       
        if delete_cost_id:
            cost = child.costs.filter(id=delete_cost_id).first()
            if cost:
                cost.delete()
                messages.success(request, "Cost deleted successfully.")
            else:
                messages.error(request, "Cost not found.")
            return redirect('costs', child_id=child_id)
        

        form=costsForm(request.POST)

        type_value = request.POST.get('type', 'expense')
        if type_value == 'income':
            form.fields['cate_choices'].choices = Cost.INCOME_CATEGORIES
        elif type_value == 'expense':
            form.fields['cate_choices'].choices = Cost.EXPENSE_CATEGORIES

        if form.is_valid():
            print("Form is valid")
            cost = form.save(commit=False)
            persian_date = form.cleaned_data['date']  
            cost.date = persian_date
            cost.child = child
            cost.save()
            messages.success(request, "Cost saved successfully.")
            return redirect('costs', child_id=child_id)
        else:
            print("Form errors:", form.errors)

    else:
        initial_type = request.GET.get('type', 'expense')
        form = costsForm(initial={'type': initial_type})
 
        if initial_type == 'income':
            form.fields['cate_choices'].choices = Cost.INCOME_CATEGORIES
        else:
            form.fields['cate_choices'].choices = Cost.EXPENSE_CATEGORIES

    for cost in costs:
        cost.persian_date = cost.date 
    return render(
        request,
        'cashflow/costs.html',
        {
            'form':form,
            'costs': costs,
            'child': child, 
            'persian_today': persian_today.strftime('%Y-%m-%d'),
            'filter_option': filter_option,
            
        },
    )



#.........................................................................................................................

def child_login(request):
    if request.method=="POST":
        form=ChildLoginForm(request.POST)
        print("IN POOOOSSSSTTTTTTTTT")
        print("FORM VALID: ", form.is_valid)
        if form.is_valid():
            print("THE FOOORRMMM ISS VAALLIIDD")
            email=form.cleaned_data["email"]
            password=form.cleaned_data["password"]
        
            try:
                child=Child.objects.get(email=email)

                if check_password(password, child.password):
                    request.session['user_type'] = 'Child'
                    request.session['user_id'] = child.id
                    return redirect('child_dashboard', child.id)
                    # return redirect('costs', child.id)
                else:
                    return render(request, 'cashflow/child_login.html', {
                        'form':form,
                        'error': "رمز عبور اشتباه است. لطفاً دوباره تلاش کنید."
                    })
            except Child.DoesNotExist:
                return render(request, 'cashflow/child_login.html', {
                    'form':form,
                    'error': "هیچ کاربری با این ایمیل وجود ندارد. لطفاً ثبت نام کنید."
                })
        else:
            return render(request, 'cashflow/child_login.html', {'form':form})
    else:
        print("NOTT IN POOOOSSSSTTTTTTTTT")
        form=ChildLoginForm()
    return render(request, 'cashflow/child_login.html', {
        'form':form
    })

#.........................................................................................................................

def details(request, child_id):
    child=get_object_or_404(Child, id=child_id)
    children=child.parent.children.all()
    user_type = request.session.get('user_type') 
    user_id = request.session.get('user_id') 

    needs = Cost.objects.filter(child=child, type='expense', cate_choices='needs').order_by('-date')
    wants = Cost.objects.filter(child=child, type='expense', cate_choices='wants').order_by('-date')
    other=Cost.objects.filter(child=child, type='expense', cate_choices='else').order_by('-date')

    print("chilldren: ",children)
    
    total_needs = Cost.objects.filter(child=child, type='expense', cate_choices='needs').aggregate(Sum('amount'))['amount__sum'] or 0
    total_wants = Cost.objects.filter(child=child, type='expense', cate_choices='wants').aggregate(Sum('amount'))['amount__sum'] or 0
    total_other = Cost.objects.filter(child=child, type='expense', cate_choices='else').aggregate(Sum('amount'))['amount__sum'] or 0

    # username=child.parent.username
    # print("usermameeeeeeeeeeeeeeeeeeeeeeee:", username)

    # parent=Parent.objects.filter(username=username).first()
    if user_type == 'Parent':
        # user = Parent.objects.get(id=user_id)
        is_parent = True
    else :
        # user = Child.objects.get(id=user_id)
        is_parent = False
        
    print("IS_PARENT: ", is_parent, user_type)

    context={
        'child':child,
        'needs': needs,
        'wants': wants,
        'other':other,
        'children':children,
        'total_needs':total_needs,
        'total_wants':total_wants,
        'total_other':total_other,
        'is_parent': is_parent,
    }

    return render(request, "cashflow/details.html", context)


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
    






    