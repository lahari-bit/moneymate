from django.urls import path
from . import views

urlpatterns = [
    # Public & Auth
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Core Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Transactions
    path('transactions/', views.transactions_view, name='transactions'),
    path('transactions/add/', views.transaction_add_view, name='transaction_add'),
    path('transactions/<int:pk>/edit/', views.transaction_edit_view, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete_view, name='transaction_delete'),

    # Budgets
    path('budgets/', views.budgets_view, name='budgets'),
    path('budgets/add/', views.budget_add_view, name='budget_add'),
    path('budgets/<int:pk>/delete/', views.budget_delete_view, name='budget_delete'),
    path('budgets/reset/', views.budget_reset_view, name='budget_reset'),

    # Savings Goals
    path('savings/', views.savings_view, name='savings'),
    path('savings/add/', views.savings_add_view, name='savings_add'),
    path('savings/<int:pk>/contribute/', views.savings_contribute_view, name='savings_contribute'),
    path('savings/<int:pk>/toggle/', views.savings_toggle_complete_view, name='savings_toggle'),
    path('savings/<int:pk>/delete/', views.savings_delete_view, name='savings_delete'),

    # Reports & Analytics
    path('reports/', views.reports_view, name='reports'),
    path('reports/export-csv/', views.export_csv_view, name='export_csv'),
    path('reports/print/', views.report_print_view, name='report_print'),

    # Recurring Expenses
    path('recurring/', views.recurring_view, name='recurring'),
    path('recurring/add/', views.recurring_add_view, name='recurring_add'),
    path('recurring/<int:pk>/process/', views.recurring_process_view, name='recurring_process'),
    path('recurring/<int:pk>/delete/', views.recurring_delete_view, name='recurring_delete'),

    # Settings & Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/load-demo/', views.load_demo_view, name='load_demo_data'),
    path('profile/clear-data/', views.clear_data_view, name='clear_data'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='mark_notification_read'),
]
