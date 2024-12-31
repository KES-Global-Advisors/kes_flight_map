from django.contrib import admin
from .models import Program, Workstream, Milestone, Task

# Register your models here.
admin.site.register(Program)
admin.site.register(Workstream)
admin.site.register(Milestone)
admin.site.register(Task)