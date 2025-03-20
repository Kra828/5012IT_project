from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm

User = get_user_model()

class CustomSignupForm(SignupForm):
    """Custom signup form with default user type as student"""
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email address is already in use. Please use a different email address."))
        return email
    
    def save(self, request):
        # Set user type to student by default
        user = super().save(request)
        user.user_type = 'student'  # Always set to student
        user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Base user profile form"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class TeacherProfileForm(UserProfileForm):
    """Teacher profile form"""
    class Meta(UserProfileForm.Meta):
        fields = UserProfileForm.Meta.fields + ['specialization']

class StudentProfileForm(UserProfileForm):
    """Student profile form"""
    class Meta(UserProfileForm.Meta):
        fields = UserProfileForm.Meta.fields + ['student_id'] 