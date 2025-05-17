from django.contrib import admin
from  .models import Parent, Child, Cost, Goals

# Register your models here.


class ParentAdmin(admin.ModelAdmin):
    list_display=('id', 'username', 'email')


class ChildAdmin(admin.ModelAdmin):
    list_display=('id', 'username', 'parent__username', 'email')
    list_filter = ('parent', )


class CostAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'cate_choices', 'type', 'date', 'child__username', 'child__parent__username') 
    list_filter = ('child__username', 'type', 'cate_choices')  
    search_fields = ('cate_choices', 'description', 'child__username', 'id')  
    ordering = ('-date',) 

class GoalAdmin(admin.ModelAdmin):
    list_display=('id', 'goal', 'savings', 'goal_amount', 'child__username')
    list_filter = ('child__username',)

admin.site.register(Parent, ParentAdmin)
admin.site.register(Child, ChildAdmin)
admin.site.register(Cost, CostAdmin)
admin.site.register(Goals, GoalAdmin)


