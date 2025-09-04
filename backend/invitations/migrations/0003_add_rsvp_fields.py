from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0002_invitation_ticket_format_invitation_ticket_html_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='rsvp_status',
            field=models.CharField(
                choices=[('PENDING', 'Pending'), ('ATTENDING', 'Attending'), ('DECLINED', 'Declined')],
                default='PENDING',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='invitation',
            name='rsvp_notes',
            field=models.TextField(blank=True, help_text='Additional notes from the guest (dietary requirements, etc.)'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='rsvp_timestamp',
            field=models.DateTimeField(blank=True, help_text='When the guest responded to the RSVP', null=True),
        ),
    ]