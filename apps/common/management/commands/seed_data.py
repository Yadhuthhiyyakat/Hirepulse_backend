from django.core.management.base import BaseCommand
from apps.accounts.models import User, UserRole, Profile
from apps.companies.models import Company
from apps.jobs.models import Job, JobType, WorkMode, ExperienceLevel, JobStatus, SavedJob
from apps.applications.models import Application, ApplicationStatus
from apps.notifications.models import Notification, NotificationType
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds initial test data with realistic users, companies, jobs, applications and notifications'

    def handle(self, *args, **options):
        self.stdout.write("Seeding recruitment platform data...")

        # 1. Admin
        admin_user, _ = User.objects.get_or_create(
            email='admin@recruitment.com',
            defaults={
                'first_name': 'Platform',
                'last_name': 'Admin',
                'role': UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('Admin@123456')
        admin_user.save()

        # 2. Recruiters
        recruiter1, _ = User.objects.get_or_create(
            email='recruiter@techcorp.com',
            defaults={
                'first_name': 'Sarah',
                'last_name': 'Connor',
                'role': UserRole.RECRUITER,
                'phone': '+1 (555) 019-2834',
            }
        )
        recruiter1.set_password('Recruiter@123')
        recruiter1.save()

        recruiter2, _ = User.objects.get_or_create(
            email='alex.hr@nexusai.io',
            defaults={
                'first_name': 'Alex',
                'last_name': 'Vance',
                'role': UserRole.RECRUITER,
                'phone': '+1 (555) 482-1940',
            }
        )
        recruiter2.set_password('Recruiter@123')
        recruiter2.save()

        # 3. Companies
        company1, _ = Company.objects.get_or_create(
            recruiter=recruiter1,
            name='TechCorp Solutions',
            defaults={
                'description': 'TechCorp Solutions is a global leader in enterprise cloud infrastructure, high-throughput systems, and developer productivity tooling.',
                'website': 'https://techcorp.example.com',
                'industry': 'Information Technology & Services',
                'location': 'San Francisco, CA',
                'company_size': '201-500',
                'founded_year': 2018,
            }
        )

        company2, _ = Company.objects.get_or_create(
            recruiter=recruiter2,
            name='Nexus AI Labs',
            defaults={
                'description': 'Nexus AI builds real-time intelligent agents and multimodal systems transforming healthcare and financial analytics.',
                'website': 'https://nexusai.example.com',
                'industry': 'Artificial Intelligence',
                'location': 'New York, NY',
                'company_size': '51-200',
                'founded_year': 2021,
            }
        )

        # 4. Job Seekers
        jobseeker1, _ = User.objects.get_or_create(
            email='john.doe@example.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'role': UserRole.JOB_SEEKER,
                'phone': '+1 (555) 234-5678',
            }
        )
        jobseeker1.set_password('Seeker@123456')
        jobseeker1.save()

        # Update profile for John Doe
        profile1, _ = Profile.objects.get_or_create(user=jobseeker1)
        profile1.bio = 'Senior Full-Stack Engineer with 5+ years of experience building modern React, TypeScript, and Django distributed applications.'
        profile1.location = 'San Francisco, CA'
        profile1.skills = ['React', 'TypeScript', 'Django', 'PostgreSQL', 'Tailwind CSS', 'Docker', 'REST API', 'Redis']
        profile1.portfolio_url = 'https://johndoe.dev'
        profile1.github_url = 'https://github.com/johndoe'
        profile1.linkedin_url = 'https://linkedin.com/in/johndoe'
        profile1.experience = [
            {
                'company': 'Fintech Horizon',
                'title': 'Senior Frontend Engineer',
                'location': 'San Francisco, CA',
                'start_date': '2022-03',
                'end_date': 'Present',
                'current': True,
                'description': 'Architected React dashboard with TanStack Query and WebSockets handling real-time trading metrics.'
            },
            {
                'company': 'CloudScale Tech',
                'title': 'Software Developer',
                'location': 'San Jose, CA',
                'start_date': '2019-06',
                'end_date': '2022-02',
                'current': False,
                'description': 'Developed Python/Django microservices and integrated PostgreSQL database pipelines.'
            }
        ]
        profile1.education = [
            {
                'institution': 'University of California, Berkeley',
                'degree': 'Bachelor of Science',
                'field_of_study': 'Computer Science',
                'start_year': '2015',
                'end_year': '2019'
            }
        ]
        profile1.save()

        # Job Seeker 2
        jobseeker2, _ = User.objects.get_or_create(
            email='emily.chen@example.com',
            defaults={
                'first_name': 'Emily',
                'last_name': 'Chen',
                'role': UserRole.JOB_SEEKER,
                'phone': '+1 (555) 345-6789',
            }
        )
        jobseeker2.set_password('Seeker@123456')
        jobseeker2.save()

        profile2, _ = Profile.objects.get_or_create(user=jobseeker2)
        profile2.bio = 'AI and Backend Engineer passionate about scalable distributed systems and LLM pipelines.'
        profile2.location = 'Seattle, WA'
        profile2.skills = ['Python', 'FastAPI', 'PyTorch', 'Django', 'Docker', 'PostgreSQL']
        profile2.save()

        # 5. Jobs
        jobs_data = [
            {
                'company': company1,
                'title': 'Senior Full-Stack Engineer (React & Django)',
                'description': 'We are looking for a Senior Full-Stack Engineer to lead the development of our flagship enterprise platform. You will design, build, and deploy high-performance web applications using modern React, TypeScript, and Django REST Framework.',
                'requirements': '• 5+ years of experience in full-stack web development.\n• Expertise in TypeScript, React, and modern state management (React Query/Zustand).\n• Deep familiarity with Django REST Framework, PostgreSQL, and asynchronous tasks.\n• Experience with Docker and CI/CD pipelines.',
                'responsibilities': '• Design clean frontend architectures and reusable UI component libraries.\n• Build resilient RESTful APIs and real-time WebSocket channels.\n• Mentor junior developers and participate in design system reviews.',
                'skills': ['React', 'TypeScript', 'Django', 'PostgreSQL', 'Docker'],
                'location': 'San Francisco, CA',
                'job_type': JobType.FULL_TIME,
                'work_mode': WorkMode.HYBRID,
                'experience_level': ExperienceLevel.SENIOR,
                'salary_min': 140000,
                'salary_max': 180000,
                'status': JobStatus.PUBLISHED,
            },
            {
                'company': company1,
                'title': 'Frontend Developer (React + Tailwind)',
                'description': 'Join our UI/UX squad to craft delightful web user interfaces with React, Tailwind CSS, and shadcn/ui. You will collaborate with product designers to implement pixel-perfect, accessible user journeys.',
                'requirements': '• 2+ years of professional experience with React and Tailwind CSS.\n• Strong grasp of modern JavaScript/TypeScript and web accessibility standards.\n• Experience with responsive design and mobile-first principles.',
                'responsibilities': '• Build intuitive dashboards and job candidate portals.\n• Optimize web performance and Core Web Vitals.\n• Write clean, maintainable modular code.',
                'skills': ['React', 'Tailwind CSS', 'TypeScript', 'HTML5', 'CSS3'],
                'location': 'Remote, US',
                'job_type': JobType.FULL_TIME,
                'work_mode': WorkMode.REMOTE,
                'experience_level': ExperienceLevel.MID,
                'salary_min': 95000,
                'salary_max': 125000,
                'status': JobStatus.PUBLISHED,
            },
            {
                'company': company2,
                'title': 'Machine Learning Platform Engineer',
                'description': 'Help Nexus AI build the next generation of scalable infrastructure for LLM fine-tuning and inference. You will build high-throughput microservices using Python and distributed queues.',
                'requirements': '• Strong background in Python, distributed computing, and Redis.\n• Experience with PyTorch or HuggingFace pipelines.\n• Knowledge of containerization with Docker and Kubernetes.',
                'responsibilities': '• Scale inference pipelines to serve low-latency user requests.\n• Maintain model registries and evaluation harnesses.',
                'skills': ['Python', 'Docker', 'Redis', 'PyTorch', 'FastAPI'],
                'location': 'New York, NY',
                'job_type': JobType.FULL_TIME,
                'work_mode': WorkMode.ONSITE,
                'experience_level': ExperienceLevel.LEAD,
                'salary_min': 175000,
                'salary_max': 230000,
                'status': JobStatus.PUBLISHED,
            },
            {
                'company': company2,
                'title': 'Junior Backend Developer (Python / Django)',
                'description': 'Exciting entry-level opportunity for a motivated software engineer to learn from industry experts while writing production Django code and database models.',
                'requirements': '• Solid grasp of Python, Object-Oriented Programming, and SQL basics.\n• Familiarity with Git version control.\n• Eagerness to learn and collaborate with senior architects.',
                'responsibilities': '• Assist with REST API endpoints and unit tests.\n• Fix bugs and write documentation.',
                'skills': ['Python', 'Django', 'SQL', 'Git'],
                'location': 'New York, NY',
                'job_type': JobType.FULL_TIME,
                'work_mode': WorkMode.HYBRID,
                'experience_level': ExperienceLevel.JUNIOR,
                'salary_min': 70000,
                'salary_max': 90000,
                'status': JobStatus.PUBLISHED,
            },
            {
                'company': company1,
                'title': 'DevOps & Cloud Engineer (Contract)',
                'description': 'Short-term contract to migrate legacy AWS workloads into modern Kubernetes clusters and automated GitHub Actions workflows.',
                'requirements': '• 4+ years of AWS and Terraform experience.\n• Strong knowledge of PostgreSQL scaling, backups, and security monitoring.',
                'responsibilities': '• Write Terraform infrastructure as code scripts.\n• Configure staging and production environments.',
                'skills': ['AWS', 'Docker', 'Terraform', 'PostgreSQL', 'CI/CD'],
                'location': 'Remote',
                'job_type': JobType.CONTRACT,
                'work_mode': WorkMode.REMOTE,
                'experience_level': ExperienceLevel.SENIOR,
                'salary_min': 120000,
                'salary_max': 150000,
                'status': JobStatus.PUBLISHED,
            },
        ]

        created_jobs = []
        for j_data in jobs_data:
            job, _ = Job.objects.get_or_create(
                company=j_data['company'],
                title=j_data['title'],
                defaults=j_data
            )
            created_jobs.append(job)

        # 6. Saved Jobs
        SavedJob.objects.get_or_create(user=jobseeker1, job=created_jobs[0])
        SavedJob.objects.get_or_create(user=jobseeker1, job=created_jobs[1])

        # 7. Applications
        # John Doe applies to Senior Full-Stack Engineer
        app1, _ = Application.objects.get_or_create(
            job=created_jobs[0],
            candidate=jobseeker1,
            defaults={
                'status': ApplicationStatus.SHORTLISTED,
                'cover_letter': 'I am very excited about TechCorp’s mission. With my 5+ years of experience in React and Django, I would love to contribute to your core architecture.',
                'internal_notes': 'Strong candidate with impressive React Query and Django experience. Move to technical interview.',
                'interview_date': timezone.now() + timedelta(days=3),
            }
        )

        # John Doe applies to Frontend Developer
        app2, _ = Application.objects.get_or_create(
            job=created_jobs[1],
            candidate=jobseeker1,
            defaults={
                'status': ApplicationStatus.UNDER_REVIEW,
                'cover_letter': 'My design and frontend experience aligns perfectly with the requirements.',
                'internal_notes': 'Reviewing portfolio URL.',
            }
        )

        # Emily Chen applies to Machine Learning Platform Engineer
        app3, _ = Application.objects.get_or_create(
            job=created_jobs[2],
            candidate=jobseeker2,
            defaults={
                'status': ApplicationStatus.INTERVIEW,
                'cover_letter': 'I have built multiple PyTorch models and low-latency inference endpoints.',
                'internal_notes': 'Scheduled interview for tomorrow morning.',
                'interview_date': timezone.now() + timedelta(days=1),
            }
        )

        # 8. Notifications
        Notification.objects.get_or_create(
            user=jobseeker1,
            title='Your application has been Shortlisted!',
            message='Congratulations! Your application for Senior Full-Stack Engineer at TechCorp Solutions has been shortlisted.',
            notification_type=NotificationType.STATUS_UPDATE,
            data={'job_id': str(created_jobs[0].id), 'application_id': str(app1.id)}
        )

        Notification.objects.get_or_create(
            user=jobseeker1,
            title='Interview Scheduled',
            message='You have been invited for a technical interview on ' + (timezone.now() + timedelta(days=3)).strftime('%b %d, %Y at %I:%M %p') + '.',
            notification_type=NotificationType.INTERVIEW,
            data={'job_id': str(created_jobs[0].id), 'application_id': str(app1.id)}
        )

        Notification.objects.get_or_create(
            user=recruiter1,
            title='New Applicant Received',
            message='John Doe applied for Senior Full-Stack Engineer (React & Django).',
            notification_type=NotificationType.NEW_APPLICATION,
            data={'job_id': str(created_jobs[0].id), 'application_id': str(app1.id)}
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with demo users, companies, jobs, applications and notifications!"))

