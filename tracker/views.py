import csv
import json
import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count, Avg
from django.db.models.functions import TruncMonth, TruncDate
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone

from .models import (
    Transaction, Category, Budget, SavingsGoal,
    RecurringExpense, Notification, UserProfile
)
from .forms import (
    UserRegistrationForm, UserProfileForm, TransactionForm,
    BudgetForm, SavingsGoalForm, SavingsContributionForm,
    RecurringExpenseForm, CategoryForm
)
from .utils import load_demo_data, check_budget_alerts


# ==========================================
# PUBLIC / AUTH VIEWS
# ==========================================

def landing_view(request):
    """Marketing and Landing Page for MoneyMate."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def register_view(request):
    """User Registration with currency preference and initial setup."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MoneyMate, {user.first_name or user.username}! Your account has been created.")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User Login with validation."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    """User Logout."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing')


# ==========================================
# DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    """Main Financial Dashboard with live metric cards and interactive charts."""
    user = request.user
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    # Total Income & Expenses (All time)
    total_income = Transaction.objects.filter(
        user=user, transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_expenses = Transaction.objects.filter(
        user=user, transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_balance = total_income - total_expenses

    # Current Month Spending & Budgets
    month_expenses = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__year=current_year,
        date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    month_income = Transaction.objects.filter(
        user=user,
        transaction_type='income',
        date__year=current_year,
        date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_budget_limit = Budget.objects.filter(
        user=user,
        year=current_year,
        month=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    remaining_budget = max(total_budget_limit - month_expenses, Decimal('0.00')) if total_budget_limit > 0 else Decimal('0.00')

    # Total Savings
    total_savings = SavingsGoal.objects.filter(user=user).aggregate(
        total=Sum('current_amount')
    )['total'] or Decimal('0.00')

    # Recent Transactions
    recent_transactions = Transaction.objects.filter(user=user).select_related('category')[:6]

    # --- CHART DATA PREPARATION ---

    # 1. Category-wise Expenses for current month
    cat_expenses = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__year=current_year,
        date__month=current_month
    ).values('category__name', 'category__color').annotate(total=Sum('amount')).order_by('-total')

    category_labels = []
    category_data = []
    category_colors = []

    for item in cat_expenses:
        name = item['category__name'] or 'Uncategorized'
        category_labels.append(name)
        category_data.append(float(item['total']))
        category_colors.append(item['category__color'] or '#10B981')

    # 2. Monthly Income vs Expenses (Last 6 Months)
    six_months_ago = today - datetime.timedelta(days=180)
    monthly_stats = []
    
    for i in range(5, -1, -1):
        target_month_date = today - datetime.timedelta(days=i*30)
        m_year = target_month_date.year
        m_month = target_month_date.month
        month_name = target_month_date.strftime('%b')

        m_inc = Transaction.objects.filter(
            user=user, transaction_type='income',
            date__year=m_year, date__month=m_month
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

        m_exp = Transaction.objects.filter(
            user=user, transaction_type='expense',
            date__year=m_year, date__month=m_month
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

        monthly_stats.append({
            'month': month_name,
            'income': float(m_inc),
            'expense': float(m_exp),
        })

    # 3. Weekly Spending Trends (Last 7 Days)
    weekly_labels = []
    weekly_expenses = []
    for d in range(6, -1, -1):
        day_date = today - datetime.timedelta(days=d)
        day_label = day_date.strftime('%a (%d)')
        day_exp = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date=day_date
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
        weekly_labels.append(day_label)
        weekly_expenses.append(float(day_exp))

    # Active Budgets status
    active_budgets = Budget.objects.filter(user=user, year=current_year, month=current_month).select_related('category')
    budget_alerts_count = sum(1 for b in active_budgets if b.is_warning() or b.is_exceeded())

    # Quick transaction form
    quick_tx_form = TransactionForm(user=user)

    context = {
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'month_expenses': month_expenses,
        'month_income': month_income,
        'total_budget_limit': total_budget_limit,
        'remaining_budget': remaining_budget,
        'total_savings': total_savings,
        'recent_transactions': recent_transactions,
        'active_budgets': active_budgets[:4],
        'budget_alerts_count': budget_alerts_count,
        'quick_tx_form': quick_tx_form,
        # JSON strings for Chart.js
        'chart_category_labels': json.dumps(category_labels),
        'chart_category_data': json.dumps(category_data),
        'chart_category_colors': json.dumps(category_colors),
        'chart_monthly_labels': json.dumps([m['month'] for m in monthly_stats]),
        'chart_monthly_income': json.dumps([m['income'] for m in monthly_stats]),
        'chart_monthly_expenses': json.dumps([m['expense'] for m in monthly_stats]),
        'chart_weekly_labels': json.dumps(weekly_labels),
        'chart_weekly_expenses': json.dumps(weekly_expenses),
    }

    return render(request, 'tracker/dashboard.html', context)


# ==========================================
# TRANSACTIONS MANAGEMENT
# ==========================================

@login_required
def transactions_view(request):
    """Full Transactions list with search, multi-faceted filtering, sorting and pagination."""
    user = request.user
    qs = Transaction.objects.filter(user=user).select_related('category')

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(notes__icontains=q) | Q(category__name__icontains=q))

    # Transaction type filter
    tx_type = request.GET.get('type', '')
    if tx_type in ['expense', 'income']:
        qs = qs.filter(transaction_type=tx_type)

    # Category filter
    category_id = request.GET.get('category', '')
    if category_id:
        qs = qs.filter(category_id=category_id)

    # Payment method filter
    payment_method = request.GET.get('payment_method', '')
    if payment_method:
        qs = qs.filter(payment_method=payment_method)

    # Date range filter
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    # Amount range filter
    min_amount = request.GET.get('min_amount', '')
    max_amount = request.GET.get('max_amount', '')
    if min_amount:
        try:
            qs = qs.filter(amount__gte=Decimal(min_amount))
        except Exception:
            pass
    if max_amount:
        try:
            qs = qs.filter(amount__lte=Decimal(max_amount))
        except Exception:
            pass

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        qs = qs.order_by('date', 'created_at')
    elif sort_by == 'highest':
        qs = qs.order_by('-amount')
    elif sort_by == 'lowest':
        qs = qs.order_by('amount')
    else:  # newest default
        qs = qs.order_by('-date', '-created_at')

    # Aggregates for the filtered dataset
    filtered_spending = qs.filter(transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    filtered_income = qs.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    # Pagination
    paginator = Paginator(qs, 12)  # 12 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # User categories for filter dropdown
    categories = Category.objects.filter(Q(user=None) | Q(user=user)).order_by('category_type', 'name')
    tx_form = TransactionForm(user=user)

    context = {
        'page_obj': page_obj,
        'transactions': page_obj.object_list,
        'filtered_spending': filtered_spending,
        'filtered_income': filtered_income,
        'categories': categories,
        'tx_form': tx_form,
        'payment_methods': Transaction.PAYMENT_METHODS,
        # Preserve query params for pagination
        'current_q': q,
        'current_type': tx_type,
        'current_category': category_id,
        'current_payment_method': payment_method,
        'current_start_date': start_date,
        'current_end_date': end_date,
        'current_sort': sort_by,
        'current_min_amount': min_amount,
        'current_max_amount': max_amount,
    }
    return render(request, 'tracker/transactions.html', context)


@login_required
def transaction_add_view(request):
    """Add new expense or income transaction."""
    if request.method == 'POST':
        form = TransactionForm(user=request.user, data=request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.save()
            check_budget_alerts(request.user, tx.category, tx.date.year, tx.date.month)
            messages.success(request, f"Transaction '{tx.title}' for {request.user.profile.currency}{tx.amount:,.2f} added successfully!")
            return redirect('transactions')
        else:
            messages.error(request, "Failed to save transaction. Please check your inputs.")
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'tracker/transaction_form.html', {'form': form, 'title': 'Add Transaction'})


@login_required
def transaction_edit_view(request, pk):
    """Edit existing transaction."""
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(user=request.user, data=request.POST, instance=tx)
        if form.is_valid():
            tx = form.save()
            check_budget_alerts(request.user, tx.category, tx.date.year, tx.date.month)
            messages.success(request, f"Transaction '{tx.title}' updated successfully!")
            return redirect('transactions')
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        form = TransactionForm(user=request.user, instance=tx)

    return render(request, 'tracker/transaction_form.html', {'form': form, 'title': 'Edit Transaction', 'transaction': tx})


@login_required
def transaction_delete_view(request, pk):
    """Delete transaction."""
    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        title = tx.title
        tx.delete()
        messages.success(request, f"Transaction '{title}' deleted.")
        return redirect('transactions')
    return render(request, 'tracker/transaction_confirm_delete.html', {'transaction': tx})


# ==========================================
# BUDGET MANAGEMENT
# ==========================================

@login_required
def budgets_view(request):
    """Budget Management Page with progress bars, warning alerts, and monthly breakdown."""
    user = request.user
    today = timezone.now().date()

    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))

    budgets = Budget.objects.filter(
        user=user,
        year=selected_year,
        month=selected_month
    ).select_related('category')

    # Calculate overall totals for this month
    total_budgeted = budgets.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    # Total expenses for this month
    total_spent = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__year=selected_year,
        date__month=selected_month
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    total_remaining = total_budgeted - total_spent
    overall_percentage = round((total_spent / total_budgeted * 100), 1) if total_budgeted > 0 else 0

    # Check for budget warnings and exceedances
    warning_budgets = []
    exceeded_budgets = []
    budget_items = []

    for b in budgets:
        spent = b.get_spent_amount()
        pct = b.get_raw_spent_percentage()
        remaining = b.amount - spent
        is_warn = pct >= 80 and pct <= 100
        is_exceed = pct > 100

        if is_warn:
            warning_budgets.append(b)
        if is_exceed:
            exceeded_budgets.append(b)

        budget_items.append({
            'budget': b,
            'spent': spent,
            'percentage': min(pct, 100),
            'raw_percentage': pct,
            'remaining': remaining,
            'is_warn': is_warn,
            'is_exceed': is_exceed,
        })

    budget_form = BudgetForm(user=user, initial={'month': selected_month, 'year': selected_year})

    # Available months and years
    months_list = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    years_list = [today.year - 1, today.year, today.year + 1]

    context = {
        'budget_items': budget_items,
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'total_remaining': total_remaining,
        'overall_percentage': min(overall_percentage, 100),
        'raw_overall_percentage': overall_percentage,
        'warning_budgets': warning_budgets,
        'exceeded_budgets': exceeded_budgets,
        'budget_form': budget_form,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_name': datetime.date(selected_year, selected_month, 1).strftime('%B'),
        'months_list': months_list,
        'years_list': years_list,
    }
    return render(request, 'tracker/budgets.html', context)


@login_required
def budget_add_view(request):
    """Add or update category budget."""
    if request.method == 'POST':
        form = BudgetForm(user=request.user, data=request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            amount = form.cleaned_data['amount']

            budget, created = Budget.objects.update_or_create(
                user=request.user,
                category=category,
                month=month,
                year=year,
                defaults={'amount': amount}
            )
            action_text = "created" if created else "updated"
            messages.success(request, f"Budget for {category.name} ({month}/{year}) {action_text} to {request.user.profile.currency}{amount:,.2f}!")
            return redirect(f"/budgets/?month={month}&year={year}")
        else:
            messages.error(request, "Failed to save budget. Please check your inputs.")
    return redirect('budgets')


@login_required
def budget_delete_view(request, pk):
    """Delete a budget limit."""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    month = budget.month
    year = budget.year
    cat_name = budget.category.name
    budget.delete()
    messages.success(request, f"Budget for {cat_name} removed.")
    return redirect(f"/budgets/?month={month}&year={year}")


@login_required
def budget_reset_view(request):
    """Roll over or reset budgets into the current or next month without deleting transactions."""
    user = request.user
    today = timezone.now().date()
    target_month = int(request.POST.get('target_month', today.month))
    target_year = int(request.POST.get('target_year', today.year))
    source_month = int(request.POST.get('source_month', today.month - 1 if today.month > 1 else 12))
    source_year = int(request.POST.get('source_year', today.year if today.month > 1 else today.year - 1))

    source_budgets = Budget.objects.filter(user=user, month=source_month, year=source_year)
    count = 0
    for b in source_budgets:
        Budget.objects.update_or_create(
            user=user,
            category=b.category,
            month=target_month,
            year=target_year,
            defaults={'amount': b.amount}
        )
        count += 1

    messages.success(request, f"Successfully copied {count} budget categories into {datetime.date(target_year, target_month, 1).strftime('%B %Y')}!")
    return redirect(f"/budgets/?month={target_month}&year={target_year}")


# ==========================================
# SAVINGS GOALS
# ==========================================

@login_required
def savings_view(request):
    """Savings Goals Page with progress meters, contribution tracking and days remaining."""
    user = request.user
    goals = SavingsGoal.objects.filter(user=user)

    total_target = goals.aggregate(t=Sum('target_amount'))['t'] or Decimal('0.00')
    total_saved = goals.aggregate(t=Sum('current_amount'))['t'] or Decimal('0.00')
    overall_progress = round((total_saved / total_target * 100), 1) if total_target > 0 else 0

    completed_count = goals.filter(is_completed=True).count()
    active_count = goals.filter(is_completed=False).count()

    goal_form = SavingsGoalForm()
    contribution_form = SavingsContributionForm()

    context = {
        'goals': goals,
        'total_target': total_target,
        'total_saved': total_saved,
        'overall_progress': min(overall_progress, 100),
        'completed_count': completed_count,
        'active_count': active_count,
        'goal_form': goal_form,
        'contribution_form': contribution_form,
    }
    return render(request, 'tracker/savings.html', context)


@login_required
def savings_add_view(request):
    """Create new savings goal."""
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            if goal.current_amount >= goal.target_amount:
                goal.is_completed = True
            goal.save()
            messages.success(request, f"Savings Goal '{goal.name}' created successfully!")
            return redirect('savings')
        else:
            messages.error(request, "Failed to create savings goal. Please review your inputs.")
    return redirect('savings')


@login_required
def savings_contribute_view(request, pk):
    """Add money / deposit into savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SavingsContributionForm(request.POST)
        if form.is_valid():
            added_amount = form.cleaned_data['amount']
            goal.current_amount += added_amount
            if goal.current_amount >= goal.target_amount:
                goal.is_completed = True
                Notification.objects.create(
                    user=request.user,
                    title=f"🎉 Goal Completed: {goal.name}!",
                    message=f"Outstanding! You've successfully hit your target of {request.user.profile.currency}{goal.target_amount:,.2f} for '{goal.name}'.",
                    notification_type='success',
                    link='/savings/'
                )
                messages.success(request, f"🎉 Woohoo! Goal '{goal.name}' has reached 100% of target!")
            else:
                messages.success(request, f"Added {request.user.profile.currency}{added_amount:,.2f} to '{goal.name}'. Current progress: {goal.get_progress_percentage()}%")
            goal.save()
            return redirect('savings')
    return redirect('savings')


@login_required
def savings_toggle_complete_view(request, pk):
    """Toggle completion status of savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    goal.is_completed = not goal.is_completed
    goal.save()
    status = "completed" if goal.is_completed else "marked active"
    messages.info(request, f"Goal '{goal.name}' {status}.")
    return redirect('savings')


@login_required
def savings_delete_view(request, pk):
    """Delete a savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    name = goal.name
    goal.delete()
    messages.success(request, f"Savings Goal '{name}' deleted.")
    return redirect('savings')


# ==========================================
# REPORTS & ANALYTICS
# ==========================================

@login_required
def reports_view(request):
    """Comprehensive financial reports, category breakdowns, monthly trends, and export options."""
    user = request.user
    today = timezone.now().date()

    # Timeframe selection: 'month', 'year', 'all'
    timeframe = request.GET.get('timeframe', 'month')
    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))

    qs = Transaction.objects.filter(user=user)

    if timeframe == 'month':
        qs = qs.filter(date__year=selected_year, date__month=selected_month)
        report_title = f"{datetime.date(selected_year, selected_month, 1).strftime('%B %Y')} Financial Report"
    elif timeframe == 'year':
        qs = qs.filter(date__year=selected_year)
        report_title = f"Annual Financial Report ({selected_year})"
    else:
        report_title = "All-Time Financial Report"

    # Aggregates
    total_income = qs.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    total_expenses = qs.filter(transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    net_savings = total_income - total_expenses
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0

    # Category breakdown (Expenses)
    category_breakdown = qs.filter(transaction_type='expense').values(
        'category__name', 'category__icon', 'category__color'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    cat_list = []
    cat_names = []
    cat_amounts = []
    cat_colors = []

    for item in category_breakdown:
        name = item['category__name'] or 'Uncategorized'
        amt = item['total']
        pct = round((amt / total_expenses * 100), 1) if total_expenses > 0 else 0
        cat_list.append({
            'name': name,
            'icon': item['category__icon'] or 'fa-tag',
            'color': item['category__color'] or '#10B981',
            'total': amt,
            'count': item['count'],
            'percentage': pct,
        })
        cat_names.append(name)
        cat_amounts.append(float(amt))
        cat_colors.append(item['category__color'] or '#10B981')

    # Monthly Trend (Past 12 Months)
    monthly_trends = []
    for m_offset in range(11, -1, -1):
        d = today - datetime.timedelta(days=m_offset * 30)
        y = d.year
        m = d.month
        m_label = d.strftime('%b %y')

        inc = Transaction.objects.filter(
            user=user, transaction_type='income', date__year=y, date__month=m
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

        exp = Transaction.objects.filter(
            user=user, transaction_type='expense', date__year=y, date__month=m
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

        monthly_trends.append({
            'label': m_label,
            'income': float(inc),
            'expense': float(exp),
            'net': float(inc - exp),
        })

    # Payment Method Breakdown
    payment_breakdown = qs.filter(transaction_type='expense').values('payment_method').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'timeframe': timeframe,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'report_title': report_title,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'savings_rate': savings_rate,
        'category_breakdown': cat_list,
        'highest_spending_category': cat_list[0] if cat_list else None,
        'payment_breakdown': payment_breakdown,
        'chart_cat_names': json.dumps(cat_names),
        'chart_cat_amounts': json.dumps(cat_amounts),
        'chart_cat_colors': json.dumps(cat_colors),
        'chart_trend_labels': json.dumps([t['label'] for t in monthly_trends]),
        'chart_trend_income': json.dumps([t['income'] for t in monthly_trends]),
        'chart_trend_expense': json.dumps([t['expense'] for t in monthly_trends]),
    }
    return render(request, 'tracker/reports.html', context)


@login_required
def export_csv_view(request):
    """Export filtered or all transactions as a CSV spreadsheet."""
    user = request.user
    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="moneymate_transactions_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Title', 'Type', 'Category', 'Amount', 'Currency', 'Payment Method', 'Notes', 'Recurring'])

    transactions = Transaction.objects.filter(user=user).select_related('category').order_by('-date', '-created_at')
    currency = user.profile.currency

    for tx in transactions:
        writer.writerow([
            tx.date.strftime('%Y-%m-%d'),
            tx.title,
            tx.get_transaction_type_display(),
            tx.category.name if tx.category else 'Uncategorized',
            f"{tx.amount:.2f}",
            currency,
            tx.get_payment_method_display(),
            tx.notes or '',
            'Yes' if tx.is_recurring else 'No',
        ])

    return response


@login_required
def report_print_view(request):
    """Printable / PDF-ready financial statement."""
    user = request.user
    today = timezone.now().date()
    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))

    transactions = Transaction.objects.filter(
        user=user, date__year=selected_year, date__month=selected_month
    ).select_related('category').order_by('date')

    total_income = transactions.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    total_expenses = transactions.filter(transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    net_savings = total_income - total_expenses

    category_breakdown = transactions.filter(transaction_type='expense').values(
        'category__name'
    ).annotate(total=Sum('amount')).order_by('-total')

    context = {
        'selected_month_name': datetime.date(selected_year, selected_month, 1).strftime('%B %Y'),
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'category_breakdown': category_breakdown,
        'generated_date': today,
    }
    return render(request, 'tracker/report_print.html', context)


# ==========================================
# RECURRING EXPENSES
# ==========================================

@login_required
def recurring_view(request):
    """Manage subscriptions and recurring bills."""
    user = request.user
    recurring_items = RecurringExpense.objects.filter(user=user).select_related('category')
    form = RecurringExpenseForm(user=user)

    total_monthly_committed = Decimal('0.00')
    for item in recurring_items:
        if item.is_active:
            if item.frequency == 'monthly':
                total_monthly_committed += item.amount
            elif item.frequency == 'yearly':
                total_monthly_committed += (item.amount / Decimal('12.00'))
            elif item.frequency == 'weekly':
                total_monthly_committed += (item.amount * Decimal('4.33'))
            elif item.frequency == 'daily':
                total_monthly_committed += (item.amount * Decimal('30.00'))

    context = {
        'recurring_items': recurring_items,
        'form': form,
        'total_monthly_committed': total_monthly_committed,
    }
    return render(request, 'tracker/recurring.html', context)


@login_required
def recurring_add_view(request):
    """Add a new recurring expense rule."""
    if request.method == 'POST':
        form = RecurringExpenseForm(user=request.user, data=request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, f"Recurring Expense '{item.title}' registered!")
            return redirect('recurring')
        else:
            messages.error(request, "Failed to create recurring expense. Check inputs.")
    return redirect('recurring')


@login_required
def recurring_process_view(request, pk):
    """Process a recurring expense now (creates an actual transaction entry)."""
    item = get_object_or_404(RecurringExpense, pk=pk, user=request.user)
    today = timezone.now().date()
    
    # Create the transaction
    Transaction.objects.create(
        user=request.user,
        title=f"{item.title} (Auto Recurring)",
        amount=item.amount,
        transaction_type='expense',
        category=item.category,
        date=today,
        payment_method=item.payment_method,
        notes=f"Generated from recurring rule: {item.title}",
        is_recurring=True
    )
    
    # Bump next due date
    if item.frequency == 'monthly':
        # Add ~30 days
        item.next_due_date = item.next_due_date + datetime.timedelta(days=30)
    elif item.frequency == 'weekly':
        item.next_due_date = item.next_due_date + datetime.timedelta(days=7)
    elif item.frequency == 'yearly':
        item.next_due_date = item.next_due_date + datetime.timedelta(days=365)
    elif item.frequency == 'daily':
        item.next_due_date = item.next_due_date + datetime.timedelta(days=1)
    item.save()

    messages.success(request, f"Transaction recorded for '{item.title}' ({request.user.profile.currency}{item.amount:,.2f})!")
    return redirect('recurring')


@login_required
def recurring_delete_view(request, pk):
    """Delete a recurring expense."""
    item = get_object_or_404(RecurringExpense, pk=pk, user=request.user)
    title = item.title
    item.delete()
    messages.success(request, f"Recurring expense '{title}' removed.")
    return redirect('recurring')


# ==========================================
# PROFILE & SETTINGS
# ==========================================

@login_required
def profile_view(request):
    """User profile settings, currency picker, theme preferences, and demo data generator."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

            profile.currency = request.POST.get('currency', profile.currency)
            profile.theme = request.POST.get('theme', profile.theme)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.occupation = request.POST.get('occupation', profile.occupation)
            profile.save()

            messages.success(request, "Profile and preferences updated successfully!")
            return redirect('profile')

        elif action == 'change_password':
            pwd_form = PasswordChangeForm(user, request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                messages.success(request, "Your password was successfully updated! Please log in with your new password.")
                return redirect('login')
            else:
                for error in pwd_form.errors.values():
                    messages.error(request, error)
                return redirect('profile')

    pwd_form = PasswordChangeForm(user)
    context = {
        'profile': profile,
        'pwd_form': pwd_form,
        'currency_choices': UserProfile.CURRENCY_CHOICES,
    }
    return render(request, 'tracker/profile.html', context)


@login_required
def load_demo_view(request):
    """Quickly seeds comprehensive demo data for the current user."""
    load_demo_data(request.user)
    messages.success(request, "🎉 Demo data loaded successfully! Explore transactions, interactive charts, budgets, and savings goals.")
    return redirect('dashboard')


@login_required
def clear_data_view(request):
    """Wipes all transactions, budgets, goals for the current user."""
    if request.method == 'POST':
        Transaction.objects.filter(user=request.user).delete()
        Budget.objects.filter(user=request.user).delete()
        SavingsGoal.objects.filter(user=request.user).delete()
        RecurringExpense.objects.filter(user=request.user).delete()
        Notification.objects.filter(user=request.user).delete()
        messages.warning(request, "All financial records and data have been reset.")
        return redirect('dashboard')
    return redirect('profile')


# ==========================================
# NOTIFICATIONS
# ==========================================

@login_required
def notifications_view(request):
    """View all system notifications and alerts."""
    user = request.user
    notifications = Notification.objects.filter(user=user)
    # Mark all as read when visited
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'tracker/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read_view(request, pk):
    """Mark a single notification as read."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications')
