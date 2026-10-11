from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Category

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # Ensure system default categories exist safely
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

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
