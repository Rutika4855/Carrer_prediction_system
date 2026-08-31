from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Import Django's default auth views

app_name = 'career'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('entrance-exams/', views.entrance_exams, name='entrance_exams'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('aptitude-test/', views.aptitude_test, name='aptitude_test'),
    path('aptitude-test/<str:category_name>/', views.aptitude_test, name='aptitude_test_category'),
    path('send-report/', views.send_report, name='send_report'),
]
