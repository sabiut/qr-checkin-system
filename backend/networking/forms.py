from django import forms
from .models import NetworkingProfile


class NetworkingProfileForm(forms.ModelForm):
    """Form for networking profile updates with validation"""
    
    class Meta:
        model = NetworkingProfile
        fields = ['company', 'industry', 'interests', 'bio', 'visible_in_directory', 'allow_contact_sharing']
        widgets = {
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company name',
                'maxlength': 100
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Technology, Healthcare, Finance',
                'maxlength': 100
            }),
            'interests': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. AI, Marketing, Startups (comma separated)',
                'maxlength': 500
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control textarea',
                'placeholder': 'Tell others about yourself and what you do...',
                'rows': 4,
                'maxlength': 1000
            }),
            'visible_in_directory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_contact_sharing': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'company': 'Company',
            'industry': 'Industry',
            'interests': 'Interests',
            'bio': 'Bio',
            'visible_in_directory': 'Show my profile in the attendee directory',
            'allow_contact_sharing': 'Allow others to see my contact information when we connect'
        }
    
    def clean_company(self):
        """Validate company field"""
        company = self.cleaned_data.get('company')
        if company and len(company) > 100:
            raise forms.ValidationError("Company name cannot exceed 100 characters.")
        return company
    
    def clean_bio(self):
        """Validate bio field"""
        bio = self.cleaned_data.get('bio')
        if bio and len(bio) > 1000:
            raise forms.ValidationError("Bio cannot exceed 1000 characters.")
        return bio
    
    def clean_interests(self):
        """Validate and clean interests field"""
        interests = self.cleaned_data.get('interests')
        if interests and len(interests) > 500:
            raise forms.ValidationError("Interests cannot exceed 500 characters.")
        return interests