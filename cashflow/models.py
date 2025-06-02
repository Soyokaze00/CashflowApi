import random
import string
from django.db import models
from django.contrib.auth.hashers import make_password
import jdatetime
# from django.utils.timezone import now
# from django.contrib.auth.models import User
# from django.core.mail import send_mail



#.............................................................................................................................................................

class Parent(models.Model):
    username=models.CharField(max_length=20, unique=True)
    password=models.CharField(max_length=128)
    email = models.EmailField(unique=True) 

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password=make_password(self.password)
        super().save(*args, **kwargs)

    def is_parent(self):
        return True
   
    def __str__(self):
        return f"{self.username} "
    
#.............................................................................................................................................................

class Child(models.Model):
    username=models.CharField(max_length=20, unique=True)
    password=models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    parent=models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password=make_password(self.password)
        super().save(*args, **kwargs)

    def is_parent(self):
        return False

    def __str__(self):
        return f"{self.username} || Created by Parent: {self.parent.username}"
        
#.............................................................................................................................................................

def get_persian_date():
        return jdatetime.date.today().strftime('%Y-%m-%d')

class Cost(models.Model):
    amount = models.DecimalField(max_digits=20, decimal_places=3 )
    date = models.CharField(max_length=10, default=get_persian_date)
    description = models.CharField(max_length=200, blank=False, null=False)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='costs')
    
    MONEY_CHOICES =[
        ('expense', 'برآمد'),
        ('income', 'درآمد')
    ]
    EXPENSE_CATEGORIES = [
        ('needs', 'نیازها'),
        ('wants', 'خواسته ها'), 
        ('else', 'سایر'),
        ('parent', 'والدین'),
        ('part_time_job', 'کار نیمه‌وقت'),
        ('other', 'دیگر'),
    ]
    INCOME_CATEGORIES = [
        ('parent', 'والدین'),
        ('part_time_job', 'کار نیمه‌وقت'),
        ('other', 'دیگر'),
    ]

    cate_choices=models.CharField(
        max_length=20,
        choices=EXPENSE_CATEGORIES,
        default='needs'
    )

    type = models.CharField(
        max_length=10, 
        choices=MONEY_CHOICES, 
        default='expense'
    ) 

    def __str__(self):
        return f"Cost: {self.amount} || {self.get_type_display()} || for: {self.cate_choices} || on {self.date} || for: {self.child.username} ||"
    
#.............................................................................................................................................................

class Goals(models.Model):
    goal = models.CharField(max_length=20)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=0)
    savings = models.DecimalField(max_digits=10, decimal_places=0)
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='goals' )
    IN_PROGRESS = 'جاری'
    COMPLETED = 'کامل'
    STATUS_CHOICES = [
        (IN_PROGRESS, 'جاری'),
        (COMPLETED, 'کامل'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=IN_PROGRESS)


    def __str__(self):
        return f" {self.goal} || {self.goal_amount} || {self.savings} || {self.status} || for child: {self.child.username}"
    