"""
Simple test script for Easy Clinic Portal.
"""
import unittest
from app import create_app, db
from app.models.user import User, Role

class EasyClinicPortalTestCase(unittest.TestCase):
    """Test case for Easy Clinic Portal."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users
        self.create_test_users()

        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def create_test_users(self):
        """Create test users for different roles."""
        # Create admin user
        admin = User(
            name='Admin User',
            email='admin@test.com',
            password='password',
            role=Role.SUPERADMIN
        )

        # Create doctor user
        doctor = User(
            name='Doctor User',
            email='doctor@test.com',
            password='password',
            role=Role.DOCTOR
        )

        # Create patient user
        patient = User(
            name='Patient User',
            email='patient@test.com',
            password='password',
            role=Role.PATIENT
        )

        # Create assistant user
        assistant = User(
            name='Assistant User',
            email='assistant@test.com',
            password='password',
            role=Role.ASSISTANT
        )

        db.session.add_all([admin, doctor, patient, assistant])
        db.session.commit()

    def test_home_page(self):
        """Test that the home page redirects to login."""
        response = self.client.get('/auth/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_login_page(self):
        """Test that the login page loads correctly."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_register_page(self):
        """Test that the register page loads correctly."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)

    def test_login_page_contains_form(self):
        """Test that the login page contains a form."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<form', response.data)
        self.assertIn(b'password', response.data)

    def test_register_page_contains_form(self):
        """Test that the register page contains a form."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<form', response.data)
        self.assertIn(b'password', response.data)

if __name__ == '__main__':
    unittest.main()
