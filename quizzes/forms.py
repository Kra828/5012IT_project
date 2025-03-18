from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .models import Quiz, Question, Choice, StudentAnswer

class QuizForm(forms.ModelForm):
    """测验表单"""
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'course', 'time_limit', 'start_time', 'end_time', 'is_published']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class QuestionForm(forms.ModelForm):
    """问题表单"""
    class Meta:
        model = Question
        fields = ['question_text']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'placeholder': '请输入问题内容...'}),
        }

class ChoiceForm(forms.ModelForm):
    """选项表单"""
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']
        widgets = {
            'choice_text': forms.TextInput(attrs={'placeholder': '请输入选项内容...'}),
        }

# 创建选择题的选项的内联表单集
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    max_num=4,
    min_num=4,
    validate_min=True,
    validate_max=True,
    can_delete=False
)

class StudentAnswerForm(forms.ModelForm):
    """学生答案表单"""
    class Meta:
        model = StudentAnswer
        fields = ['selected_choice']
        widgets = {
            'selected_choice': forms.RadioSelect()
        }
    
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
        if question:
            self.fields['selected_choice'].queryset = question.choices.all()
            self.fields['selected_choice'].empty_label = None

    def clean(self):
        """表单整体验证"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and end_time < start_time:
            self.add_error('end_time', _('End time must be after start time.'))
            
        return cleaned_data 