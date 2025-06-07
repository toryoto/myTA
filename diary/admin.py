from django.contrib import admin
from .models import Day

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'author')  # 一覧表示するフィールド
    list_filter = ('date', 'author')  # フィルターを設定するフィールド
    search_fields = ('title', 'text')  # 検索対象のフィールド
    ordering = ('-date',)  # 日付の降順で表示