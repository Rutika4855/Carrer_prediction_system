import re
import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import Student, Career, Question
from .forms import StudentRegistrationForm, StudentUpdateForm, UserCreationForm
from django.contrib.auth.forms import AuthenticationForm


def predict_career(student):
    """
    Advanced rule-based career prediction logic.
    Strictly prioritizes careers that match the student's field of interest.
    """
    student_skills_list = [skill.strip().lower() for skill in student.skills.split(',') if skill.strip()]
    student_interest = student.interest.lower()

    all_careers = Career.objects.all()
    
    if not all_careers.exists():
        return None

    # Filter careers that belong to the student's interest stream
    eligible_careers = []
    
    # Mapping interest to keywords to ensure valid matches
    interest_keywords = {
        'it': ['it', 'software', 'developer', 'data scientist', 'computer', 'tech', 'ai', 'cloud', 'coding'],
        'commerce': ['accountant', 'finance', 'tax', 'audit', 'banking', 'commerce', 'ca', 'cfa', 'business'],
        'medical': ['doctor', 'pharmacist', 'biotech', 'medical', 'healthcare', 'biology', 'nurse', 'scientist'],
        'arts': ['graphic', 'design', 'arts', 'lawyer', 'journalist', 'writer', 'creative', 'psychologist']
    }
    
    keywords = interest_keywords.get(student_interest, [student_interest])

    for career in all_careers:
        career_text = (career.name + " " + career.description).lower()
        if any(keyword in career_text for keyword in keywords):
            eligible_careers.append(career)

    # If no specific match, fallback to all but scoring will favor interest
    if not eligible_careers:
        eligible_careers = list(all_careers)

    best_career = None
    max_score = -1

    for career in eligible_careers:
        score = 0
        career_name_lower = career.name.lower()
        career_description_lower = career.description.lower()
        
        # 1. Interest Match (Huge Weight)
        if any(keyword in career_name_lower for keyword in keywords):
            score += 500
        elif any(keyword in career_description_lower for keyword in keywords):
            score += 300
        
        # 2. Skills Match (Significant Weight)
        required_skills_list = [skill.strip().lower() for skill in career.required_skills.split(',') if skill.strip()]
        if required_skills_list:
            matched_skills = set(student_skills_list) & set(required_skills_list)
            score += len(matched_skills) * 100
            
            # Bonus for high match percentage
            match_ratio = len(matched_skills) / len(required_skills_list)
            if match_ratio >= 0.5:
                score += 150
        
        # 3. Marks (Tie-breaker/Bonus)
        if student.marks >= 75:
            score += 50
        elif student.marks >= 60:
            score += 25
            
        if score > max_score:
            max_score = score
            best_career = career
        elif score == max_score and best_career:
            # Alphabetical tie-break
            if career.name < best_career.name:
                best_career = career

    return best_career

