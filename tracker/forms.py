from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Transaction, Budget, SavingsGoal, RecurringExpense, UserProfile, Category
from django.utils import timezone

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-input'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-input'}))
    currency = forms.ChoiceField(
        choices=UserProfile.CURRENCY_CHOICES,
        initial='₹',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose Username', 'class': 'form-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.currency = self.cleaned_data.get('currency', '₹')
            profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = UserProfile
        fields = ['currency', 'theme', 'phone', 'occupation', 'monthly_income_goal']
        widgets = {
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 9876543210', 'class': 'form-input'}),
            'occupation': forms.TextInput(attrs={'placeholder': 'e.g. CS Student, Freelancer', 'class': 'form-input'}),
            'monthly_income_goal': forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-input', 'step': '0.01'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'transaction_type', 'category', 'date', 'payment_method', 'notes', 'is_recurring']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Grocery Shopping, Salary', 'class': 'form-input'}),
            'amount': forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_transaction_type'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'placeholder': 'Optional notes or receipt details...', 'rows': 3, 'class': 'form-textarea'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=None) | Q(user=user)
            ).order_by('category_type', 'name')
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().strftime('%Y-%m-%d')


class BudgetForm(forms.ModelForm):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    month = forms.ChoiceField(choices=MONTH_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Budget
        fields = ['category', 'amount', 'month', 'year']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'placeholder': '5000.00', 'class': 'form-input', 'step': '0.01', 'min': '1'}),
            'year': forms.NumberInput(attrs={'class': 'form-input', 'min': 2020, 'max': 2100}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.now()
        if not self.initial.get('month'):
            self.initial['month'] = now.month
        if not self.initial.get('year'):
            self.initial['year'] = now.year

        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                (Q(user=None) | Q(user=user)) & Q(category_type='expense')
            ).order_by('name')


class SavingsGoalForm(forms.ModelForm):
    ICON_CHOICES = [
        ('fa-bullseye', '🎯 Target'),
        ('fa-laptop', '💻 Laptop / Gadget'),
        ('fa-graduation-cap', '🎓 College / Education'),
        ('fa-plane', '✈️ Travel & Vacation'),
        ('fa-motorcycle', '🛵 Vehicle / Bike'),
        ('fa-piggy-bank', '🐷 Emergency Fund'),
        ('fa-house', '🏠 Home / Rent Deposit'),
        ('fa-gift', '🎁 Gifts & Festive'),
    ]

    category_icon = forms.ChoiceField(choices=ICON_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = SavingsGoal
        fields = ['name', 'target_amount', 'current_amount', 'target_date', 'category_icon', 'color', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. MacBook Pro, Semester Fees', 'class': 'form-input'}),
            'target_amount': forms.NumberInput(attrs={'placeholder': '50000.00', 'class': 'form-input', 'step': '0.01', 'min': '1'}),
            'current_amount': forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-color', 'value': '#10B981'}),
            'notes': forms.Textarea(attrs={'placeholder': 'Why are you saving for this?', 'rows': 2, 'class': 'form-textarea'}),
        }


class SavingsContributionForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1.00,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter amount to add', 'class': 'form-input', 'step': '0.01', 'min': '1'})
    )


class RecurringExpenseForm(forms.ModelForm):
    class Meta:
        model = RecurringExpense
        fields = ['title', 'amount', 'category', 'frequency', 'payment_method', 'start_date', 'next_due_date', 'is_active', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Netflix, Room Rent, WiFi Bill', 'class': 'form-input'}),
            'amount': forms.NumberInput(attrs={'placeholder': '999.00', 'class': 'form-input', 'step': '0.01', 'min': '1'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'notes': forms.Textarea(attrs={'placeholder': 'Billing notes, account details...', 'rows': 2, 'class': 'form-textarea'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.now()
        if not self.initial.get('start_date'):
            self.initial['start_date'] = now.strftime('%Y-%m-%d')
        if not self.initial.get('next_due_date'):
            self.initial['next_due_date'] = now.strftime('%Y-%m-%d')
        if user:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                (Q(user=None) | Q(user=user)) & Q(category_type='expense')
            ).order_by('name')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Gym & Fitness', 'class': 'form-input'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'placeholder': 'fa-dumbbell', 'class': 'form-input'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-color', 'value': '#10B981'}),
        }
