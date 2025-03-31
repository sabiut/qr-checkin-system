from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('invitations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('has_attended', models.BooleanField(default=False)),
                ('check_in_time', models.DateTimeField(blank=True, null=True)),
                ('check_in_notes', models.TextField(blank=True)),
                ('invitation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='invitations.invitation')),
            ],
        ),
    ]