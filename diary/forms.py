from django import forms
from django.contrib.auth.models import User
from .models import Day, Reviewer


class DayCreateForm(forms.ModelForm):

    class Meta:
        model = Day
        fields = ('title', 'text', 'date')


class ReviewerAddForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='ユーザー名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'レビュアーのユーザー名を入力'
        })
    )

    def __init__(self, *args, **kwargs):
        self.diary_owner = kwargs.pop('diary_owner', None)
        super().__init__(*args, **kwargs)

    # clean_<フィールド名>で事前定義された、特定のフィールドのバリデーションを実行するメソッド
    def clean_username(self):
        username = self.cleaned_data['username']
        
        # ユーザーが存在するかチェック
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError('指定されたユーザーは存在しません。')
        
        # 自分自身を指定していないかチェック
        if user == self.diary_owner:
            raise forms.ValidationError('自分自身をレビュアーに指定することはできません。')
        
        # 既にレビュアーに登録されていないかチェック
        if Reviewer.objects.filter(diary_owner=self.diary_owner, reviewer=user).exists():
            raise forms.ValidationError('このユーザーは既にレビュアーに登録されています。')
        
        return username

    def save(self):
        username = self.cleaned_data['username']
        user = User.objects.get(username=username)
        return Reviewer.objects.create(diary_owner=self.diary_owner, reviewer=user)