def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST) # Use custom StudentRegistrationForm
        if form.is_valid():
            user = form.save()
            # Student object is created and report_email is set within StudentRegistrationForm.save()
            login(request, user)
            return redirect('career:dashboard')
    else:
        form = StudentRegistrationForm() # Use custom StudentRegistrationForm
    return render(request, 'career/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('career:dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'career/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('career:login')

def generate_roadmap(student, predicted_career):
    roadmap = []
    if not predicted_career:
        return roadmap

    career_name = predicted_career.name.lower()

    if 'accountant' in career_name or 'financial' in career_name or 'bank' in career_name:
        if 'chartered accountant' in career_name:
            roadmap = [
                'Step 1: Education (Complete B.Com and register for ICAI CA Foundation)',
                'Step 2: CA Intermediate (Clear both groups of Intermediate exams)',
                'Step 3: Articleship (Complete 3 years of practical training under a CA)',
                'Step 4: CA Final (Clear CA Final exams and become a member of ICAI)',
                'Step 5: Job Roles (Statutory Auditor, Tax Consultant, Finance Manager)'
            ]
        elif 'accountant' in career_name:
            roadmap = [
                'Step 1: Education (Complete B.Com, Learn Tally, GST, Income Tax, Basic Excel & Advanced Excel)',
                'Step 2: Certification (Tally Certification, GST Practitioner Course, MS Excel Certification)',
                'Step 3: Internship (Work under CA firm, Gain 1–2 years experience)',
                'Step 4: Job Roles (Junior Accountant, Accounts Executive, Tax Assistant)',
                'Step 5: Growth Path (Senior Accountant, Finance Manager, CFO (Long term))'
            ]
        else:
            roadmap = [
                'Step 1: Education (B.Com / BBA (Finance))',
                'Step 2: Skills (Learn Financial Modeling, Advanced Excel, Power BI)',
                'Step 3: Certification (CFA (Optional), NISM Certification)',
                'Step 4: Internship (Internship in Bank / Finance company)',
                'Step 5: Job Roles (Financial Analyst, Investment Analyst, Portfolio Manager)'
            ]
    elif 'software' in career_name or 'developer' in career_name or 'it' in career_name:
        if 'developer' in career_name:
            roadmap = [
                'Step 1: Learn Programming (Python / Java / C++, Data Structures)',
                'Step 2: Learn Web Development (HTML, CSS, JavaScript, Django / React)',
                'Step 3: Build 3–4 Projects',
                'Step 4: Internship & GitHub Portfolio',
                'Step 5: Apply for (Junior Developer, Backend Developer, Full Stack Developer)'
            ]
        elif 'data scientist' in career_name:
            roadmap = [
                'Step 1: Foundations (Python, Statistics, Mathematics)',
                'Step 2: Libraries (Pandas, NumPy, Scikit-learn)',
                'Step 3: Machine Learning Projects',
                'Step 4: Internship in Data Field',
                'Step 5: Job Roles (Data Analyst, ML Engineer, Data Scientist)'
            ]
        else:
            roadmap = [
                'Year 1 – Master a programming language',
                'Year 2 – Work on personal IT projects',
                'Year 3 – Gain experience through internships',
                'Year 4 – Specialization in an IT domain',
                'Year 5 – Lead IT projects'
            ]
    elif 'doctor' in career_name or 'medical' in career_name or 'pharmacist' in career_name:
        if 'doctor' in career_name:
            roadmap = [
                'Step 1: 12th Grade (PCB in 12th, Prepare for NEET)',
                'Step 2: MBBS Degree',
                'Step 3: Internship (Hospital)',
                'Step 4: MD / Specialization',
                'Step 5: Practice / Hospital Job'
            ]
        else:
            roadmap = [
                'Year 1 – Focus on Science fundamentals',
                'Year 2 – Healthcare internships/volunteering',
                'Year 3 – Pursue advanced medical studies',
                'Year 4 – Entry-level role in healthcare',
                'Year 5 – Specialization or research'
            ]
    elif 'graphic' in career_name or 'designer' in career_name or 'arts' in career_name:
        if 'graphic designer' in career_name:
            roadmap = [
                'Step 1: Learn Software (Photoshop, Illustrator, Canva)',
                'Step 2: UI/UX Basics',
                'Step 3: Build Portfolio',
                'Step 4: Freelancing / Internship',
                'Step 5: Job (Graphic Designer, UI Designer, Creative Head)'
            ]
        else:
            roadmap = [
                'Year 1 – Develop creative skills (e.g., writing, design, music)',
                'Year 2 – Build a portfolio or body of work',
                'Year 3 – Seek internships or entry-level positions',
                'Year 4 – Network and collaborate',
                'Year 5 – Establish as an expert in chosen Arts field'
            ]
    else:
        # Generic roadmap
        roadmap = [
            'Year 1 – Explore different fields of study',
            'Year 2 – Develop foundational skills',
            'Year 3 – Gain practical experience',
            'Year 4 – Identify specialization area',
            'Year 5 – Advance in chosen career path'
        ]
    return roadmap


def parse_abroad_opportunities(file_path):
    if not os.path.exists(file_path):
        return {}

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    opportunities = {}
    
    stream_sections = re.split(r'\s*(?:💻|📊|🧪|🎨)\s*(\w+\s+Stream)\s*', content)
    
    if len(stream_sections) > 1:
        it = iter(stream_sections[1:])
        for stream_name, section_content in zip(it, it):
            stream_name = stream_name.strip().replace(" Stream", "")
            
            opportunities[stream_name] = {}
            
            subsections = re.split(r'(?:📌|🌎)\s*([\w\s]+):\s*', section_content)
            
            if len(subsections) > 1:
                sub_it = iter(subsections[1:])
                for sub_name, sub_content in zip(sub_it, sub_it):
                    sub_name = sub_name.strip()
                    items = [line.strip() for line in sub_content.strip().split('\n') if line.strip()]
                    opportunities[stream_name][sub_name] = items

    return opportunities


@login_required
def dashboard(request):
    print(f"--- Dashboard View ---")
    print(f"Request User: {request.user.username} (Authenticated: {request.user.is_authenticated})")
    
    student, created = Student.objects.get_or_create(user=request.user, defaults={'marks': 0, 'interest': 'General', 'skills': ''})
    if created:
        print(f"Student object created for {request.user.username} with defaults.")
    else:
        print(f"Existing Student object retrieved for {request.user.username}.")
    print(f"Student ID: {student.id}, Interest: {student.interest}, Marks: {student.marks}, Skills: {student.skills}")
    
    predicted_career = student.predicted_career
    if predicted_career:
        print(f"Predicted Career from Student object: {predicted_career.name}")
    else:
        print("No Predicted Career stored in Student object.")
    required_skills_for_career = []
    missing_skills = []
    learning_platforms = {
        'Python': ['Coursera', 'Udemy', 'Codecademy'],
        'Java': ['Udemy', 'Pluralsight', 'edX'],
        'C++': ['Udemy', 'Coursera', 'GeeksforGeeks'],
        'SQL': ['Codecademy', 'Khan Academy', 'SQLZoo'],
        'Machine Learning': ['Coursera', 'edX', 'Fast.ai'],
        'Statistics': ['Coursera', 'Khan Academy'],
        'Communication': ['Coursera', 'LinkedIn Learning'],
        'Financial Management': ['edX', 'Coursera'],
        'Accounting': ['Coursera', 'ACA'],
        'Taxation': ['ClearTax', 'Udemy', 'ICAI Portal'],
        'Tally': ['Tally Education', 'Udemy'],
        'GST': ['GST Portal', 'ClearTax', 'Vskills'],
        'Biology': ['Khan Academy', 'Coursera', 'edX'],
        'Anatomy': ['Coursera', 'Kenhub'],
        'Pharmacology': ['Lecturio', 'Coursera'],
        # Add more skills and platforms as needed
    }

    # Career Suggestions based on Background
    career_suggestions_by_interest = {
        'Commerce': [
            'Accountant', 'Chartered Accountant (CA)', 'Financial Analyst',
            'Investment Banker', 'Tax Consultant', 'Auditor', 'Banking Officer'
        ],
        'IT': [
            'Software Developer', 'Web Developer', 'Data Scientist', 'Data Analyst',
            'AI Engineer', 'Cyber Security Analyst', 'Cloud Engineer'
        ],
        'Medical': [
            'Doctor', 'Pharmacist', 'Biotechnologist', 'Lab Technician',
            'Research Scientist', 'Nurse', 'Nutritionist'
        ],
        'Arts': [
            'Journalist', 'Content Writer', 'Graphic Designer', 'Lawyer',
            'Psychologist', 'Teacher', 'Event Manager'
        ],
        'General': []
    }

    suggested_careers = []
    # Get relevant careers for the interest stream
    all_potential = career_suggestions_by_interest.get(student.interest, [])
    predicted_career_name = predicted_career.name if predicted_career else ""
    
    for career in all_potential:
        if career.lower() != predicted_career_name.lower():
            suggested_careers.append(career)
        if len(suggested_careers) >= 3:
            break

    if predicted_career:
        student_skills_list = [skill.strip().lower() for skill in student.skills.split(',') if skill.strip()]
        required_skills_for_career = [skill.strip() for skill in predicted_career.required_skills.split(',') if skill.strip()]
        
        # Calculate missing skills (case-insensitive comparison)
        missing_skills = sorted(list(set(s.lower() for s in required_skills_for_career) - set(student_skills_list)))
        missing_skills_display = []
        for missing_skill_lower in missing_skills:
            # Find the original casing for display
            for rs in required_skills_for_career:
                if rs.lower() == missing_skill_lower:
                    missing_skills_display.append(rs)
                    break
        missing_skills = missing_skills_display

    roadmap = []
    if student.marks > 0 and predicted_career: # Only generate roadmap if test taken and career predicted
        roadmap = generate_roadmap(student, predicted_career)

    # --- Interview Preparation and SWOT Analysis Data ---
    interview_prep_data = {
        'Accountant': {
            'technical_topics': [
                'Basics of Accounting', 'Tally & GST', 'Income Tax', 
                'Financial Statements', 'MS Excel (VLOOKUP, Pivot Table)'
            ],
            'technical_questions': [
                'What is double entry system?', 'Difference between debit and credit?', 
                'What is GST?', 'Explain balance sheet.', 'What is depreciation?'
            ],
            'hr_questions': [
                'Why do you want to become an accountant?', 'How do you handle financial errors?', 
                'Are you comfortable working with deadlines?'
            ],
        },
        'Research Scientist': {
            'technical_topics': [
                'Research Methodology', 'Laboratory Techniques', 'Data Analysis', 'Scientific Writing'
            ],
            'technical_questions': [
                'What is hypothesis?', 'Explain your final year project.', 'What is research design?'
            ],
            'hr_questions': [
                'Why research field?', 'How do you handle failure in experiments?'
            ],
        },
        'Graphic Designer': {
            'technical_topics': [
                'Photoshop', 'Illustrator', 'Canva', 'UI/UX Basics', 'Color Theory'
            ],
            'technical_questions': [
                'What is RGB vs CMYK?', 'Explain your design portfolio.', 'What is typography?'
            ],
            'hr_questions': [
                'How do you handle client feedback?', 'Why choose graphic design?'
            ],
        },
        'Software Developer': {
            'technical_topics': [
                'DSA (Data Structures & Algorithms)', 'OOP (Object-Oriented Programming)', 
                'DBMS (Database Management Systems)', 'Python / Java', 'Git'
            ],
            'technical_questions': [
                'What is polymorphism?', 'Difference between list and tuple?', 'Explain MVC.'
            ],
            'hr_questions': [
                'Why software development?', 'Strengths & weaknesses?'
            ],
        },
    }

    swot_analysis_data = {
        'Accountant': {
            'strengths': ['Good numerical ability', 'Attention to detail', 'Strong finance interest'],
            'weaknesses': ['Limited practical exposure', 'Weak Excel skills'],
            'opportunities': ['Growing businesses need accountants', 'Tax consultancy demand'],
            'threats': ['Automation in accounting software', 'High competition'],
        },
        'Research Scientist': {
            'strengths': ['Analytical thinking', 'Strong subject knowledge'],
            'weaknesses': ['Limited lab experience', 'Need better research paper writing'],
            'opportunities': ['Government research grants', 'Pharma & biotech industries'],
            'threats': ['Limited research funding', 'High competition for PhD seats'],
        },
        'Graphic Designer': {
            'strengths': ['Creative thinking', 'Strong visual imagination'],
            'weaknesses': ['Limited portfolio', 'Time management issues'],
            'opportunities': ['Freelancing', 'Social media marketing boom'],
            'threats': ['AI design tools', 'High freelance competition'],
        },
        'Software Developer': {
            'strengths': ['Logical thinking', 'Coding skills'],
            'weaknesses': ['Poor communication', 'Lack of internships'],
            'opportunities': ['IT industry growth', 'Remote jobs'],
            'threats': ['Fast-changing technology', 'High competition'],
        },
    }

    current_interview_prep = None
    current_swot_analysis = None

    if predicted_career:
        career_name_str = predicted_career.name
        current_interview_prep = interview_prep_data.get(career_name_str)
        current_swot_analysis = swot_analysis_data.get(career_name_str)
    # --- End Interview Preparation and SWOT Analysis Data ---

    # --- Abroad Opportunities ---
    abroad_opportunities_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'career_abroad.md')
    abroad_opportunities_data = parse_abroad_opportunities(abroad_opportunities_file)
    print(f"Abroad Opportunities Data: {abroad_opportunities_data}")
    student_abroad_opportunities = abroad_opportunities_data.get(student.interest, {})
    print(f"Student Abroad Opportunities for {student.interest}: {student_abroad_opportunities}")
    
    context = {
        'student': student,
        'predicted_career': predicted_career,
        'required_skills_for_career': required_skills_for_career,
        'missing_skills': missing_skills,
        'learning_platforms': learning_platforms,
        'roadmap': roadmap,
        'suggested_careers': suggested_careers,
        'interview_prep': current_interview_prep,
        'swot_analysis': current_swot_analysis,
        'abroad_opportunities': student_abroad_opportunities,
    }
    return render(request, 'career/dashboard.html', context)

