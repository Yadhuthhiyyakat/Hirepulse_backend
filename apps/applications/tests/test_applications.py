from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User, UserRole
from apps.companies.models import Company
from apps.jobs.models import Job, JobType, WorkMode, ExperienceLevel, JobStatus
from apps.applications.models import Application, ApplicationStatus

class ApplicationAPITests(APITestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email='recruiter_app@example.com',
            password='Password123!',
            first_name='Recruiter',
            last_name='User',
            role=UserRole.RECRUITER
        )
        self.seeker = User.objects.create_user(
            email='seeker_app@example.com',
            password='Password123!',
            first_name='Applicant',
            last_name='Candidate',
            role=UserRole.JOB_SEEKER
        )
        self.company = Company.objects.create(
            recruiter=self.recruiter,
            name='Test Corp'
        )
        self.job = Job.objects.create(
            company=self.company,
            title='Staff Software Engineer',
            description='Lead architecture',
            location='New York, NY',
            job_type=JobType.FULL_TIME,
            work_mode=WorkMode.REMOTE,
            experience_level=ExperienceLevel.LEAD,
            status=JobStatus.PUBLISHED
        )

        self.resume_file = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 dummy pdf content",
            content_type="application/pdf"
        )

    def test_apply_for_job_success(self):
        self.client.force_authenticate(user=self.seeker)
        data = {
            'job_id': str(self.job.id),
            'resume': self.resume_file,
            'cover_letter': 'I am the perfect fit for this staff position.'
        }
        response = self.client.post('/api/v1/applications/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], ApplicationStatus.APPLIED)

    def test_duplicate_application_prevention(self):
        self.client.force_authenticate(user=self.seeker)
        data = {
            'job_id': str(self.job.id),
            'resume': self.resume_file,
            'cover_letter': 'First application'
        }
        res1 = self.client.post('/api/v1/applications/', data, format='multipart')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Re-apply with same user
        resume2 = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 dummy", content_type="application/pdf")
        data2 = {
            'job_id': str(self.job.id),
            'resume': resume2,
            'cover_letter': 'Second attempt'
        }
        res2 = self.client.post('/api/v1/applications/', data2, format='multipart')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res2.data['success'])

    def test_recruiter_can_update_status(self):
        # Create an application
        application = Application.objects.create(
            job=self.job,
            candidate=self.seeker,
            resume=self.resume_file,
            status=ApplicationStatus.APPLIED
        )

        self.client.force_authenticate(user=self.recruiter)
        update_data = {
            'status': ApplicationStatus.SHORTLISTED,
            'internal_notes': 'Candidate passed initial resume screen.'
        }
        response = self.client.patch(
            f'/api/v1/applications/{application.id}/update_status/',
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.SHORTLISTED)
        self.assertEqual(application.internal_notes, 'Candidate passed initial resume screen.')

    def test_unrelated_seeker_cannot_view_application(self):
        application = Application.objects.create(
            job=self.job,
            candidate=self.seeker,
            resume=self.resume_file,
            status=ApplicationStatus.APPLIED
        )
        other_seeker = User.objects.create_user(
            email='other_seeker@example.com',
            password='Password123!',
            first_name='Other',
            last_name='Candidate',
            role=UserRole.JOB_SEEKER
        )
        self.client.force_authenticate(user=other_seeker)
        response = self.client.get(f'/api/v1/applications/{application.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recruiter_stats_aggregation(self):
        Application.objects.create(
            job=self.job,
            candidate=self.seeker,
            resume=self.resume_file,
            status=ApplicationStatus.SHORTLISTED
        )
        self.client.force_authenticate(user=self.recruiter)
        response = self.client.get('/api/v1/applications/recruiter_stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        data = response.data['data']
        self.assertEqual(data['active_jobs'], 1)
        self.assertEqual(data['total_applications'], 1)
        self.assertEqual(data['shortlisted'], 1)
        self.assertEqual(data['interviews'], 0)

