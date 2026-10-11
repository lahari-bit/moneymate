from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from decimal import Decimal

class UserProfile(models.Model):
    CURRENCY_CHOICES = [
        ('₹', 'INR - Indian Rupee (₹)'),
        ('$', 'USD - US Dollar ($)'),
        ('€', 'EUR - Euro (€)'),
        ('£', 'GBP - British Pound (£)'),
        ('¥', 'JPY - Japanese Yen (¥)'),
        ('A$', 'AUD - Australian Dollar (A$)'),
        ('C$', 'CAD - Canadian Dollar (C$)'),
        ('AED', 'AED - UAE Dirham (AED)'),
    ]

    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    currency = models.CharField(max_length=5, default='₹', choices=CURRENCY_CHOICES)
    theme = models.CharField(max_length=10, default='light', choices=THEME_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, default='Student / Individual')
    monthly_income_goal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Category(models.Model):
    CATEGORY_TYPES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]

    DEFAULT_CATEGORIES = [
        # (Name, Type, Icon, Color)
        ('Food & Dining', 'expense', 'fa-utensils', '#EF4444'),
        ('Transportation', 'expense', 'fa-bus', '#F59E0B'),
        ('Education', 'expense', 'fa-graduation-cap', '#3B82F6'),
        ('Shopping', 'expense', 'fa-bag-shopping', '#EC4899'),
        ('Bills & Utilities', 'expense', 'fa-receipt', '#8B5CF6'),
        ('Healthcare', 'expense', 'fa-heart-pulse', '#10B981'),
        ('Entertainment', 'expense', 'fa-film', '#6366F1'),
        ('Personal Care', 'expense', 'fa-spa', '#14B8A6'),
        ('Other Expense', 'expense', 'fa-tags', '#64748B'),
        ('Salary', 'income', 'fa-money-bill-wave', '#10B981'),
        ('Freelance & Projects', 'income', 'fa-laptop-code', '#3B82F6'),
        ('Pocket Money / Allowance', 'income', 'fa-hand-holding-dollar', '#F59E0B'),
        ('Scholarship / Grants', 'income', 'fa-award', '#8B5CF6'),
        ('Investment Returns', 'income', 'fa-chart-line', '#06B6D4'),
        ('Other Income', 'income', 'fa-gift', '#EC4899'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=80)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='expense')
    icon = models.CharField(max_length=60, default='fa-tag')
    color = models.CharField(max_length=30, default='#10B981')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]

    PAYMENT_METHODS = [
        ('upi', 'UPI / GPay / PhonePe'),
        ('cash', 'Cash'),
        ('debit_card', 'Debit Card'),
        ('credit_card', 'Credit Card'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Mobile Wallet'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='expense')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='upi')
    notes = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.transaction_type})"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.PositiveSmallIntegerField(default=timezone.now().month)
    year = models.PositiveSmallIntegerField(default=timezone.now().year)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')
        ordering = ['-year', '-month', 'category__name']

    def __str__(self):
        return f"{self.category.name} Budget ({self.month}/{self.year}) - {self.amount}"

    def get_spent_amount(self):
        """Calculates total spent in this category for this month & year."""
        total = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_type='expense',
            date__year=self.year,
            date__month=self.month
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        return total

    def get_spent_percentage(self):
        spent = self.get_spent_amount()
        if self.amount > 0:
            pct = (spent / self.amount) * 100
            return round(min(pct, 100), 1)
        return 0

    def get_raw_spent_percentage(self):
        spent = self.get_spent_amount()
        if self.amount > 0:
            return round((spent / self.amount) * 100, 1)
        return 0

    def get_remaining_amount(self):
        spent = self.get_spent_amount()
        return self.amount - spent

    def is_warning(self):
        return self.get_raw_spent_percentage() >= 80 and self.get_raw_spent_percentage() <= 100

    def is_exceeded(self):
        return self.get_raw_spent_percentage() > 100


class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=150)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    target_date = models.DateField()
    category_icon = models.CharField(max_length=50, default='fa-bullseye')
    color = models.CharField(max_length=30, default='#10B981')
    notes = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"

    def get_progress_percentage(self):
        if self.target_amount > 0:
            pct = (self.current_amount / self.target_amount) * 100
            return round(min(pct, 100), 1)
        return 0

    def get_remaining_amount(self):
        rem = self.target_amount - self.current_amount
        return max(rem, Decimal('0.00'))

    def get_days_remaining(self):
        today = date.today()
        if self.target_date > today:
            return (self.target_date - today).days
        elif self.target_date == today:
            return 0
        else:
            return -((today - self.target_date).days)


class RecurringExpense(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_expenses')
    title = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='recurring_expenses')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
    payment_method = models.CharField(max_length=20, choices=Transaction.PAYMENT_METHODS, default='upi')
    start_date = models.DateField(default=timezone.now)
    next_due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_due_date']

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.frequency})"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Budget Warning'),
        ('danger', 'Budget Exceeded'),
        ('success', 'Goal Achieved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} for {self.user.username}"