@login_required
def entrance_exams(request):
    return render(request, 'career/entrance_exams.html')


@login_required
def update_profile(request):
    print(f"--- Update Profile View ---")
    print(f"Request User: {request.user.username}")
    student = request.user.student
    print(f"Student ID before update: {student.id}, Interest: {student.interest}, Marks: {student.marks}, Skills: {student.skills}")
    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            print(f"Student object saved after profile update. New Interest: {student.interest}, New Skills: {student.skills}")
            # After profile update, re-run prediction
            print("Running predict_career after profile update.")
            predicted_career = predict_career(student)
            student.predicted_career = predicted_career
            student.save()
            if predicted_career:
                print(f"Predicted Career after update: {predicted_career.name}")
            else:
                print("predict_career returned None after profile update.")
            print("Student object saved with new predicted_career.")
            return redirect('career:dashboard')
    else:
        form = StudentUpdateForm(instance=student)
    
    suggested_skills_by_interest = {
        'IT': ['Python', 'Java', 'C++', 'SQL', 'HTML', 'CSS', 'JavaScript', 'React', 'Django', 'Machine Learning', 'Data Science', 'Cybersecurity', 'Cloud Computing'],
        'Commerce': ['Tally', 'GST', 'Income Tax', 'Basic Excel', 'Advanced Excel', 'Financial Modeling', 'Power BI', 'Auditing', 'Accounting Principles', 'Business Analysis'],
        'Medical': ['Biology', 'Chemistry', 'Physics', 'Anatomy', 'Physiology', 'Research Methods', 'Clinical Skills', 'Patient Care'],
        'Arts': ['Photoshop', 'Illustrator', 'Canva', 'Creative Writing', 'Graphic Design Principles', 'UI/UX Design', 'Video Editing', 'Content Creation'],
        'General': ['Communication', 'Teamwork', 'Problem Solving', 'Leadership', 'Time Management', 'Critical Thinking']
    }

    context = {
        'form': form,
        'suggested_skills_by_interest': suggested_skills_by_interest
    }
    return render(request, 'career/update_profile.html', context)

