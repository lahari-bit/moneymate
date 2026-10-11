from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import datetime
from django.utils import timezone
from tracker.models import Transaction, Category, Budget, SavingsGoal, RecurringExpense, Notification, UserProfile

class MoneyMateCoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123', first_name='John')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123', first_name='Jane')

        # Retrieve categories seeded by signal
        self.cat_food = Category.objects.filter(name='Food & Dining').first()
        if not self.cat_food:
            self.cat_food = Category.objects.create(name='Food & Dining', category_type='expense', user=None)

        self.cat_salary = Category.objects.filter(name='Salary').first()
        if not self.cat_salary:
            self.cat_salary = Category.objects.create(name='Salary', category_type='income', user=None)

    def test_registration_and_login(self):
        """Test registration and login flow."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'currency': '₹',
            'password1': 'mypassword123',
            'password2': 'mypassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_u = User.objects.get(username='newuser')
        self.assertEqual(new_u.profile.currency, '₹')

    def test_user_data_isolation(self):
        """Verify each user only sees their own transactions."""
        Transaction.objects.create(
            user=self.user1, title='User1 Expense', amount=Decimal('500.00'),
            transaction_type='expense', category=self.cat_food, date=timezone.now().date()
        )
        Transaction.objects.create(
            user=self.user2, title='User2 Secret Expense', amount=Decimal('999.00'),
            transaction_type='expense', category=self.cat_food, date=timezone.now().date()
        )

        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User1 Expense')
        self.assertNotContains(response, 'User2 Secret Expense')

    def test_transaction_crud(self):
        """Test adding, editing, and deleting a transaction."""
        self.client.login(username='user1', password='password123')
        
        # Add
        today = timezone.now().date().strftime('%Y-%m-%d')
        response = self.client.post(reverse('transaction_add'), {
            'title': 'Campus Lunch',
            'amount': '150.00',
            'transaction_type': 'expense',
            'category': self.cat_food.id,
            'date': today,
            'payment_method': 'upi',
            'notes': 'Lunch at canteen'
        })
        self.assertEqual(response.status_code, 302)
        tx = Transaction.objects.filter(user=self.user1, title='Campus Lunch').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, Decimal('150.00'))

        # Edit
        response = self.client.post(reverse('transaction_edit', args=[tx.id]), {
            'title': 'Campus Lunch Special',
            'amount': '220.00',
            'transaction_type': 'expense',
            'category': self.cat_food.id,
            'date': today,
            'payment_method': 'cash',
        })
        self.assertEqual(response.status_code, 302)
        tx.refresh_from_db()
        self.assertEqual(tx.title, 'Campus Lunch Special')
        self.assertEqual(tx.amount, Decimal('220.00'))

        # Delete
        response = self.client.post(reverse('transaction_delete', args=[tx.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(id=tx.id).exists())

    def test_budget_warning_and_exceeded(self):
        """Test budget warning at 80% and alert when exceeded."""
        today = timezone.now().date()
        budget = Budget.objects.create(
            user=self.user1,
            category=self.cat_food,
            amount=Decimal('1000.00'),
            month=today.month,
            year=today.year
        )

        # Spend 850 (85%)
        tx = Transaction.objects.create(
            user=self.user1,
            category=self.cat_food,
            title='Dinner',
            amount=Decimal('850.00'),
            transaction_type='expense',
            date=today
        )

        self.assertTrue(budget.is_warning())
        self.assertFalse(budget.is_exceeded())

        # Spend another 200 (Total 1050 > 1000)
        Transaction.objects.create(
            user=self.user1,
            category=self.cat_food,
            title='Late night snacks',
            amount=Decimal('200.00'),
            transaction_type='expense',
            date=today
        )

        self.assertTrue(budget.is_exceeded())

    def test_savings_goal_contribution(self):
        """Test contributing money to a savings goal."""
        self.client.login(username='user1', password='password123')
        goal = SavingsGoal.objects.create(
            user=self.user1,
            name='Study Laptop',
            target_amount=Decimal('10000.00'),
            current_amount=Decimal('5000.00'),
            target_date=timezone.now().date() + datetime.timedelta(days=60),
            category_icon='fa-laptop'
        )

        response = self.client.post(reverse('savings_contribute', args=[goal.id]), {
            'amount': '5000.00'
        })
        self.assertEqual(response.status_code, 302)
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal('10000.00'))
        self.assertTrue(goal.is_completed)

    def test_csv_export(self):
        """Test CSV export view returns valid spreadsheet response."""
        self.client.login(username='user1', password='password123')
        Transaction.objects.create(
            user=self.user1,
            title='Freelance Milestone',
            amount=Decimal('5000.00'),
            transaction_type='income',
            category=self.cat_salary,
            date=timezone.now().date()
        )

        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Freelance Milestone', response.content.decode('utf-8'))
