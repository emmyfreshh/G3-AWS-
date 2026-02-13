from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import CustomUserCreationForm, CSVUploadForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from patients.models import PressureData
import csv
from io import TextIOWrapper
from django.utils import timezone
from django.contrib import messages
import tempfile
import os

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def create_user(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return render(request, '403.html')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if request.user.is_superuser:
            form.fields['role'].choices = [('patient', 'Patient'), ('clinician', 'Clinician'), ('admin', 'Admin')]
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
        if request.user.is_superuser:
            form.fields['role'].choices = [('patient', 'Patient'), ('clinician', 'Clinician'), ('admin', 'Admin')]
    return render(request, 'users/create_user.html', {'form': form})

@login_required
def user_list(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return render(request, '403.html')
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

@login_required
def delete_user(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return render(request, '403.html')
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'users/delete_user.html', {'user': user})

@login_required
def reset_password(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return render(request, '403.html')
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        user.set_password(new_password)
        user.save()
        return redirect('user_list')
    return render(request, 'users/reset_password.html', {'user': user})

@login_required
def assign_clinician(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return render(request, '403.html')
    patient = get_object_or_404(User, id=user_id, role='patient')
    if request.method == 'POST':
        clinician_id = request.POST.get('clinician')
        if clinician_id:
            clinician = get_object_or_404(User, id=clinician_id, role='clinician')
            patient.clinician = clinician
        else:
            patient.clinician = None
        patient.save()
        return redirect('user_list')
    clinicians = User.objects.filter(role='clinician')
    return render(request, 'users/assign_clinician.html', {'patient': patient, 'clinicians': clinicians})

@login_required
def upload_csv(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return render(request, '403.html')
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.cleaned_data['patient']
            csv_file = request.FILES['csv_file']
            date = form.cleaned_data['date']
            # Process CSV immediately and show success message
            try:
                # Wrap uploaded file stream for csv parsing
                file_stream = getattr(csv_file, 'file', csv_file)
                text_wrapper = TextIOWrapper(file_stream, encoding='utf-8', newline='')
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

                required_headers = {'sensor_location', 'pressure_value'}

                if required_headers.issubset({f.strip() for f in fieldnames}):
                    text_wrapper.seek(0)
                    reader = csv.DictReader(text_wrapper)
                    from datetime import datetime as _dt, time as _time
                    timestamp = _dt.combine(date, _time.min).replace(tzinfo=timezone.get_current_timezone())
                    for row in reader:
                        try:
                            sensor_location = row.get('sensor_location')
                            pressure_value = float(row.get('pressure_value'))
                        except (TypeError, ValueError):
                            continue
                        PressureData.objects.create(
                            patient=patient,
                            sensor_location=sensor_location,
                            pressure_value=pressure_value,
                            timestamp=timestamp
                        )
                elif looks_like_numeric_header(fieldnames):
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
                                objs = []
                    if objs:
                        PressureData.objects.bulk_create(objs)
                else:
                    form.add_error('csv_file', 'CSV must include headers or be a numeric matrix')
                    return render(request, 'users/upload_csv.html', {'form': form})
            except Exception as e:
                form.add_error('csv_file', f'Error processing CSV: {e}')
                return render(request, 'users/upload_csv.html', {'form': form})

            messages.success(request, 'CSV uploaded and imported successfully')
            return redirect('user_list')
    else:
        form = CSVUploadForm()
    return render(request, 'users/upload_csv.html', {'form': form})
