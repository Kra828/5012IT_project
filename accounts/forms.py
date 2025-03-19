from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm

User = get_user_model()

class CustomSignupForm(SignupForm):
    """自定义注册表单，添加用户类型选择"""
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label=_('I am a'),
        initial='student'
    )
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email address is already in use. Please use a different email address."))
        return email
    
    def save(self, request):
        # 保存用户类型
        user = super().save(request)
        user.user_type = self.cleaned_data['user_type']
        user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """用户个人资料基础表单"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class TeacherProfileForm(UserProfileForm):
    """教师个人资料表单"""
    class Meta(UserProfileForm.Meta):
        fields = UserProfileForm.Meta.fields + ['specialization']

class StudentProfileForm(UserProfileForm):
    """学生个人资料表单"""
    class Meta(UserProfileForm.Meta):
        fields = UserProfileForm.Meta.fields + ['student_id'] 