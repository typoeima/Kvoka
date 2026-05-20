from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FocusSession, WorkspaceConfig, Achievement, EarnedAchievement

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Квока профиль', {'fields': ('avatar', 'total_hours', 'current_days', 'max_days', 'last_focus_date', 'total_sessions', 'total_videos_watched', 'total_pdfs_read')}),
    )
    list_display = ('username', 'email', 'total_hours', 'current_days', 'max_days')

admin.site.register(User, CustomUserAdmin)
admin.site.register(FocusSession)
admin.site.register(WorkspaceConfig)

class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'required_streak', 'required_friends', 'required_sessions', 'required_hours', 'order', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'description', 'type', 'icon', 'order', 'is_active')
        }),
        ('Условия для стрика', {
            'fields': ('required_streak',),
            'classes': ('collapse',)
        }),
        ('Условия для друзей', {
            'fields': ('required_friends',),
            'classes': ('collapse',)
        }),
        ('Условия для сессий', {
            'fields': ('required_sessions',),
            'classes': ('collapse',)
        }),
        ('Условия для часов', {
            'fields': ('required_hours',),
            'classes': ('collapse',)
        }),
        ('Условия для медиа', {
            'fields': ('required_videos_watched', 'required_pdfs_read'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(Achievement, AchievementAdmin)
admin.site.register(EarnedAchievement)