import datetime
import calendar

from django.contrib import admin
from django.db.models import QuerySet, Q, Sum, F

from . import models
from . import inlines


# Get the first and last day of the current month
def get_month_days(today=datetime.date.today()):
    _, last_day = calendar.monthrange(today.year, today.month)
    return last_day


def convert_day_to_date(day, today=datetime.date.today()):
    return datetime.date(day=day, month=today.month, year=today.year)


def get_saturdays():
    last_day = get_month_days()
    return [convert_day_to_date(i + 1) for i in range(last_day) if convert_day_to_date(i + 1).weekday() == 5]


def calculate_work_hours(employee):
    work_day = employee.aggregate(over_time_sum=Sum(F('hours') - 8, default=0))
    return 8 * len(employee), work_day.get('over_time_sum', 0)


def calculate_period_wage(hour_in, hour_out, rate_in, rate_out, wage):
    return hour_in * rate_in * wage + hour_out * rate_out * wage


# Register your models here.
@admin.register(models.Employee)
class AdminEmployee(admin.ModelAdmin):
    actions = ['make_published']
    autocomplete_fields = ['monthly_salary']
    search_fields = ['name__istartswith', 'name__istartswith']
    readonly_fields = ['created_at', 'updated_at', 'monthly_salary']
    inlines = [inlines.WorkingDayInline]
    list_select_related = ['monthly_salary']

    def link_wage_to_employee(self, employee, salary, hours_in, hours_out):
        monthly_salary = models.MonthlySalary(hours_in=hours_in, hours_out=hours_out,
                                              total_hours=employee.total_hours,
                                              total_payment=salary, employee_name=employee.name,
                                              employee_surname=employee.surname)
        monthly_salary.save()
        employee.monthly_salary = monthly_salary
        employee.save()

    @admin.action(description='Generate salaries')
    def make_published(self, request, queryset: QuerySet):
        # Get all holidays
        official_off_days = models.OffDay.objects.all().values('date')
        today = datetime.date.today()
        # Get all workings hours for all employees during this month
        queryset = queryset.filter(workingday__date__month=today.month,
                                   workingday__date__year=today.year).annotate(total_hours=Sum('workingday__hours'))

        # Get all saturdays of the month
        month_saturdays = get_saturdays()
        # Calculate working hours by days off, weekend, extra hours
        for employee in queryset:
            # Calculate working hours
            day_off_in, day_off_out = calculate_work_hours(employee.workingday_set.filter(date__in=official_off_days))
            weekend_in, weekend_out = calculate_work_hours(
                employee.workingday_set.filter(date__in=month_saturdays).exclude(date__in=official_off_days))
            base_in, base_out = calculate_work_hours(employee.workingday_set.filter(~Q(date__in=official_off_days),
                                                                                    ~Q(date__in=month_saturdays)))
            # Calculate wage
            wage = calculate_period_wage(day_off_in, day_off_out, 1.5, 2, employee.wage)
            wage = wage + calculate_period_wage(weekend_in, weekend_out, 1.25, 1.5, employee.wage)
            wage = wage + calculate_period_wage(base_in, base_out, 1, 1.25, employee.wage)
            self.link_wage_to_employee(employee, wage, day_off_in + weekend_in + base_in,
                                       day_off_out + weekend_out + base_out)


@admin.register(models.WorkingDay)
class AdminWorkingDay(admin.ModelAdmin):
    autocomplete_fields = ['employee']
    list_select_related = ['employee']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(models.OffDay)
class AdminOffDay(admin.ModelAdmin):
    list_display = ['date', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(models.MonthlySalary)
class AdminMonthlySalary(admin.ModelAdmin):
    search_fields = ['hours_in', 'hours_out']
