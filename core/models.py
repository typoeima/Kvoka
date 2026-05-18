from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    rank = models.CharField(max_length=30, default='Новичок')
    total_hours = models.FloatField(default=0.0)
    current_days = models.IntegerField(default=0)
    max_days = models.IntegerField(default=0)
    
    def __str__(self):
        return self.username
    
    def update_rank(self):
        if self.total_hours >= 30:
            self.rank = 'Дзен-мастер'
        elif self.total_hours >= 10:
            self.rank = 'Монах'
        else:
            self.rank = 'Новичок'
        self.save()

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

class Achievement(models.Model):
    name = models.CharField(max_length=50)
    required_streak = models.IntegerField(help_text='Требуемая серия дней (7, 30, 100)')
    icon = models.ImageField(upload_to='achievements/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.required_streak} дней)"

class EarnedAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'achievement')
    
    def __str__(self):
        return f"{self.user} - {self.achievement.name}"