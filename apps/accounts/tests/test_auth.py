from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User, UserRole

class AuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.refresh_url = reverse('auth_refresh')
        self.logout_url = reverse('auth_logout')
        self.me_url = reverse('auth_me')

        self.seeker_data = {
            'email': 'testseeker@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'Seeker',
            'role': UserRole.JOB_SEEKER,
            'phone': '1234567890'
        }
        self.login_payload = {
            'email': self.seeker_data['email'],
            'password': self.seeker_data['password'],
        }

    def test_job_seeker_registration(self):
        response = self.client.post(self.register_url, self.seeker_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertNotIn('refresh', response.data['data'])
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        self.assertEqual(response.data['data']['user']['email'], self.seeker_data['email'])

    def test_registration_password_mismatch(self):
        mismatched_data = dict(self.seeker_data)
        mismatched_data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, mismatched_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_success(self):
        # Register first
        self.client.post(self.register_url, self.seeker_data, format='json')

        response = self.client.post(self.login_url, self.login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        self.assertEqual(response.data['user']['role'], UserRole.JOB_SEEKER)

    def test_refresh_token_via_cookie(self):
        # Login to obtain cookie
        self.client.post(self.register_url, self.seeker_data, format='json')
        login_res = self.client.post(self.login_url, self.login_payload, format='json')
        self.assertIn('refresh_token', login_res.cookies)

        # Refresh endpoint should read refresh_token from cookies
        refresh_res = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)
        self.assertIn('refresh_token', refresh_res.cookies)

    def test_logout_clears_cookie(self):
        self.client.post(self.register_url, self.seeker_data, format='json')
        login_res = self.client.post(self.login_url, self.login_payload, format='json')
        access = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        logout_res = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
        # Cookie should be expired / deleted
        self.assertEqual(logout_res.cookies['refresh_token'].value, '')

    def test_authenticated_me_endpoint(self):
        user = User.objects.create_user(
            email='testme@example.com',
            password='StrongPassword123!',
            first_name='Current',
            last_name='User',
            role=UserRole.JOB_SEEKER
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], 'testme@example.com')