@login_required
def aptitude_test(request, category_name=None):
    print(f"--- Aptitude Test View ---")
    print(f"Request User: {request.user.username}")
    student = request.user.student
    print(f"Student ID before test: {student.id}, Interest: {student.interest}, Marks: {student.marks}")

    if request.method == 'POST':
        score = 0
        questions = Question.objects.all() # Fetch all questions to check answers
        for question in questions:
            selected_option = request.POST.get(str(question.id))
            if selected_option == question.correct_option:
                score += 1
        
        # Calculate marks based on correct answers
        if questions.count() > 0:
            student.marks = (score / questions.count()) * 100
        else:
            student.marks = 0 # No questions, no marks
        
        student.save()
        print(f"Student marks updated to: {student.marks}")

        print("Running predict_career after aptitude test.")
        predicted_career = predict_career(student)
        student.predicted_career = predicted_career
        student.save()
        if predicted_career:
            print(f"Predicted Career after test: {predicted_career.name}")
        else:
            print("predict_career returned None after aptitude test.")
        print("Student object saved with new predicted_career.")
        
        return redirect('career:dashboard')

    else:
        # Determine the category for filtering questions
        if category_name:
            # If category is provided in URL, use it
            filter_category = category_name
        elif student.interest and student.interest != 'General':
            # Otherwise, use student's interest if available and specific
            filter_category = student.interest
        else:
            # Fallback to a general category or no filter if neither is specific
            filter_category = None

        if filter_category:
            questions = Question.objects.filter(category=filter_category).order_by('?')
        else:
            questions = Question.objects.order_by('?') # Get all questions if no specific filter

        if not questions.exists():
            messages.info(request, "No questions found for this category. Displaying general questions.")
            questions = Question.objects.order_by('?') # Fallback if specific category yields no questions
            
        context = {
            'questions': questions,
            'current_category': filter_category # Pass current category to template if needed
        }
        return render(request, 'career/aptitude_test.html', context)

