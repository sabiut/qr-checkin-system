from django.db import migrations, models
import django.db.models.deletion


def set_default_owner(apps, schema_editor):
    """Set the first admin user as the owner of all existing events"""
    Event = apps.get_model('events', 'Event')
    User = apps.get_model('auth', 'User')
    
    # Try to find an admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # If no admin user exists, create a default one
    if not admin_user:
        admin_user = User.objects.create(
            username='admin',
            is_staff=True,
            is_superuser=True
        )
    
    # Set all existing events to be owned by this user
    for event in Event.objects.all():
        event.owner = admin_user
        event.save()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='auth.user'),
        ),
        migrations.RunPython(set_default_owner),
        migrations.AlterField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='auth.user'),
        ),
    ]