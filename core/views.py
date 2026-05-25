from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
from .models import FocusSession, WorkspaceConfig
from .forms import CustomUserCreationForm  # Добавьте эту строку

def home(request):
    return render(request, 'core/home.html')

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            WorkspaceConfig.objects.create(user=user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/signup.html', {'form': form})

@login_required
def dashboard(request):
    config, created = WorkspaceConfig.objects.get_or_create(user=request.user)
    today = timezone.now().date()
    today_sessions = FocusSession.objects.filter(
        user=request.user,
        start_time__date=today,
        completed=True
    )
    today_total = sum(s.minutes for s in today_sessions)
    
    context = {
        'config': config,
        'today_total': today_total,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def save_timer_settings(request):
    if request.method == 'POST':
        config = WorkspaceConfig.objects.get(user=request.user)
        focus_minutes = int(request.POST.get('focus_minutes', 25))
        break_minutes = int(request.POST.get('break_minutes', 5))
        
        if focus_minutes < 1:
            focus_minutes = 1
        if focus_minutes > 180:
            focus_minutes = 180
        if break_minutes < 1:
            break_minutes = 1
        if break_minutes > 60:
            break_minutes = 60
            
        config.focus_minutes = focus_minutes
        config.break_minutes = break_minutes
        config.save()
        
        return JsonResponse({'status': 'ok', 'focus_minutes': focus_minutes, 'break_minutes': break_minutes})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def save_session(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        minutes = int(data.get('minutes', 0))
        plan_text = data.get('plan_text', '')
        plan_done = data.get('plan_done', False)
        
        if minutes > 0:
            session = FocusSession.objects.create(
                user=request.user,
                minutes=minutes,
                completed=True,
                plan_text=plan_text,
                plan_done=plan_done,
                end_time=timezone.now()
            )
            return JsonResponse({'status': 'ok', 'session_id': session.id, 'streak_updated': True})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def profile(request):
    achievements = request.user.get_achievements_list()
    context = {
        'user': request.user,
        'achievements': achievements,
    }
    return render(request, 'core/profile.html', context)

@login_required
def get_user_stats(request):
    """Возвращает актуальную статистику пользователя (для AJAX)"""
    return JsonResponse({
        'current_days': request.user.current_days,
        'max_days': request.user.max_days,
        'total_hours': request.user.total_hours,
        'total_sessions': request.user.total_sessions,
    })

@login_required
def session_history(request):
    """История сессий с фильтрацией"""
    
    # Получаем параметры фильтрации
    period = request.GET.get('period', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Базовая выборка
    sessions = FocusSession.objects.filter(
        user=request.user,
        completed=True
    ).order_by('-start_time')
    
    # Фильтрация по периоду
    today = timezone.now().date()
    
    if period == 'day':
        sessions = sessions.filter(start_time__date=today)
    elif period == 'week':
        week_ago = today - timedelta(days=7)
        sessions = sessions.filter(start_time__date__gte=week_ago)
    elif period == 'month':
        month_ago = today - timedelta(days=30)
        sessions = sessions.filter(start_time__date__gte=month_ago)
    elif period == 'custom' and date_from and date_to:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            sessions = sessions.filter(start_time__date__gte=from_date, start_time__date__lte=to_date)
        except ValueError:
            pass
    
    # Статистика за период
    total_minutes = sessions.aggregate(total=Sum('minutes'))['total'] or 0
    total_hours = round(total_minutes / 60, 1)
    total_sessions = sessions.count()
    
    # Сессии с планом
    sessions_with_plan = sessions.filter(plan_text__isnull=False).exclude(plan_text='').count()
    
    # Дней со стриком в выбранный период
    streak_days_in_period = sessions.dates('start_time', 'day').count()
    
    # Успешность выполнения планов
    plan_completion_rate = 0
    if sessions_with_plan > 0:
        plan_done_count = sessions.filter(plan_done=True).count()
        plan_completion_rate = round(plan_done_count / sessions_with_plan * 100)
    
    # Пагинация (по 20 сессий на страницу)
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_minutes': total_minutes,
        'total_hours': total_hours,
        'total_sessions': total_sessions,
        'sessions_with_plan': sessions_with_plan,
        'streak_days_in_period': streak_days_in_period,
        'plan_completion_rate': plan_completion_rate,
        'period': period,
        'date_from': date_from,
        'date_to': date_to,
        'today': today,
    }
    
    return render(request, 'core/session_history.html', context)

@login_required
def session_detail(request, session_id):
    """Детальная страница сессии"""
    session = get_object_or_404(FocusSession, id=session_id, user=request.user)
    return render(request, 'core/session_detail.html', {'session': session})
@login_required
def session_history(request):
    """История сессий с фильтрацией и графиком"""
    
    # Получаем параметры фильтрации
    period = request.GET.get('period', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Базовая выборка
    sessions = FocusSession.objects.filter(
        user=request.user,
        completed=True
    ).order_by('-start_time')
    
    # Фильтрация по периоду
    today = timezone.now().date()
    
    if period == 'day':
        sessions = sessions.filter(start_time__date=today)
    elif period == 'week':
        week_ago = today - timedelta(days=7)
        sessions = sessions.filter(start_time__date__gte=week_ago)
    elif period == 'month':
        month_ago = today - timedelta(days=30)
        sessions = sessions.filter(start_time__date__gte=month_ago)
    elif period == 'custom' and date_from and date_to:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            sessions = sessions.filter(start_time__date__gte=from_date, start_time__date__lte=to_date)
        except ValueError:
            pass
    
    # Данные для графика (группировка по дням)
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate
    
    chart_data = sessions.annotate(date=TruncDate('start_time')).values('date').annotate(
        total_minutes=Sum('minutes'),
        sessions_count=Count('id')
    ).order_by('date')
    
    chart_labels = [item['date'].strftime('%d.%m') for item in chart_data]
    chart_minutes = [item['total_minutes'] for item in chart_data]
    chart_sessions = [item['sessions_count'] for item in chart_data]
    
    # Статистика за период
    total_minutes = sessions.aggregate(total=Sum('minutes'))['total'] or 0
    total_hours = round(total_minutes / 60, 1)
    total_sessions = sessions.count()
    
    # Сессии с планом
    sessions_with_plan = sessions.filter(plan_text__isnull=False).exclude(plan_text='').count()
    
    # Дней со стриком в выбранный период
    streak_days_in_period = sessions.dates('start_time', 'day').count()
    
    # Успешность выполнения планов
    plan_completion_rate = 0
    if sessions_with_plan > 0:
        plan_done_count = sessions.filter(plan_done=True).count()
        plan_completion_rate = round(plan_done_count / sessions_with_plan * 100)
    
    # Средняя длительность сессии
    avg_duration = round(total_minutes / total_sessions, 1) if total_sessions > 0 else 0
    
    # Пагинация
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_minutes': total_minutes,
        'total_hours': total_hours,
        'total_sessions': total_sessions,
        'sessions_with_plan': sessions_with_plan,
        'streak_days_in_period': streak_days_in_period,
        'plan_completion_rate': plan_completion_rate,
        'avg_duration': avg_duration,
        'period': period,
        'date_from': date_from,
        'date_to': date_to,
        'today': today,
        'chart_labels': chart_labels,
        'chart_minutes': chart_minutes,
        'chart_sessions': chart_sessions,
    }
    
    return render(request, 'core/session_history.html', context)

@login_required
def save_workspace_settings(request):
    """Сохраняет все настройки рабочего пространства"""
    if request.method == 'POST':
        config, created = WorkspaceConfig.objects.get_or_create(user=request.user)
        
        config.focus_minutes = int(request.POST.get('focus_minutes', 25))
        config.break_minutes = int(request.POST.get('break_minutes', 5))
        config.theme = request.POST.get('theme', 'light')
        config.video_enabled = request.POST.get('video_enabled') == 'true'
        config.video_url = request.POST.get('video_url', '')
        config.pdf_enabled = request.POST.get('pdf_enabled') == 'true'
        
        if request.FILES.get('pdf_file'):
            config.pdf_file = request.FILES['pdf_file']
        
        config.save()
        
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def remove_pdf(request):
    """Удаляет PDF файл"""
    if request.method == 'POST':
        config = WorkspaceConfig.objects.get(user=request.user)
        if config.pdf_file:
            config.pdf_file.delete()
            config.pdf_file = None
            config.save()
        return JsonResponse({'status': 'ok'})
    
    return JsonResponse({'status': 'error'}, status=400)