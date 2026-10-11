from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import UserProfile
from tracker.utils import load_demo_data

class Command(BaseCommand):
    help = 'Seeds standard categories and creates a ready-to-test demo account (demo / demo12345)'

    def handle(self, *args, **options):
        username = 'demo'
        email = 'demo@moneymate.app'
        password = 'demo12345'

        user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'first_name': 'Alex', 'last_name': 'Sharma'})
        user.set_password(password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.currency = '₹'
        profile.occupation = 'Computer Science Student'
        profile.save()

        load_demo_data(user)

        self.stdout.write(self.style.SUCCESS(f"Successfully configured demo user: '{username}' with password: '{password}'"))
        self.stdout.write(self.style.SUCCESS("All transactions, budgets, savings goals, and alerts have been populated!"))
