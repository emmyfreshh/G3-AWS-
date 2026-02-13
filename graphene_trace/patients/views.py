from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PressureData, Comment, Notification
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import redirect
from .forms import CommentForm, PressureDataForm
from django.http import JsonResponse
import re

@login_required
def add_pressure_data(request):
    if request.user.role != 'patient':
        return render(request, '403.html')
    if request.method == 'POST':
        form = PressureDataForm(request.POST)
        if form.is_valid():
            data = form.save(commit=False)
            data.patient = request.user
            data.save()
            return redirect('dashboard')
    else:
        form = PressureDataForm()
    return render(request, 'patients/add_pressure_data.html', {'form': form})

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')
    if request.user.role == 'patient':
        # Real-time pressure heat map - get latest data
        recent_data = PressureData.objects.filter(patient=request.user).order_by('-timestamp')[:100]
        # Notifications
        notifications = Notification.objects.filter(patient=request.user, is_read=False)
        return render(request, 'patients/dashboard.html', {
            'recent_data': recent_data,
            'notifications': notifications,
        })
    elif request.user.role == 'clinician':
        # Redirect to clinician dashboard or show patient list
        return render(request, 'clinicians/dashboard.html')
    elif request.user.is_superuser or request.user.role == 'admin':
        return render(request, 'admin/dashboard.html')
    else:
        return render(request, '403.html')  # Forbidden for unknown roles

@login_required
def pressure_data(request):
    if request.user.role != 'patient':
        return render(request, '403.html')  # Forbidden
    data = PressureData.objects.filter(patient=request.user).order_by('-timestamp')[:100]  # Limit for graph
    labels = [d.timestamp.strftime('%Y-%m-%d %H:%M') for d in reversed(data)]
    values = [d.pressure_value for d in reversed(data)]
    return render(request, 'patients/pressure_data.html', {
        'data': data,
        'labels': labels,
        'values': values,
    })

@login_required
def comments(request):
    if request.user.role != 'patient':
        return render(request, '403.html')
    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.patient = request.user
            comment.save()
            return redirect('comments')
    else:
        form = CommentForm(user=request.user)
    comments = Comment.objects.filter(patient=request.user).order_by('-timestamp')
    return render(request, 'patients/comments.html', {'comments': comments, 'form': form})

@login_required
def notifications(request):
    if request.user.role != 'patient':
        return render(request, '403.html')
    notifications = Notification.objects.filter(patient=request.user).order_by('-timestamp')
    return render(request, 'patients/notifications.html', {'notifications': notifications})


@login_required
def live_map(request):
    if request.user.role != 'patient':
        return render(request, '403.html')
    return render(request, 'patients/live_map.html')


@login_required
def live_grid_json(request):
    # Return latest grid for the current patient as JSON
    if request.user.role != 'patient':
        return JsonResponse({'error': 'forbidden'}, status=403)
    # find latest timestamp for this patient
    latest = PressureData.objects.filter(patient=request.user).order_by('-timestamp').values_list('timestamp', flat=True).first()
    if not latest:
        return JsonResponse({'cells': []})
    rows = PressureData.objects.filter(patient=request.user, timestamp=latest)
    cells = []
    coord_re = re.compile(r'^r(\d+)_c(\d+)$')
    for p in rows:
        m = coord_re.match(p.sensor_location)
        if m:
            r = int(m.group(1))
            c = int(m.group(2))
            cells.append({'r': r, 'c': c, 'value': p.pressure_value})
        else:
            cells.append({'label': p.sensor_location, 'value': p.pressure_value})
    # Simple repositioning heuristic: check persistence across recent timestamps
    reposition = None
    try:
        recent_timestamps = PressureData.objects.filter(patient=request.user).order_by('-timestamp').values_list('timestamp', flat=True).distinct()[:3]
        top_locations = []
        for ts in recent_timestamps:
            rows_ts = PressureData.objects.filter(patient=request.user, timestamp=ts)
            if not rows_ts:
                continue
            # find location with max pressure
            top = max(rows_ts, key=lambda p: p.pressure_value)
            top_locations.append(top.sensor_location)
        if top_locations:
            # if most common top location repeats, consider it persistent
            from collections import Counter
            cnt = Counter(top_locations)
            loc, count = cnt.most_common(1)[0]
            # get current top value
            current_top = max(rows, key=lambda p: p.pressure_value)
            if count >= 2 and current_top.pressure_value > 80:
                # derive simple direction from coordinate if possible
                import re
                m = re.match(r'^r(\d+)_c(\d+)$', loc)
                if m:
                    c = int(m.group(2))
                    max_c = max([p.sensor_location for p in rows if re.match(r'^r(\d+)_c(\d+)$', p.sensor_location)] or [loc])
                # compute cols by inspecting numeric cells
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


@login_required
def live_graph_json(request):
    # Return recent time-series pressure values for charting (JSON)
    if request.user.role != 'patient':
        return JsonResponse({'error': 'forbidden'}, status=403)
    # get last 100 entries ordered oldest->newest
    qs = PressureData.objects.filter(patient=request.user).order_by('-timestamp')[:100]
    data = list(reversed([{'timestamp': p.timestamp.isoformat(), 'value': p.pressure_value} for p in qs]))
    return JsonResponse({'data': data})
