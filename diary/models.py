from django.db import models
from django.utils import (
    timezone,
)  # djangoでは、datetime.now のかわりに、timezone.now で現在日付・時刻を取得する
from django.contrib.auth.models import User


class Day(models.Model):
    title = models.CharField("タイトル", max_length=200)
    text = models.TextField("本文")
    date = models.DateTimeField("日付", default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to="diary_images/", null=True, blank=True, verbose_name="画像"
    )

    @property
    def has_reviewer_comments(self):
        """レビュアーからのコメントがあるかどうかをチェック"""
        return self.comments.filter(author__in=self.get_reviewers()).exists()

    @property
    def reviewers(self):
        """この日記のレビュアーを取得"""
        return User.objects.filter(review_permissions__diary_owner=self.author)

    @property
    def is_reviewed(self):
        """レビュー済みかどうか（レビュアーからのコメントがある場合）"""
        return self.has_reviewer_comments

    # オブジェクトの文字列表現を定義するために使用
    # day = Day.objects.first()が"タイトル" のように表示される
    def __str__(self):
        return self.title


class Reviewer(models.Model):
    diary_owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="granted_reviewers"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="review_permissions"
    )
    granted_at = models.DateTimeField("許可日時", auto_now_add=True)

    class Meta:
        unique_together = ("diary_owner", "reviewer")  # 同じレビュアーを重複登録しない
        verbose_name = "レビュアー権限"
        verbose_name_plural = "レビュアー権限"

    def __str__(self):
        return f"{self.reviewer.username} → {self.diary_owner.username}の全日記"


class Comment(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField("コメント内容", max_length=1000)
    created_at = models.DateTimeField("投稿日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "コメント"
        verbose_name_plural = "コメント"

    def __str__(self):
        return f"{self.author.username}: {self.text[:50]}"

    @property
    def is_reply(self):
        return self.reply_to_id is not None
