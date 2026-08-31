from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student

class StudentRegistrationForm(UserCreationForm):
    report_email = forms.EmailField(required=False, help_text="Email address to send career reports to (optional)", label="Report Email")
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=True)
        if commit:
            student, created = Student.objects.get_or_create(user=user)
            if created:
                student.marks = 0
                student.interest = 'General'
                student.skills = ''
            # Prioritize the explicitly provided report_email, otherwise default to user's primary email
            # Only set if a value was actually submitted for report_email in the form
            if 'report_email' in self.cleaned_data and self.cleaned_data['report_email']:
                student.report_email = self.cleaned_data['report_email']
            elif created: # Only if student was just created and no report_email was provided, use user.email
                student.report_email = user.email
            student.save()
        return user

class StudentUpdateForm(forms.ModelForm):
    INTEREST_CHOICES = [
        ('IT', 'IT'),
        ('Commerce', 'Commerce'),
        ('Medical', 'Medical'),
        ('Arts', 'Arts'),
    ]
    interest = forms.ChoiceField(choices=INTEREST_CHOICES, widget=forms.RadioSelect)
    skills = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), help_text="Enter skills separated by commas (e.g., Python, Communication, Teamwork)")

    class Meta:
        model = Student
        fields = ['marks', 'interest', 'skills']
