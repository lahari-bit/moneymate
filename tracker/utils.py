import datetime
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Transaction, Budget, SavingsGoal, RecurringExpense, Notification, Category

def check_budget_alerts(user, category, year=None, month=None):
    """Checks if spending in a category has crossed 80% or 100% of the budget and triggers notifications."""
    if not category or category.category_type != 'expense':
        return

    today = timezone.now().date()
    year = year or today.year
    month = month or today.month

    try:
        budget = Budget.objects.get(user=user, category=category, year=year, month=month)
    except Budget.DoesNotExist:
        return

    spent = budget.get_spent_amount()
    if budget.amount <= 0:
        return

    percentage = (spent / budget.amount) * 100

    if percentage >= 100:
        # Check if already notified recently
        exists = Notification.objects.filter(
            user=user,
            notification_type='danger',
            title__icontains=category.name,
            created_at__year=year,
            created_at__month=month
        ).exists()
        if not exists:
            Notification.objects.create(
                user=user,
                title=f"🚨 Budget Exceeded: {category.name}",
                message=f"You have spent {user.profile.currency}{spent:,.2f} of your {user.profile.currency}{budget.amount:,.2f} budget ({percentage:.1f}%) for {category.name} in {today.strftime('%B %Y')}.",
                notification_type='danger',
                link='/budgets/'
            )
    elif percentage >= 80:
        exists = Notification.objects.filter(
            user=user,
            notification_type='warning',
            title__icontains=category.name,
            created_at__year=year,
            created_at__month=month
        ).exists()
        if not exists:
            Notification.objects.create(
                user=user,
                title=f"⚠️ Budget Warning: {category.name}",
                message=f"You have reached {percentage:.1f}% ({user.profile.currency}{spent:,.2f}) of your {user.profile.currency}{budget.amount:,.2f} budget for {category.name}.",
                notification_type='warning',
                link='/budgets/'
            )


