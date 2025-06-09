from django.contrib import admin
from .models import Day, Reviewer, Comment

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'author', 'image')  # 一覧表示するフィールド
    list_filter = ('date', 'author')  # フィルターを設定するフィールド
    search_fields = ('title', 'text')  # 検索対象のフィールド
    ordering = ('-date',)  # 日付の降順で表示

@admin.register(Reviewer)
class ReviewerAdmin(admin.ModelAdmin):
    list_display = ('diary_owner', 'reviewer', 'granted_at')
    list_filter = ('diary_owner', 'reviewer')
    search_fields = ('diary_owner', 'reviewer')
    ordering = ('-granted_at',)
    
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('day', 'author', 'text', 'created_at', 'is_reply')
    list_filter = ('created_at', 'author')
    search_fields = ('text', 'author__username', 'day__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')