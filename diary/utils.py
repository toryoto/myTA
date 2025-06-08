from django.contrib.auth.models import User
from .models import Day, Reviewer


def can_comment_on_day(user, day):
    """ユーザーが特定の日記にコメントできるかチェック"""
    return Reviewer.objects.filter(
        diary_owner=day.author,
        reviewer=user
    ).exists()


def get_reviewable_days(user):
    """ユーザーがコメントできる全ての日記一覧"""
    return Day.objects.filter(
        author__granted_reviewers__reviewer=user
    ).order_by('-date')


def get_my_reviewers(user):
    """自分の日記にコメントできるレビュアー一覧"""
    return Reviewer.objects.filter(diary_owner=user)


def get_reviewable_diary_owners(user):
    """ユーザーがレビューできる日記作成者一覧"""
    return User.objects.filter(
        granted_reviewers__reviewer=user
    ).distinct()