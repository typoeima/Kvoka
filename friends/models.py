from django.db import models
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()  # Это правильный способ получить модель пользователя

class Friend(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Друзья'),
        ('rejected', 'Отклонена'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"
    
    def accept(self):
        self.status = 'accepted'
        self.save()
        # Проверяем достижения у обоих пользователей
        if hasattr(self.from_user, 'add_friend'):
            self.from_user.add_friend()
        if hasattr(self.to_user, 'add_friend'):
            self.to_user.add_friend()
    
    def reject(self):
        self.status = 'rejected'
        self.save()
    
    @classmethod
    def are_friends(cls, user1, user2):
        return cls.objects.filter(
            Q(from_user=user1, to_user=user2, status='accepted') |
            Q(from_user=user2, to_user=user1, status='accepted')
        ).exists()
    
    @classmethod
    def get_friends(cls, user):
        """Возвращает список друзей пользователя"""
        sent = cls.objects.filter(from_user=user, status='accepted').values_list('to_user', flat=True)
        received = cls.objects.filter(to_user=user, status='accepted').values_list('from_user', flat=True)
        friend_ids = list(sent) + list(received)
        return User.objects.filter(id__in=friend_ids)
    
    @classmethod
    def get_pending_requests(cls, user):
        """Возвращает входящие заявки в друзья"""
        return cls.objects.filter(to_user=user, status='pending')
    
    @classmethod
    def get_sent_requests(cls, user):
        """Возвращает исходящие заявки"""
        return cls.objects.filter(from_user=user, status='pending')