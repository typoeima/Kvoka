from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
import json
from .models import FocusSession, WorkspaceConfig

def home(request):
    return render(request, 'core/home.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            WorkspaceConfig.objects.create(user=user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
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
    """Сохраняет завершённую сессию"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        minutes = int(data.get('minutes', 0))
        plan_text = data.get('plan_text', '')
        plan_done = data.get('plan_done', False)
        
        print(f"Получен запрос на сохранение: {minutes} минут для {request.user.username}")
        
        if minutes > 0:
            session = FocusSession.objects.create(
                user=request.user,
                minutes=minutes,
                completed=True,
                plan_text=plan_text,
                plan_done=plan_done,
                end_time=timezone.now()
            )
            
            # Обновляем данные пользователя из базы
            request.user.refresh_from_db()
            
            print(f"Сессия сохранена! Новый стрик: {request.user.current_days}")
            
            return JsonResponse({
                'status': 'ok',
                'session_id': session.id,
                'streak_updated': True,
                'new_streak': request.user.current_days
            })
    
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
        'rank': request.user.rank,
    })