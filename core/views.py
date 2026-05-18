from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
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
def profile(request):
    return render(request, 'core/profile.html', {'user': request.user})