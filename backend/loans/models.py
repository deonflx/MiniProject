from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

class Loan(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=160)
    interest_rate = models.DecimalField(max_digits=6, decimal_places=2)
    max_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tenure_months = models.PositiveIntegerField()
    description = models.TextField()

class KYCRecord(models.Model):
    aadhaar_no = models.CharField(max_length=12, unique=True)
    dob = models.DateField()
    full_name = models.CharField(max_length=200)

class CreditRecord(models.Model):
    pan = models.CharField(max_length=10, unique=True)
    score = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)
    emi = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stage = models.CharField(max_length=30, default="sales")
    profile = models.JSONField(default=dict)
    state = models.JSONField(default=dict)
    logs = models.JSONField(default=list)
