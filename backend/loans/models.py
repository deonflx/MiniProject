import re
from django.contrib.auth.models import AbstractUser
from django.db import models
from .crypto import encrypt_field, decrypt_field, hash_identity

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
    # P0: Aadhaar is stored as a salted HMAC-SHA256 hash. Plaintext 12 digits are never retained.
    aadhaar_hash = models.CharField(max_length=64, unique=True, db_index=True)
    aadhaar_last4 = models.CharField(max_length=4, default="")
    aadhaar_no = models.CharField(max_length=12, blank=True, null=True)
    dob = models.DateField()
    full_name = models.CharField(max_length=200)

    def set_aadhaar(self, raw_aadhaar: str):
        cleaned = re.sub(r"\D", "", str(raw_aadhaar))
        self.aadhaar_hash = hash_identity(cleaned)
        self.aadhaar_last4 = cleaned[-4:] if len(cleaned) >= 4 else ""
        self.aadhaar_no = None  # Ensure raw number is never saved

    def save(self, *args, **kwargs):
        if self.aadhaar_no and not self.aadhaar_hash:
            self.set_aadhaar(self.aadhaar_no)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} (Aadhaar: XXXX-XXXX-{self.aadhaar_last4})"

class CreditRecord(models.Model):
    # P2: PAN is encrypted with Fernet (AES-128-CBC) and searched via HMAC-SHA256 hash
    pan_hash = models.CharField(max_length=64, unique=True, db_index=True)
    encrypted_pan = models.TextField(blank=True, default="")
    pan = models.CharField(max_length=10, blank=True, null=True)
    score = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)
    emi = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def set_pan(self, raw_pan: str):
        cleaned = re.sub(r"\s", "", str(raw_pan)).upper()
        self.pan_hash = hash_identity(cleaned)
        self.encrypted_pan = encrypt_field(cleaned)
        self.pan = None  # Ensure plaintext PAN is never saved

    def get_decrypted_pan(self) -> str:
        if self.encrypted_pan:
            return decrypt_field(self.encrypted_pan)
        return self.pan or ""

    def save(self, *args, **kwargs):
        if self.pan and not self.pan_hash:
            self.set_pan(self.pan)
        elif self.encrypted_pan and not self.pan_hash:
            self.pan_hash = hash_identity(decrypt_field(self.encrypted_pan))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Credit Score: {self.score})"

class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stage = models.CharField(max_length=30, default="sales")
    profile = models.JSONField(default=dict)
    state = models.JSONField(default=dict)
    logs = models.JSONField(default=list)
