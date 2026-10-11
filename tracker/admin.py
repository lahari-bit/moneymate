from django.contrib import admin
from .models import UserProfile, Category, Transaction, Budget, SavingsGoal, RecurringExpense, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'theme', 'occupation', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'user', 'is_default', 'icon', 'color')
    list_filter = ('category_type', 'is_default')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'amount', 'transaction_type', 'category', 'payment_method', 'date')
    list_filter = ('transaction_type', 'payment_method', 'date', 'category')
    search_fields = ('title', 'notes', 'user__username')
    date_hierarchy = 'date'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'month', 'year')
    list_filter = ('month', 'year')
    search_fields = ('user__username', 'category__name')

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_amount', 'current_amount', 'target_date', 'is_completed')
    list_filter = ('is_completed', 'target_date')
    search_fields = ('name', 'user__username')

@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'amount', 'frequency', 'next_due_date', 'is_active')
    list_filter = ('frequency', 'is_active')
    search_fields = ('title', 'user__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'user__username')
