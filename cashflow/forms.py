from django import forms
import jdatetime
from .models import Parent, Child, Cost, Goals
from django.core.exceptions import ValidationError
#...................................................................................................



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
        







