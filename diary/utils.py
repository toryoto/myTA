from django.contrib.auth.models import User
from django.db.models import Q, Exists, OuterRef
from .models import Day, Reviewer, Comment


def can_comment_on_day(user, day):
    """ユーザーが特定の日記にコメントできるかチェック"""
    return Reviewer.objects.filter(diary_owner=day.author, reviewer=user).exists()


def get_reviewable_days(user):
    """ユーザーがコメントできる全ての日記一覧（レビュー済みでないもののみ）"""
    # レビュアーからのコメントがある日記を除外する
    reviewer_commented_days = Comment.objects.filter(
        day=OuterRef("pk"), author=user  # 自分がコメントした日記を除外
    )

    return (
        Day.objects.filter(author__granted_reviewers__reviewer=user)
        .exclude(Exists(reviewer_commented_days))
        .order_by("-date")
    )


def get_reviewed_days(user):
    """ユーザーがレビュー済みの日記一覧（自分がコメントした日記）"""
    return (
        Day.objects.filter(
            author__granted_reviewers__reviewer=user, comments__author=user
        )
        .distinct()
        .order_by("-date")
    )


def get_my_reviewers(user):
    """自分の日記にコメントできるレビュアー一覧"""
    return Reviewer.objects.filter(diary_owner=user)


def get_reviewable_diary_owners(user):
    """ユーザーがレビューできる日記作成者一覧"""
    return User.objects.filter(granted_reviewers__reviewer=user).distinct()
