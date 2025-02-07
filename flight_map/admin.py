from django.contrib import admin
from .models import Strategy,StrategicGoal, Program, Workstream, Milestone, Activity

# Register your models here.
admin.site.register(Strategy)
admin.site.register(StrategicGoal)
admin.site.register(Program)
admin.site.register(Workstream)
admin.site.register(Milestone)
# @admin.register(Milestone)
# class MilestoneAdmin(admin.ModelAdmin):
#     list_display = ('name', 'workstream', 'deadline', 'current_progress')
#     readonly_fields = ('current_progress', 'timeframe_category')
admin.site.register(Activity)