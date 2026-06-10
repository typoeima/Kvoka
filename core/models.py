from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    total_hours = models.FloatField(default=0.0)
    current_days = models.IntegerField(default=0)
    max_days = models.IntegerField(default=0)
    last_focus_date = models.DateField(null=True, blank=True)
    
    # Новые поля для достижений
    total_sessions = models.IntegerField(default=0)  # всего сессий
    total_videos_watched = models.IntegerField(default=0)  # просмотрено видео
    total_pdfs_read = models.IntegerField(default=0)  # прочитано PDF
    
    def __str__(self):
        return self.username

    def update_streak(self):
        today = timezone.now().date()
    
        if self.last_focus_date == today:
            return
    
        if self.last_focus_date == today - timedelta(days=1):
            self.current_days += 1
        else:
            self.current_days = 1
    
        if self.current_days > self.max_days:
            self.max_days = self.current_days
    
        self.last_focus_date = today
        self.save()
    
        self.check_and_grant_achievements()
    
    def increment_sessions(self):
        self.total_sessions += 1
        self.save()
        self.check_and_grant_achievements()
    
    def increment_videos_watched(self):
        self.total_videos_watched += 1
        self.save()
        self.check_and_grant_achievements()
    
    def increment_pdfs_read(self):
        self.total_pdfs_read += 1
        self.save()
        self.check_and_grant_achievements()
    
    def add_friend(self):
        """Вызывается когда у пользователя появляется новый друг"""
        self.check_and_grant_achievements()
    
    def check_and_grant_achievements(self):
        from .models import Achievement, EarnedAchievement
        
        earned_ids = EarnedAchievement.objects.filter(user=self).values_list('achievement_id', flat=True)
        available_achievements = Achievement.objects.filter(is_active=True).exclude(id__in=earned_ids)
        
        new_achievements = []
        for ach in available_achievements:
            earned = False
            
            if ach.type == 'streak' and ach.required_streak:
                if self.current_days >= ach.required_streak:
                    earned = True
            
            elif ach.type == 'friends' and ach.required_friends:
                friends_count = self.friend_requests_sent.filter(status='accepted').count() + \
                               self.friend_requests_received.filter(status='accepted').count()
                if friends_count >= ach.required_friends:
                    earned = True
            
            elif ach.type == 'sessions' and ach.required_sessions:
                if self.total_sessions >= ach.required_sessions:
                    earned = True
            
            elif ach.type == 'hours' and ach.required_hours:
                if self.total_hours >= ach.required_hours:
                    earned = True
            
            elif ach.type == 'media' and ach.required_videos_watched:
                if self.total_videos_watched >= ach.required_videos_watched:
                    earned = True
            
            elif ach.type == 'special':
                # Для особых достижений — отдельная логика
                pass
            
            if earned:
                new_achievements.append(EarnedAchievement(user=self, achievement=ach))
        
        if new_achievements:
            EarnedAchievement.objects.bulk_create(new_achievements)
    
    def get_achievements_list(self):
        return self.earned_achievements.select_related('achievement').all()
    
    def get_friends_count(self):
        from friends.models import Friend
        return Friend.objects.filter(
            models.Q(from_user=self, status='accepted') |
            models.Q(to_user=self, status='accepted')
        ).count()
    def add_friend(self):
        """Вызывается когда у пользователя появляется новый друг"""
        # Проверяем достижения за друзей
        self.check_and_grant_achievements()

class FocusSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    minutes = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    plan_text = models.TextField(blank=True, verbose_name='План на сессию')
    plan_done = models.BooleanField(default=False, verbose_name='План выполнен')
    
    def __str__(self):
        return f"{self.user.username} - {self.minutes}мин"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if self.completed and self.minutes > 0 and is_new:
            print(f"Сохраняем сессию: {self.minutes} минут для {self.user.username}")  # Отладка
            
            hours = self.minutes / 60
            self.user.total_hours += hours
            
            # Увеличиваем счётчик сессий
            self.user.total_sessions += 1  # Напрямую, без метода increment_sessions
            
            # Обновляем стрик
            self.user.update_streak()
            
            self.user.save()
        
        super().save(*args, **kwargs)

class WorkspaceConfig(models.Model):
    THEME_CHOICES = [
        ('dark', 'Тёмная'),
        ('light', 'Светлая'),
        ('forest', 'Лесная'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workspace_config')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    background = models.CharField(max_length=255, blank=True)
    focus_minutes = models.IntegerField(default=25, validators=[MinValueValidator(1), MaxValueValidator(180)])
    break_minutes = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(60)])
    widgets = models.JSONField(default=dict)
    video_url = models.URLField(blank=True)
    
    def __str__(self):
        return f"Настройки {self.user.username}"
    FOCUS_MODE_CHOICES = [
        ('timer_only', 'Только таймер'),
        ('timer_pdf', 'Таймер + PDF'),
        ('timer_youtube', 'Таймер + YouTube'),
    ]

    focus_mode = models.CharField(max_length=20, choices=FOCUS_MODE_CHOICES, default='timer_only')
    video_url = models.URLField(blank=True, help_text='YouTube ссылка')
    video_enabled = models.BooleanField(default=False)
    
    pdf_enabled = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)
    
    def get_video_id(self):
        """Извлекает ID видео из YouTube URL"""
        import re
        if not self.video_url:
            return None
        patterns = [
            r'youtu\.be/([^?&]+)',
            r'youtube\.com/watch\?v=([^&]+)',
            r'youtube\.com/embed/([^?&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, self.video_url)
            if match:
                return match.group(1)
        return None

class Achievement(models.Model):
    TYPE_CHOICES = [
        ('streak', 'Стрик'),
        ('friends', 'Друзья'),
        ('sessions', 'Сессии'),
        ('hours', 'Часы фокуса'),
        ('media', 'Медиа'),
        ('special', 'Особые'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text='Описание достижения')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='streak')
    
    # Условия для получения
    required_streak = models.IntegerField(null=True, blank=True, help_text='Требуемая серия дней')
    required_friends = models.IntegerField(null=True, blank=True, help_text='Требуемое количество друзей')
    required_sessions = models.IntegerField(null=True, blank=True, help_text='Требуемое количество сессий')
    required_hours = models.FloatField(null=True, blank=True, help_text='Требуемое количество часов')
    required_videos_watched = models.IntegerField(null=True, blank=True, help_text='Просмотренных видео')
    required_pdfs_read = models.IntegerField(null=True, blank=True, help_text='Прочитанных PDF')
    
    icon = models.ImageField(upload_to='achievements/', blank=True, null=True)
    order = models.IntegerField(default=0, help_text='Порядок отображения')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        ordering = ['order', 'required_streak']

class EarnedAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'achievement')
    
    def __str__(self):
        return f"{self.user} - {self.achievement.name}"

class EarnedAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'achievement')
    
    def __str__(self):
        return f"{self.user} - {self.achievement.name}"
