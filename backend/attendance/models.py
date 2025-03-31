from django.db import models


class Attendance(models.Model):
    invitation = models.OneToOneField('invitations.Invitation', on_delete=models.CASCADE, related_name='attendance')
    has_attended = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.invitation.guest_name} - {'Attended' if self.has_attended else 'Not Attended'}"