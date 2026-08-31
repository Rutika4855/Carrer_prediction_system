from django.db import models
from django.contrib.auth.models import User

class Career(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.TextField()
    courses = models.TextField()
    salary_range = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Question(models.Model):
    CATEGORY_CHOICES = [
        ('IT', 'IT'),
        ('Commerce', 'Commerce'),
        ('Medical', 'Medical'),
        ('Arts', 'Arts'),
    ]
    question_text = models.CharField(max_length=255)
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.question_text

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    marks = models.IntegerField(default=0)
    interest = models.CharField(max_length=255, default='General')
    skills = models.TextField(blank=True, default='') # To store comma-separated skills
    predicted_career = models.ForeignKey(Career, on_delete=models.SET_NULL, null=True, blank=True)
    report_email = models.EmailField(blank=True, null=True, help_text="Email address to send career reports to (optional)")

    def __str__(self):
        return self.user.username
