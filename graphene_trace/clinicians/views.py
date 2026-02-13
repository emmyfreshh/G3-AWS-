from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from patients.models import PressureData, Comment, Notification
from django.contrib.auth import get_user_model
from patients.forms import CommentForm

User = get_user_model()

@login_required
def patient_list(request):
    if request.user.role != 'clinician':
        return render(request, '403.html')
    filter_alerts = request.GET.get('filter_alerts', False)
    patients = User.objects.filter(role='patient')
    if filter_alerts:
        patients = patients.filter(notifications__is_read=False).distinct()
    patients_with_alerts = []
    for patient in patients:
        alerts = Notification.objects.filter(patient=patient, is_read=False).count()
        patients_with_alerts.append((patient, alerts))
    return render(request, 'clinicians/patient_list.html', {'patients': patients_with_alerts, 'filter_alerts': filter_alerts})

@login_required
def patient_detail(request, patient_id):
    if request.user.role != 'clinician':
        return render(request, '403.html')
    patient = get_object_or_404(User, id=patient_id, role='patient')
    recent_data = PressureData.objects.filter(patient=patient).order_by('-timestamp')[:50]
    return render(request, 'clinicians/patient_detail.html', {'patient': patient, 'recent_data': recent_data})

@login_required
def patient_history(request, patient_id):
    if request.user.role != 'clinician':
        return render(request, '403.html')
    patient = get_object_or_404(User, id=patient_id, role='patient')
    data = PressureData.objects.filter(patient=patient).order_by('-timestamp')[:100]
    labels = [d.timestamp.strftime('%Y-%m-%d %H:%M') for d in reversed(data)]
    values = [d.pressure_value for d in reversed(data)]
    return render(request, 'clinicians/patient_history.html', {
        'patient': patient,
        'data': data,
        'labels': labels,
        'values': values,
    })

@login_required
def patient_comments(request, patient_id):
    if request.user.role != 'clinician':
        return render(request, '403.html')
    patient = get_object_or_404(User, id=patient_id, role='patient')
    if request.method == 'POST':
        form = CommentForm(request.POST, user=patient)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.patient = patient
            comment.clinician = request.user
            comment.is_reply = True
            comment.save()
            return redirect('patient_comments', patient_id=patient_id)
    else:
        form = CommentForm(user=patient)
    comments = Comment.objects.filter(patient=patient).order_by('-timestamp')
    return render(request, 'clinicians/patient_comments.html', {'patient': patient, 'comments': comments, 'form': form})


@login_required
def patient_live_grid_json(request, patient_id):
    # Clinician API: return latest grid for patient
    if request.user.role != 'clinician':
        return JsonResponse({'error': 'forbidden'}, status=403)
    patient = get_object_or_404(User, id=patient_id, role='patient')
    latest = PressureData.objects.filter(patient=patient).order_by('-timestamp').values_list('timestamp', flat=True).first()
    if not latest:
        return JsonResponse({'cells': []})
    rows = PressureData.objects.filter(patient=patient, timestamp=latest)
    cells = []
    import re
    coord_re = re.compile(r'^r(\d+)_c(\d+)$')
    for p in rows:
        m = coord_re.match(p.sensor_location)
        if m:
            r = int(m.group(1))
            c = int(m.group(2))
            cells.append({'r': r, 'c': c, 'value': p.pressure_value})
        else:
            cells.append({'label': p.sensor_location, 'value': p.pressure_value})
    return JsonResponse({'cells': cells, 'timestamp': latest.isoformat()})
    # Simple repositioning heuristic similar to patient endpoint
    reposition = None
    try:
        recent_timestamps = PressureData.objects.filter(patient=patient).order_by('-timestamp').values_list('timestamp', flat=True).distinct()[:3]
        top_locations = []
        for ts in recent_timestamps:
            rows_ts = PressureData.objects.filter(patient=patient, timestamp=ts)
            if not rows_ts:
                continue
            top = max(rows_ts, key=lambda p: p.pressure_value)
            top_locations.append(top.sensor_location)
        if top_locations:
            from collections import Counter
            cnt = Counter(top_locations)
            loc, count = cnt.most_common(1)[0]
            current_top = max(rows, key=lambda p: p.pressure_value)
            if count >= 2 and current_top.pressure_value > 80:
                import re
                coord_re = re.compile(r'^r(\d+)_c(\d+)$')
                numeric_cells = [p for p in rows if coord_re.match(p.sensor_location)]
                if numeric_cells:
                    maxC = max([int(coord_re.match(p.sensor_location).group(2)) for p in numeric_cells])
                    mm = coord_re.match(loc)
                    if mm:
                        col = int(mm.group(2))
                        if col < (maxC / 2.0):
                            action = 'roll_right'
                            message = f"Suggest roll to the right — persistent high pressure at {loc}"
                        elif col > (maxC / 2.0):
                            action = 'roll_left'
                            message = f"Suggest roll to the left — persistent high pressure at {loc}"
                        else:
                            action = 'adjust_position'
                            message = f"Suggest adjust position — persistent high pressure at {loc}"
                    else:
                        action = 'adjust_position'
                        message = f"Suggest adjust position — persistent high pressure at {loc}"
                else:
                    action = 'adjust_position'
                    message = f"Suggest adjust position — persistent high pressure at {loc}"
                reposition = {'action': action, 'reason': message, 'location': loc, 'confidence': round(min(0.95, 0.5 + (count-1)*0.2), 2)}
    except Exception:
        reposition = None

    return JsonResponse({'cells': cells, 'timestamp': latest.isoformat(), 'reposition': reposition})
