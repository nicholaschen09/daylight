from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **options):
        self.stdout.write("Implement your seed logic here")
