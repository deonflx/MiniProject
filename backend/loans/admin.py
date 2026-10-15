from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Loan, KYCRecord, CreditRecord, ChatSession

admin.site.register(User, UserAdmin)
admin.site.register(Loan)
admin.site.register(KYCRecord)
admin.site.register(CreditRecord)
admin.site.register(ChatSession)
