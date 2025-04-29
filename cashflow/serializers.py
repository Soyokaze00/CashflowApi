from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import Parent, Child, Cost
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.cache import cache
import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import IsAuthenticated



def send_code_to_email(email, code, is_child=False):
    subject = 'کد تایید ثبت‌ نام شما در کش‌فلو'
    message = f'!سلام\n\nCode: {code}'
    from_email = settings.EMAIL_HOST_USER  
    recipient_list = [email]

    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False  
        )
        print(f"✅ Sent {'child' if is_child else 'parent'} code {code} to {email}")
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, email):
        
        try:
            validate_email(email)
            
        except ValidationError:
            raise serializers.ValidationError("فرمت ایمیل اشتباه است.")
        
    
        if getattr(self, 'is_child', False):
            if Child.objects.filter(email=email).exists():
                raise serializers.ValidationError("این ایمیل قبلاً برای فرزند ثبت شده است")
        else:
            if Parent.objects.filter(email=email).exists():
                raise serializers.ValidationError("این ایمیل قبلاً برای والد ثبت شده است")
        return email
    
    def create(self, validated_data):
        email = validated_data['email']
        is_child = getattr(self, 'is_child', False)
        prefix = "child_verify_" if is_child else "verify_"
        code = f"{random.randint(100000, 999999)}"
        
        cache.set(f"{prefix}{email}", code, 300)
        send_code_to_email(email, code, is_child)
        return {'email': email}
    

class ParentVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    
    def validate(self, data):
        cached_code = cache.get(f"verify_{data['email']}")
        print("THISS ISS CACHEEDD_COODEE:\n", cached_code)
        print("THISSS ISS COODEEE:\n", data['code'])
        if cached_code != data['code']:
            raise serializers.ValidationError({"error": "کد تایید نامعتبر است"})
        return data
    def create(self, validated_data):
        # No actual creation needed - just return the validated data
        return validated_data
    
    
class ParentSignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        print("Session Data: ", self.context['request'].session.keys())  # Print all session keys
        print("Verified Email: ", self.context['request'].session.get('verified_email')) 
        if Parent.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("این نام کاربری موجود است.")
        
        if not self.context['request'].session.get('verified_email'):
            raise serializers.ValidationError("لطفا ابتدا ایمیل خود را تایید کنید")
        
        return data
    
    
    
    def create(self, validated_data):
        email = self.context['request'].session.get('verified_email')

        parent = Parent.objects.create(
            username=validated_data['username'],
            password=make_password(validated_data['password']),
            email=email
        )

        self.context['request'].session.pop('verified_email', None)
        
        return parent


class ParentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        try:
            parent = Parent.objects.get(email=data['email'])
        except Parent.DoesNotExist:
            raise serializers.ValidationError("چنین ایمیلی وجود ندارد")
        
        if not check_password(data['password'], parent.password):
            raise serializers.ValidationError("رمز عبور اشتباه است.")
        
        data['user'] = parent
        return data
 

class ChildVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    
    def validate(self, data):
        cached_code = cache.get(f"child_verify_{data['email']}")
        print("THISS ISS CACHEEDD_COODEE:\n", cached_code)
        print("THISSS ISS COODEEE:\n", data['code'])
        if cached_code != data['code']:
            raise serializers.ValidationError({"error": "کد تایید نامعتبر است"})
        return data
    def create(self, validated_data):
        # No actual creation needed - just return the validated data
        return validated_data


class ChildSignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        
        request = self.context.get('request')
        
        # 1. Verify token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            raise serializers.ValidationError("لطفا ابتدا به عنوان والد وارد شوید")
        
        token = auth_header.split(' ')[1]
        parent_id = cache.get(f"parent_token_{token}")
        
        if not parent_id:
            raise serializers.ValidationError("احراز هویت نامعتبر - لطفا دوباره وارد شوید")

        if not request.session.get('child_verified_email'):
            raise serializers.ValidationError("لطفا ابتدا ایمیل فرزند را تایید کنید")
        
        
        if Child.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("این نام کاربری موجود است.")
        
        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            raise serializers.ValidationError("حساب والد یافت نشد")
        
        
        
        return {
            **data,
            'email': request.session['child_verified_email'],
            'parent': parent 
        }
    
    def create(self, validated_data):
     
        child = Child.objects.create(
            username=validated_data['username'],
            password=make_password(validated_data['password']),
            email=validated_data['email'],
            parent=validated_data['parent']
        )
        
        # Clear session data
        self.context['request'].session.pop('child_verified_email', None)
        
        return child
    

class ChildLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            child = Child.objects.get(email=data['email'])
        except Child.DoesNotExist:
             raise serializers.ValidationError("چنین ایمیلی وجود ندارد")

        if not check_password(data['password'], child.password):
            raise serializers.ValidationError("رمز عبور اشتباه است.")

        data['user'] = child
        return data
    
    

    
    
    
class CostSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= Cost
        fields=['id', 'amount', 'cate_choices', 'description', 'date', 'type', 'child']
        read_only_fields=['child']
        
    def validate(self, data):
        request = self.context.get('request')
        
        # 1. Verify Token from header 
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            raise serializers.ValidationError("ابتدا باید وارد شوید.")
        
        token = auth_header.split(' ')[1]
        print("THISSS ISSS THE STOREDDD TOOKEENNSERIALIZER: \n", token)
        child_id_from_token = cache.get(f"child_token_{token}")
        print("THIS ISS THEE CHILD_IIDDD FROM THE TOKEN:\n", child_id_from_token)
        
        if not child_id_from_token:
             raise serializers.ValidationError("احراز هویت نامعتبر - لطفا دوباره وارد شوید")
         
        self.context['child_id_from_token'] = child_id_from_token
        
        return data 
        
    def create(self, validated_data):
        try:
            child_id = self.context.get('child_id_from_token')
            if not child_id:
                raise serializers.ValidationError("No child associated with this token")
                
            child = Child.objects.get(id=child_id)
            
            return Cost.objects.create(
                child=child,
                **validated_data
            )
            
        except Child.DoesNotExist:
            raise serializers.ValidationError("Child not found")
        except Exception as e:
            raise serializers.ValidationError(str(e))