@login_required
def send_report(request):
    # Retrieve student and predicted career information
    student = request.user.student
    predicted_career = student.predicted_career

    # If no predicted career, redirect to dashboard with a message
    if not predicted_career:
        messages.warning(request, "Please update your profile and take the aptitude test to get a career prediction before generating a report.")
        return redirect('career:dashboard')

    # Get dashboard context to populate PDF report
    context = {
        'student': student,
        'predicted_career': predicted_career,
        'learning_platforms': {
            'Python': ['Coursera', 'Udemy', 'Codecademy'],
            'Java': ['Udemy', 'Pluralsight', 'edX'],
            'C++': ['Udemy', 'Coursera', 'GeeksforGeeks'],
            'SQL': ['Codecademy', 'Khan Academy', 'SQLZoo'],
            'Machine Learning': ['Coursera', 'edX', 'Fast.ai'],
            'Statistics': ['Coursera', 'Khan Academy'],
            'Communication': ['Coursera', 'LinkedIn Learning'],
            'Financial Management': ['edX', 'Coursera'],
            'Accounting': ['Coursera', 'ACA'],
            'Taxation': ['ClearTax', 'Udemy', 'ICAI Portal'],
            'Tally': ['Tally Education', 'Udemy'],
            'GST': ['GST Portal', 'ClearTax', 'Vskills'],
            'Biology': ['Khan Academy', 'Coursera', 'edX'],
            'Anatomy': ['Coursera', 'Kenhub'],
            'Pharmacology': ['Lecturio', 'Coursera'],
        },
        'roadmap': generate_roadmap(student, predicted_career),
        'now': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # Recalculate missing skills and suggested careers within this view for the report
    student_skills_list = [skill.strip().lower() for skill in student.skills.split(',') if skill.strip()]
    required_skills_for_career = [skill.strip() for skill in predicted_career.required_skills.split(',') if skill.strip()]
    
    context['required_skills_for_career'] = required_skills_for_career
    
    missing_skills = sorted(list(set(s.lower() for s in required_skills_for_career) - set(student_skills_list)))
    missing_skills_for_report = []
    for missing_skill_lower in missing_skills:
        skill_name = ""
        for rs in required_skills_for_career:
            if rs.lower() == missing_skill_lower:
                skill_name = rs
                break
        
        platforms = context['learning_platforms'].get(skill_name, [])
        missing_skills_for_report.append({'skill': skill_name, 'platforms': platforms})
    context['missing_skills'] = missing_skills_for_report

    career_suggestions_by_interest = {
        'Commerce': [
            'Accountant', 'Chartered Accountant (CA)', 'Financial Analyst',
            'Investment Banker', 'Tax Consultant', 'Auditor', 'Banking Officer'
        ],
        'IT': [
            'Software Developer', 'Web Developer', 'Data Scientist', 'Data Analyst',
            'AI Engineer', 'Cyber Security Analyst', 'Cloud Engineer'
        ],
        'Medical': [
            'Doctor', 'Pharmacist', 'Biotechnologist', 'Lab Technician',
            'Research Scientist', 'Nurse', 'Nutritionist'
        ],
        'Arts': [
            'Journalist', 'Content Writer', 'Graphic Designer', 'Lawyer',
            'Psychologist', 'Teacher', 'Event Manager'
        ],
        'General': []
    }
    suggested_careers = []
    all_potential = career_suggestions_by_interest.get(student.interest, [])
    predicted_career_name = predicted_career.name if predicted_career else ""
    
    for career in all_potential:
        if career.lower() != predicted_career_name.lower():
            suggested_careers.append(career)
        if len(suggested_careers) >= 3:
            break
    context['suggested_careers'] = suggested_careers


    # Render HTML template to string
    html_string = render_to_string('career/pdf_report.html', context)

    # Create PDF
    response = BytesIO()
    pdf = pisa.CreatePDF(html_string, dest=response)

    if pdf.err:
        messages.error(request, "Failed to generate PDF report.")
        return redirect('career:dashboard')

    # Create email
    recipient_email = student.report_email if student.report_email else student.user.email
    email = EmailMessage(
        subject=f"Your Career Report from Career Guidance System - {student.user.username}",
        body="Please find your personalized career report attached.",
        from_email=settings.EMAIL_HOST_USER,
        to=[recipient_email],
    )
    email.attach(f"career_report_{student.user.username}.pdf", response.getvalue(), 'application/pdf')
    
    try:
        email.send()
        messages.success(request, "Your career report has been sent to your email address!")
    except Exception as e:
        messages.error(request, f"Failed to send email: {e}")

    return redirect('career:dashboard')
