import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('guest_name', models.CharField(max_length=255)),
                ('guest_email', models.EmailField(blank=True, max_length=254)),
                ('guest_phone', models.CharField(blank=True, max_length=20)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='qrcodes/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='events.event')),
            ],
        ),
    ]