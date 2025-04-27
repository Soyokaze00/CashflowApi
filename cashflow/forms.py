from django import forms
import jdatetime
from .models import Parent, Child, Cost, Goals
from django.core.exceptions import ValidationError
#...................................................................................................

class parentSignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور خود را وارد کنید.'}),
        error_messages={'required': 'لطفاً رمز عبور خود را وارد کنید.'},
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'ایمیل خود را وارد کنید',
            'title': 'لطفاً یک ایمیل معتبر وارد کنید.',
        }),
        error_messages={
            'required': 'لطفاً ایمیل خود را وارد کنید.',
            'invalid': 'ایمیل وارد شده معتبر نیست.',
        }
    )
    username = forms.CharField(
        error_messages={
            'required': 'نام کاربری الزامی است.',
        }
    )
    class Meta:
        model=Parent
        fields = ['username', 'password', 'email']
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Child.objects.filter(username=username).exists():
            raise forms.ValidationError('کاربری با این نام کاربری قبلاً ثبت شده است.')
        return username
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("لطفاً ایمیل خود را وارد کنید.")
        return email

    
#......................................................................................................

class costsForm(forms.ModelForm):

    date = forms.CharField(
        initial=jdatetime.date.today().strftime('%Y-%m-%d'),
        widget=forms.TextInput(attrs={'dir': 'rtl', 'id': 'id_date'}),
        required=False
        
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')
        try:
            print("Raw date input:", date)  
            jdatetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("فرمت تاریخ وارد شده اشتباه است!")    
        return date

    class Meta:
        model=Cost
        fields = ['amount', 'cate_choices', 'description', 'date', 'type']
        error_messages = {
            'amount': {'required': 'لطفا یک مبلغی را وارد کنید😊'},
            'description': {'required': 'لطفا توضیحات را وارد کنید😊'},
            
        }
        
            
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


            type_value = self.initial.get('type', 'expense')
            if type_value == 'income':
                self.fields['cate_choices'].choices = Cost.INCOME_CATEGORIES
            else:
                self.fields['cate_choices'].choices = Cost.EXPENSE_CATEGORIES


            self.fields['type'].choices = Cost.MONEY_CHOICES
            # self.fields['type'].initial = 'expense' 
            # self.fields['cate_choices'].initial = 'food' 

        # def clean(self):
        #     cleaned_data = super().clean()
        #     type_value = cleaned_data.get('type')
        #     cate_choice = cleaned_data.get('cate_choices')

        #     if type_value == 'income':
        #         valid_choices = [choice[0] for choice in Cost.INCOME_CATEGORIES]
        #     else:
        #         valid_choices = [choice[0] for choice in Cost.EXPENSE_CATEGORIES]

        #     if cate_choice not in valid_choices:
        #         raise forms.ValidationError({'cate_choices': "Invalid choice for the selected type."})

        #     return cleaned_data



#.....................................................................................................

class goalsForm(forms.ModelForm):
    class Meta:
        model = Goals
        fields = ['goal', 'goal_amount', 'savings']
        error_messages = {
            'goal': {'required': 'لطفا این فیلد را خالی نزارین😊'},
            'goal_amount': {'required': 'لطفا این فیلد را خالی نزارین😊'},
            'savings' : {'required': 'لطفا این فیلد را خالی نزارین😊'},
        }

        def clean_current_amount(self):
            goal_amount = self.cleaned_data.get('goal_amount')
            savings = self.cleaned_data.get('savings')
            if goal_amount and savings and goal_amount > savings:
                raise forms.ValidationError('مقدار پس‌انداز نمی‌تواند بیشتر از مبلغ هدف باشد!')
            return goal_amount
    

#.....................................................................................................

class GoalUpdateForm(forms.ModelForm):
    class Meta:
        model = Goals
        fields = ['savings']
        


#......................................................................................................

class ChildSignupForm(forms.ModelForm):
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور خود را وارد کنید.'}),
        error_messages={'required': 'لطفاً رمز عبور خود را وارد کنید.'},
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'ایمیل خود را وارد کنید',
            'title': 'لطفاً یک ایمیل معتبر وارد کنید.',
        }),
        error_messages={
            'required': 'لطفاً ایمیل خود را وارد کنید.',
            'invalid': 'ایمیل وارد شده معتبر نیست.',
        }
    )
    # verification_code = forms.CharField(
    #     error_messages={
    #         'required': 'کد تأیید الزامی است.',
    #     }
    # )
    username = forms.CharField(
        error_messages={
            'required': 'نام کاربری الزامی است.',
        }
    )
    class Meta:
        model=Child
        fields = ['username', 'password', 'email']
    
    
    # class Meta:
    #     model = Child
    #     fields = ['username', 'password',]
    #     error_messages = {
    #         'username': {
    #             'required': 'لطفاً یک نام کاربری وارد کنید.',
    #         },
    #         'password': {
    #             'required': 'لطفاً رمز عبور خود را وارد کنید.',
    #         }
    #     }

    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if Child.objects.filter(username=username).exists():
    #         raise forms.ValidationError('کاربری با این نام کاربری قبلاً ثبت شده است.')
    #     return username

#......................................................................................................

class ParentLoginForm(forms.Form):
    email = forms.CharField(
        required=True,
        label='Email',
        error_messages={'required': 'لطفاً ایمیل خود را وارد کنید.'}
        )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label='Password',
        error_messages={'required': 'لطفاً رمز عبور خود را وارد کنید.'}
    )

#......................................................................................................
    
class ChildLoginForm(forms.Form):
    email = forms.CharField(
        required=True,
        label='Email',
        error_messages={'required': 'لطفاً ایمیل خود را وارد کنید.'}
        )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label='Password',
        error_messages={'required': 'لطفاً رمز عبور خود را وارد کنید.'}
    )

        




