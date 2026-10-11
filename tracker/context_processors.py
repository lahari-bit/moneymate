from .models import Notification, UserProfile, Category
from django.db.models import Q

def global_context(request):
    """Provides common context data such as active currency, unread notifications count, and categories."""
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            currency = profile.currency
        except (UserProfile.DoesNotExist, AttributeError):
            currency = '₹'
            profile = None

        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]

        # Categories available to user
        available_categories = Category.objects.filter(
            Q(user=None) | Q(user=request.user)
        ).order_by('category_type', 'name')

        return {
            'user_profile': profile,
            'user_currency': currency,
            'unread_notifications_count': unread_notifications,
            'recent_notifications': recent_notifications,
            'global_categories': available_categories,
        }
    return {
        'user_currency': '₹',
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'global_categories': [],
    }
