
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import DayCreateForm, ReviewerAddForm, CommentForm
from .models import Day, Reviewer, Comment
from .utils import get_my_reviewers, get_reviewable_days, can_comment_on_day
from django.views import generic
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse


class IndexView(LoginRequiredMixin, generic.ListView):
    model = Day
    template_name = 'diary/day_list.html'
    context_object_name = 'day_list'

    def get_queryset(self):
        return Day.objects.filter(author=self.request.user)

    
class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Day
    template_name = 'diary/day_detail.html'
    context_object_name = 'day'
    
    def get_queryset(self):
        user = self.request.user
        # Qオブジェクトを使用することで、OR条件を一つのクエリで表現することができるようになる
        # distinct()がないと、レビュアーと投稿者の条件により同じデータを複数取得してしまう
        return Day.objects.filter(
            Q(author=user) | Q(author__granted_reviewers__reviewer=user)
        ).distinct()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        day = self.get_object()
        user = self.request.user
        
        # ユーザーの権限を判定
        is_owner = day.author == user
        is_reviewer = can_comment_on_day(user, day)
        
        # アクセス権限チェック
        if not (is_owner or is_reviewer):
            return context  # エラーは後でハンドリング
        
        # コメント一覧（返信でないもの）
        comments = Comment.objects.filter(day=day, reply_to__isnull=True)
        
        # コメントフォーム（レビュアーのみ）
        comment_form = CommentForm() if is_reviewer else None
        
        context.update({
            'comments': comments,
            'comment_form': comment_form,
            'is_owner': is_owner,
            'is_reviewer': is_reviewer,
        })
        return context

class CreateView(LoginRequiredMixin, generic.CreateView):
    model = Day
    form_class = DayCreateForm
    template_name = 'diary/day_form.html'
    success_url = reverse_lazy('diary:index')

    def form_valid(self, form):
        # 作成時に自動的にログインユーザーをauthorに設定
        form.instance.author = self.request.user
        return super().form_valid(form)


class UpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Day
    form_class = DayCreateForm
    template_name = 'diary/day_form.html'
    success_url = reverse_lazy('diary:index')

    def get_queryset(self):
        return Day.objects.filter(author=self.request.user)


class DeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Day
    template_name = 'diary/day_confirm_delete.html'
    success_url = reverse_lazy('diary:index')
    context_object_name = 'day'

    def get_queryset(self):
        return Day.objects.filter(author=self.request.user)

def add_comment_htmx(request, day_id):
    """HTMXを使用したコメント投稿機能"""
    day = get_object_or_404(Day, id=day_id)
    
    # レビュー権限チェック
    if not can_comment_on_day(request.user, day):
        return HttpResponse("<div class='text-red-500'>コメントする権限がありません</div>", status=403)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.day = day
            comment.author = request.user
            comment.save()
            
            # 新しいコメント一覧を返す（返信でないもののみ）
            comments = Comment.objects.filter(day=day, reply_to__isnull=True)
            comment_form = CommentForm()
            
            return render(request, 'diary/partials/comment_section.html', {
                'comments': comments,
                'comment_form': comment_form,
                'day': day,
                'is_reviewer': True
            })
        else:
            # エラーがある場合、フォームとエラーを含むセクションを返す
            comments = Comment.objects.filter(day=day, reply_to__isnull=True)
            return render(request, 'diary/partials/comment_section.html', {
                'comments': comments,
                'comment_form': form,
                'day': day,
                'is_reviewer': True
            })
    
    return HttpResponse(status=405)
    
@login_required
def manage_reviewers(request):
    """レビュアー管理ページ"""
    my_reviewers = get_my_reviewers(request.user)
    
    if request.method == 'POST':
        form = ReviewerAddForm(request.POST, diary_owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'レビュアーを追加しました。')
            return redirect('diary:manage_reviewers')
    else:
        form = ReviewerAddForm(diary_owner=request.user)
    
    return render(request, 'diary/manage_reviewers.html', {
        'form': form,
        'reviewers': my_reviewers
    })


@login_required
def delete_reviewer(request, reviewer_id):
    """レビュアー削除"""
    reviewer = get_object_or_404(Reviewer, id=reviewer_id, diary_owner=request.user)
    reviewer.delete()
    messages.success(request, f'{reviewer.reviewer.username}をレビュアーから削除しました。')
    return redirect('diary:manage_reviewers')


@login_required
def review_list(request):
    """レビューページ - コメント可能な日記一覧"""
    reviewable_days = get_reviewable_days(request.user)
    return render(request, 'diary/review_list.html', {
        'day_list': reviewable_days
    })




# def index(request):
#     context = {
#         'day_list': Day.objects.all(),
#     }
#     return render(request, 'diary/day_list.html', context)


# def add(request):
#     form = DayCreateForm(request.POST or None)
    
#     if request.method == 'POST' and form.is_valid():
#         form.save()
#         return redirect('diary:index')
    
#     context = {
#         'form': form
#     }
#     return render(request, 'diary/day_form.html', context)


# def update(request, pk):
#     day = get_object_or_404(Day, pk=pk)

#     # instanceでformの初期値を設定する
#     form = DayCreateForm(request.POST or None, instance=day)

#     if request.method == 'POST' and form.is_valid():
#         form.save()
#         return redirect('diary:index')
    
#     context = {
#         'form': form
#     }
#     return render(request, 'diary/day_form.html', context) 


# def delete(request, pk):
#     day = get_object_or_404(Day, pk=pk)

#     if request.method == 'POST':
#         day.delete()
#         return redirect('diary:index')
    
#     context = {
#         'day': day,
#     }
#     return render(request, 'diary/day_confirm_delete.html', context) 


# def detail(request, pk):
#     day = get_object_or_404(Day, pk=pk)

#     context = {
#         'day': day,
#     }
#     return render(request, 'diary/day_detail.html', context) 
