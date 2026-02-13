from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from patients.models import PressureData
import csv
from io import TextIOWrapper
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Simulate CSV upload and report inserted PressureData rows'

    def add_arguments(self, parser):
        parser.add_argument('--csv', required=True, help='Path to CSV file')
        parser.add_argument('--username', required=True, help='Patient username to attach data to')
        parser.add_argument('--date', required=False, help='Date (YYYY-MM-DD) for timestamp', default=None)

    def handle(self, *args, **options):
        csv_path = options['csv']
        username = options['username']
        date_str = options['date']

        try:
            patient = User.objects.get(username=username, role='patient')
        except User.DoesNotExist:
            raise CommandError(f"Patient user '{username}' not found")

        if date_str:
            from datetime import datetime
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid date format, use YYYY-MM-DD')
        else:
            date = timezone.now().date()

        required_headers = {'sensor_location', 'pressure_value'}

        inserted = 0
        with open(csv_path, 'rb') as f:
            text_wrapper = TextIOWrapper(f, encoding='utf-8', newline='')
            # peek headers
            reader = csv.DictReader(text_wrapper)
            fieldnames = reader.fieldnames or []

            def looks_like_numeric_header(names):
                if not names:
                    return True
                for n in names:
                    s = n.strip()
                    if s == '':
                        return True
                    try:
                        float(s)
                    except ValueError:
                        return False
                return True

            if required_headers.issubset({f.strip() for f in fieldnames}):
                # normal two-column CSV
                text_wrapper.seek(0)
                reader = csv.DictReader(text_wrapper)
                for row in reader:
                    try:
                        sensor_location = row.get('sensor_location')
                        pressure_value = float(row.get('pressure_value'))
                    except (TypeError, ValueError):
                        continue
                    from datetime import datetime as _dt, time as _time
                    timestamp = _dt.combine(date, _time.min).replace(tzinfo=timezone.get_current_timezone())
                    PressureData.objects.create(
                        patient=patient,
                        sensor_location=sensor_location,
                        pressure_value=pressure_value,
                        timestamp=timestamp
                    )
                    inserted += 1
            elif looks_like_numeric_header(fieldnames):
                # headerless numeric matrix
                text_wrapper.seek(0)
                matrix_reader = csv.reader(text_wrapper)
                from datetime import datetime as _dt, time as _time
                timestamp = _dt.combine(date, _time.min).replace(tzinfo=timezone.get_current_timezone())
                objs = []
                batch_size = 2000
                for r_idx, row in enumerate(matrix_reader):
                    for c_idx, cell in enumerate(row):
                        cell = cell.strip()
                        if cell == '':
                            continue
                        try:
                            pressure_value = float(cell)
                        except ValueError:
                            continue
                        sensor_location = f"r{r_idx}_c{c_idx}"
                        objs.append(PressureData(
                            patient=patient,
                            sensor_location=sensor_location,
                            pressure_value=pressure_value,
                            timestamp=timestamp
                        ))
                        if len(objs) >= batch_size:
                            PressureData.objects.bulk_create(objs)
                            inserted += len(objs)
                            objs = []
                if objs:
                    PressureData.objects.bulk_create(objs)
                    inserted += len(objs)
            else:
                raise CommandError('CSV must include headers or be a numeric matrix')

        self.stdout.write(self.style.SUCCESS(f'Inserted {inserted} PressureData rows for {username}'))
