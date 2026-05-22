from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Friend
from core.models import FocusSession

User = get_user_model()

@login_required
def friends_list(request):
    """Страница со списком друзей и заявками"""
    # Получаем друзей
    friends = Friend.get_friends(request.user)
    
    # Входящие заявки
    incoming_requests = Friend.get_pending_requests(request.user)
    
    # Исходящие заявки
    outgoing_requests = Friend.get_sent_requests(request.user)
    
    # Поиск пользователей для добавления
    search_query = request.GET.get('search', '')
    search_results = []
    if search_query:
        # Получаем ID друзей
        friend_ids = [f.id for f in friends]
        # Получаем ID пользователей с активными заявками
        pending_from_ids = [req.from_user.id for req in incoming_requests]
        pending_to_ids = [req.to_user.id for req in outgoing_requests]
        
        search_results = User.objects.filter(
            Q(username__icontains=search_query)
        ).exclude(id=request.user.id).exclude(
            id__in=friend_ids
        ).exclude(
            id__in=pending_from_ids
        ).exclude(
            id__in=pending_to_ids
        )[:10]
    
    # Статистика друзей для лидерборда
    friends_with_stats = []
    for friend in friends:
        # Общее количество минут за всё время
        total_minutes = FocusSession.objects.filter(
            user=friend, completed=True
        ).aggregate(total=Sum('minutes'))['total'] or 0
        total_hours = round(total_minutes / 60, 1)
        
        # Сегодняшние минуты
        today = timezone.now().date()
        today_minutes = FocusSession.objects.filter(
            user=friend, completed=True, start_time__date=today
        ).aggregate(total=Sum('minutes'))['total'] or 0
        
        # Получаем стрик из модели User
        streak = friend.current_days if hasattr(friend, 'current_days') else 0
        
        friends_with_stats.append({
            'user': friend,
            'streak': streak,
            'total_hours': total_hours,
            'today_minutes': today_minutes,
        })
    
    # Сортируем по стрику (по убыванию)
    friends_with_stats.sort(key=lambda x: x['streak'], reverse=True)
    
    context = {
        'friends': friends_with_stats,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'friends/friends.html', context)


@login_required
def send_friend_request(request, user_id):
    """Отправить заявку в друзья"""
    if request.method == 'POST':
        to_user = get_object_or_404(User, id=user_id)
        
        # Проверяем, не отправлена ли уже заявка
        if Friend.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user)
        ).exists():
            return JsonResponse({'status': 'error', 'message': 'Заявка уже существует'}, status=400)
        
        Friend.objects.create(from_user=request.user, to_user=to_user)
        return JsonResponse({'status': 'ok', 'message': 'Заявка отправлена'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def accept_friend_request(request, request_id):
    """Принять заявку в друзья"""
    if request.method == 'POST':
        friend_request = get_object_or_404(Friend, id=request_id, to_user=request.user, status='pending')
        friend_request.accept()
        return JsonResponse({'status': 'ok', 'message': 'Заявка принята'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def reject_friend_request(request, request_id):
    """Отклонить заявку в друзья"""
    if request.method == 'POST':
        friend_request = get_object_or_404(Friend, id=request_id, to_user=request.user, status='pending')
        friend_request.reject()
        return JsonResponse({'status': 'ok', 'message': 'Заявка отклонена'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def remove_friend(request, user_id):
    """Удалить друга"""
    if request.method == 'POST':
        friend = get_object_or_404(User, id=user_id)
        Friend.objects.filter(
            Q(from_user=request.user, to_user=friend, status='accepted') |
            Q(from_user=friend, to_user=request.user, status='accepted')
        ).delete()
        return JsonResponse({'status': 'ok', 'message': 'Друг удалён'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def cancel_friend_request(request, request_id):
    """Отменить отправленную заявку"""
    if request.method == 'POST':
        friend_request = get_object_or_404(Friend, id=request_id, from_user=request.user, status='pending')
        friend_request.delete()
        return JsonResponse({'status': 'ok', 'message': 'Заявка отменена'})
    
    return JsonResponse({'status': 'error'}, status=400)