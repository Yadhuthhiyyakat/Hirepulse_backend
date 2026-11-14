from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User, UserRole
from apps.companies.models import Company
from apps.jobs.models import Job, JobType, WorkMode, ExperienceLevel, JobStatus

class JobAPITests(APITestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            email='recruiter@example.com',
            password='Password123!',
            first_name='Jane',
            last_name='Recruiter',
            role=UserRole.RECRUITER
        )
        self.seeker = User.objects.create_user(
            email='seeker@example.com',
            password='Password123!',
            first_name='Bob',
            last_name='Seeker',
            role=UserRole.JOB_SEEKER
        )
        self.company = Company.objects.create(
            recruiter=self.recruiter,
            name='Acme Corp',
            industry='Software',
            location='Austin, TX'
        )
        self.job = Job.objects.create(
            company=self.company,
            title='React Frontend Architect',
            description='Build outstanding user interfaces with React and TypeScript.',
            requirements='5+ years experience',
            skills=['React', 'TypeScript', 'Tailwind'],
            location='Austin, TX',
            job_type=JobType.FULL_TIME,
            work_mode=WorkMode.HYBRID,
            experience_level=ExperienceLevel.SENIOR,
            salary_min=130000,
            salary_max=160000,
            status=JobStatus.PUBLISHED
        )

    def test_job_listing_public(self):
        response = self.client.get('/api/v1/jobs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['count'], 1)

    def test_job_search_by_keyword(self):
        response = self.client.get('/api/v1/jobs/?search=React')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

        response2 = self.client.get('/api/v1/jobs/?search=NonExistentSkill')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['data']['count'], 0)

    def test_recruiter_can_create_job(self):
        self.client.force_authenticate(user=self.recruiter)
        payload = {
            'title': 'Senior Python Backend Developer',
            'description': 'Develop scalable backend microservices.',
            'requirements': 'Django experience required.',
            'skills': ['Python', 'Django', 'PostgreSQL'],
            'location': 'Austin, TX',
            'job_type': JobType.FULL_TIME,
            'work_mode': WorkMode.REMOTE,
            'experience_level': ExperienceLevel.MID,
            'salary_min': 110000,
            'salary_max': 140000,
            'status': JobStatus.PUBLISHED
        }
        response = self.client.post('/api/v1/jobs/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['title'], 'Senior Python Backend Developer')

    def test_seeker_cannot_create_job(self):
        self.client.force_authenticate(user=self.seeker)
        payload = {'title': 'Invalid Job'}
        response = self.client.post('/api/v1/jobs/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_save_job_toggle(self):
        self.client.force_authenticate(user=self.seeker)
        # First save
        res1 = self.client.post(f'/api/v1/jobs/{self.job.id}/save/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(res1.data['data']['is_saved'])

        # Second save (unsaves)
        res2 = self.client.post(f'/api/v1/jobs/{self.job.id}/save/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data['data']['is_saved'])

    def test_recruiter_cannot_edit_other_recruiter_job(self):
        other_recruiter = User.objects.create_user(
            email='recruiter2@example.com',
            password='Password123!',
            first_name='Other',
            last_name='Recruiter',
            role=UserRole.RECRUITER
        )
        self.client.force_authenticate(user=other_recruiter)
        response = self.client.patch(
            f'/api/v1/jobs/{self.job.id}/',
            {'title': 'Hacked Title'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_job_list_prevents_n_plus_one_queries(self):
        # Create 5 additional jobs
        for i in range(5):
            Job.objects.create(
                company=self.company,
                title=f'Job Batch {i}',
                description='Batch job test',
                location='Remote',
                job_type=JobType.FULL_TIME,
                work_mode=WorkMode.REMOTE,
                status=JobStatus.PUBLISHED
            )

        self.client.force_authenticate(user=self.seeker)
        # Listing 6 jobs should execute a minimal, fixed number of queries (count + select_related/prefetch_related/annotation)
        # Without N+1, queries should be <= 5 regardless of number of jobs
        with self.assertNumQueries(4):
            response = self.client.get('/api/v1/jobs/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['data']['count'], 6)

