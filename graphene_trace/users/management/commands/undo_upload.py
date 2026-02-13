from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from patients.models import PressureData

User = get_user_model()


class Command(BaseCommand):
    help = 'Undo uploads by deleting PressureData matching a sensor prefix for a user and optional date'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Patient username')
        parser.add_argument('--prefix', required=False, help="Sensor_location prefix to match (e.g., 'r')", default=None)
        parser.add_argument('--date', required=False, help='Date (YYYY-MM-DD) to filter timestamp', default=None)

    def handle(self, *args, **options):
        username = options['username']
        prefix = options['prefix']
        date_str = options['date']

        try:
            patient = User.objects.get(username=username, role='patient')
        except User.DoesNotExist:
            raise CommandError(f"Patient user '{username}' not found")

        qs = PressureData.objects.filter(patient=patient)
        if prefix:
            qs = qs.filter(sensor_location__startswith=prefix)
        if date_str:
            from datetime import datetime, timezone as _tz
            try:
                d = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid date format, use YYYY-MM-DD')
            from django.utils import timezone
            start = timezone.datetime.combine(d, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
            end = timezone.datetime.combine(d, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone())
            qs = qs.filter(timestamp__range=(start, end))

        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING('No matching rows found'))
            return

        # For very large deletes, perform raw SQL to avoid instantiating large querysets
        if count > 100000:
            from django.db import connection
            sql = 'DELETE FROM patients_pressuredata WHERE patient_id = %s'
            params = [patient.id]
            if prefix:
                sql += ' AND sensor_location LIKE %s'
                params.append(prefix + '%')
            if date_str:
                from django.utils import timezone
                start = timezone.datetime.combine(d, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
                end = timezone.datetime.combine(d, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone())
                sql += ' AND timestamp BETWEEN %s AND %s'
                params.extend([start, end])
            with connection.cursor() as cur:
                cur.execute(sql, params)
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} PressureData rows for {username} (raw SQL)'))
        else:
            qs.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} PressureData rows for {username}'))
