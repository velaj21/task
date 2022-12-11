import datetime

from django.db import models
from django.utils.timezone import now


# Create your models here.
class MonthlySalary(models.Model):
    employee_name = models.CharField(max_length=125)
    employee_surname = models.CharField(max_length=125)
    hours_in = models.PositiveSmallIntegerField()
    hours_out = models.PositiveSmallIntegerField()
    total_hours = models.PositiveSmallIntegerField()
    total_payment = models.FloatField()

    def __str__(self):
        return f'{self.total_payment} {self.total_hours}'


class Employee(models.Model):
    name = models.CharField(max_length=125)
    surname = models.CharField(max_length=125)
    wage = models.FloatField()
    created_at = models.DateField(default=now)
    updated_at = models.DateField(auto_now=True)
    monthly_salary = models.ForeignKey(MonthlySalary, on_delete=models.SET_NULL,
                                       null=True, blank=True)

    def __str__(self):
        return f'{self.name} {self.surname}'


class WorkingDay(models.Model):
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField()
    hours = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateField(default=now)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.date} {self.hours}'


class OffDay(models.Model):
    date = models.DateField()
    created_at = models.DateField(default=now)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f'{self.date}'
