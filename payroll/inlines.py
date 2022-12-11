from django.contrib.admin import TabularInline

from . import models


class WorkingDayInline(TabularInline):
    model = models.WorkingDay
    readonly_fields = ['updated_at', 'created_at']
    min_num = 0
    extra = 0
