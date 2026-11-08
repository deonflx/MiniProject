# Generated migration for security improvements (P0 & P2)

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0001_initial'),
    ]

    operations = [
        # KYCRecord updates (P0)
        migrations.AddField(
            model_name='kycrecord',
            name='aadhaar_hash',
            field=models.CharField(db_index=True, default='', max_length=64, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kycrecord',
            name='aadhaar_last4',
            field=models.CharField(default='', max_length=4),
        ),
        migrations.AlterField(
            model_name='kycrecord',
            name='aadhaar_no',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        # CreditRecord updates (P2)
        migrations.AddField(
            model_name='creditrecord',
            name='pan_hash',
            field=models.CharField(db_index=True, default='', max_length=64, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='creditrecord',
            name='encrypted_pan',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='creditrecord',
            name='pan',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