def load_demo_data(user):
    """Populates realistic demo data for testing and demonstrations."""
    # Ensure default categories safely
    for name, c_type, icon, color in Category.DEFAULT_CATEGORIES:
        if not Category.objects.filter(user=None, name=name).exists():
            Category.objects.create(
                user=None,
                name=name,
                category_type=c_type,
                icon=icon,
                color=color,
                is_default=True
            )

    # Fetch category maps
    cats = {c.name: c for c in Category.objects.filter(Q(user=None) | Q(user=user))}

    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    # 1. Clear existing demo data if any, or create fresh
    Transaction.objects.filter(user=user).delete()
    Budget.objects.filter(user=user).delete()
    SavingsGoal.objects.filter(user=user).delete()
    RecurringExpense.objects.filter(user=user).delete()
    Notification.objects.filter(user=user).delete()

    # 2. Add realistic income transactions
    income_samples = [
        ("Monthly Tech Internship Stipend", Decimal('35000.00'), cats.get('Salary'), today.replace(day=1), 'net_banking'),
        ("Freelance Web Design Project", Decimal('15000.00'), cats.get('Freelance & Projects'), today - datetime.timedelta(days=12), 'upi'),
        ("Semester Merit Scholarship", Decimal('12000.00'), cats.get('Scholarship / Grants'), today - datetime.timedelta(days=22), 'net_banking'),
        ("Pocket Money Allowance", Decimal('5000.00'), cats.get('Pocket Money / Allowance'), today - datetime.timedelta(days=5), 'upi'),
    ]

    for title, amount, cat, tx_date, method in income_samples:
        if cat:
            Transaction.objects.create(
                user=user,
                title=title,
                amount=amount,
                transaction_type='income',
                category=cat,
                date=tx_date,
                payment_method=method,
                notes="Verified credited transaction"
            )

    # 3. Add realistic expense transactions
    expense_samples = [
        # Food
        ("Weekly Campus Groceries & Fruits", Decimal('2450.00'), cats.get('Food & Dining'), today - datetime.timedelta(days=2), 'upi'),
        ("Dinner with Friends @ Bistro", Decimal('1280.00'), cats.get('Food & Dining'), today - datetime.timedelta(days=6), 'credit_card'),
        ("Cafeteria Snacks & Coffee", Decimal('320.00'), cats.get('Food & Dining'), today - datetime.timedelta(days=1), 'upi'),
        ("Pizza Night Study Group", Decimal('890.00'), cats.get('Food & Dining'), today - datetime.timedelta(days=10), 'upi'),
        ("Supermarket Essentials", Decimal('1750.00'), cats.get('Food & Dining'), today - datetime.timedelta(days=18), 'debit_card'),
        # Transportation
        ("Monthly Metro Smart Card Recharge", Decimal('1200.00'), cats.get('Transportation'), today - datetime.timedelta(days=8), 'upi'),
        ("Uber Ride to Airport & Back", Decimal('850.00'), cats.get('Transportation'), today - datetime.timedelta(days=14), 'upi'),
        ("Bike Fuel Refill", Decimal('650.00'), cats.get('Transportation'), today - datetime.timedelta(days=4), 'cash'),
        # Education
        ("Python & Django Fullstack Course", Decimal('1999.00'), cats.get('Education'), today - datetime.timedelta(days=15), 'net_banking'),
        ("Semester Textbooks & Stationery", Decimal('1450.00'), cats.get('Education'), today - datetime.timedelta(days=20), 'upi'),
        ("Cloud Hosting & Domain for Portfolio", Decimal('1250.00'), cats.get('Education'), today - datetime.timedelta(days=11), 'credit_card'),
        # Shopping
        ("Winter Jacket & Sneaker Sale", Decimal('3499.00'), cats.get('Shopping'), today - datetime.timedelta(days=9), 'credit_card'),
        ("Wireless Noise-Canceling Earbuds", Decimal('2899.00'), cats.get('Shopping'), today - datetime.timedelta(days=16), 'upi'),
        # Bills & Utilities
        ("High-Speed Fiber Broadband", Decimal('999.00'), cats.get('Bills & Utilities'), today - datetime.timedelta(days=7), 'net_banking'),
        ("Mobile Postpaid Unlimited Plan", Decimal('499.00'), cats.get('Bills & Utilities'), today - datetime.timedelta(days=13), 'upi'),
        ("Electricity & Water Shared Bill", Decimal('1450.00'), cats.get('Bills & Utilities'), today - datetime.timedelta(days=5), 'upi'),
        # Healthcare
        ("Dental Checkup & Cleaning", Decimal('1500.00'), cats.get('Healthcare'), today - datetime.timedelta(days=17), 'cash'),
        ("Vitamins & First Aid Supplies", Decimal('620.00'), cats.get('Healthcare'), today - datetime.timedelta(days=3), 'upi'),
        # Entertainment
        ("IMAX Movie Tickets with Popcorn", Decimal('780.00'), cats.get('Entertainment'), today - datetime.timedelta(days=8), 'upi'),
        ("Spotify Premium Student Plan", Decimal('119.00'), cats.get('Entertainment'), today - datetime.timedelta(days=21), 'upi'),
        # Personal Care
        ("Haircut & Grooming Salon", Decimal('450.00'), cats.get('Personal Care'), today - datetime.timedelta(days=12), 'cash'),
    ]

    for title, amount, cat, tx_date, method in expense_samples:
        if cat:
            Transaction.objects.create(
                user=user,
                title=title,
                amount=amount,
                transaction_type='expense',
                category=cat,
                date=tx_date,
                payment_method=method,
                notes="Paid and tracked on MoneyMate"
            )

    # 4. Create Budgets for the current month
    budget_data = [
        (cats.get('Food & Dining'), Decimal('7500.00')),    # Spent ~6690 (Warning 89%)
        (cats.get('Transportation'), Decimal('3000.00')),  # Spent ~2700 (90%)
        (cats.get('Education'), Decimal('6000.00')),       # Spent ~4699 (78%)
        (cats.get('Shopping'), Decimal('5000.00')),        # Spent ~6398 (Exceeded! 127%)
        (cats.get('Bills & Utilities'), Decimal('3500.00')),# Spent ~2948 (84%)
        (cats.get('Entertainment'), Decimal('2000.00')),   # Spent ~899 (45%)
    ]

    for cat, b_amount in budget_data:
        if cat:
            Budget.objects.create(
                user=user,
                category=cat,
                amount=b_amount,
                month=current_month,
                year=current_year
            )

    # 5. Create Savings Goals
    SavingsGoal.objects.create(
        user=user,
        name="Apple MacBook Pro M3",
        target_amount=Decimal('125000.00'),
        current_amount=Decimal('82500.00'),
        target_date=today + datetime.timedelta(days=75),
        category_icon='fa-laptop',
        color='#3B82F6',
        notes="Targeting end-of-semester purchase with internship savings"
    )

    SavingsGoal.objects.create(
        user=user,
        name="Emergency Contingency Fund",
        target_amount=Decimal('50000.00'),
        current_amount=Decimal('35000.00'),
        target_date=today + datetime.timedelta(days=120),
        category_icon='fa-piggy-bank',
        color='#10B981',
        notes="Aiming for 3 months worth of essential living costs"
    )

    SavingsGoal.objects.create(
        user=user,
        name="Goa Graduation Road Trip",
        target_amount=Decimal('20000.00'),
        current_amount=Decimal('16500.00'),
        target_date=today + datetime.timedelta(days=35),
        category_icon='fa-plane',
        color='#F59E0B',
        notes="Travel, resort stay, and scooter rentals with friends"
    )

    SavingsGoal.objects.create(
        user=user,
        name="Advanced Cloud Certification",
        target_amount=Decimal('15000.00'),
        current_amount=Decimal('15000.00'),
        target_date=today - datetime.timedelta(days=5),
        category_icon='fa-award',
        color='#8B5CF6',
        is_completed=True,
        notes="Achieved 100%! Ready to schedule AWS/GCP exam voucher"
    )

    # 6. Create Recurring Expenses
    RecurringExpense.objects.create(
        user=user,
        title="House / Hostel Monthly Rent",
        amount=Decimal('8500.00'),
        category=cats.get('Bills & Utilities'),
        frequency='monthly',
        payment_method='net_banking',
        start_date=today.replace(day=1),
        next_due_date=today + datetime.timedelta(days=20),
        is_active=True,
        notes="Due on the 1st of every month to landlord"
    )

    RecurringExpense.objects.create(
        user=user,
        title="Fiber Broadband Internet",
        amount=Decimal('999.00'),
        category=cats.get('Bills & Utilities'),
        frequency='monthly',
        payment_method='upi',
        start_date=today - datetime.timedelta(days=15),
        next_due_date=today + datetime.timedelta(days=15),
        is_active=True,
        notes="Auto-debit scheduled"
    )

    RecurringExpense.objects.create(
        user=user,
        title="Gym & Fitness Club Membership",
        amount=Decimal('1500.00'),
        category=cats.get('Personal Care'),
        frequency='monthly',
        payment_method='upi',
        start_date=today - datetime.timedelta(days=10),
        next_due_date=today + datetime.timedelta(days=20),
        is_active=True,
        notes="Monthly subscription plan"
    )

    # 7. Create Notifications
    Notification.objects.create(
        user=user,
        title="🚨 Budget Exceeded: Shopping",
        message="You have spent ₹6,398.00 against your ₹5,000.00 budget (127.9%) for Shopping.",
        notification_type='danger',
        link='/budgets/'
    )
    Notification.objects.create(
        user=user,
        title="⚠️ Budget Warning: Transportation",
        message="You have consumed 90% of your Transportation budget for this month.",
        notification_type='warning',
        link='/budgets/'
    )
    Notification.objects.create(
        user=user,
        title="🎉 Goal Completed: Cloud Certification",
        message="Congratulations! You have reached 100% of your target amount (₹15,000.00)!",
        notification_type='success',
        link='/savings/'
    )
    Notification.objects.create(
        user=user,
        title="💡 MoneyMate Tip",
        message="Track every small UPI transaction to keep your weekly spending insights razor sharp.",
        notification_type='info',
        link='/transactions/'
    )
