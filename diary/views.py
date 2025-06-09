from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import DayCreateForm, ReviewerAddForm, CommentForm
from .models import Day, Reviewer, Comment
from .utils import get_my_reviewers, get_reviewable_days, get_reviewed_days, can_comment_on_day
from django.views import generic
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.middleware.csrf import get_token


class IndexView(LoginRequiredMixin, generic.ListView):
    model = Day
    template_name = 'diary/day_list.html'
    context_object_name = 'day_list'
    
    def get_queryset(self):
        queryset = Day.objects.filter(author=self.request.user)
        
        # 検索クエリを取得
        search_query = self.request.GET.get('search')
        if search_query:
            print(f"検索クエリ：{search_query}")
            
            try:
                from .vision_rag import search_days_by_image_content
                
                # 画像内容に基づく検索を実行
                matched_days = search_days_by_image_content(
                    query_text=search_query,
                    user_id=self.request.user.id,
                    top_k=20  # 最大20件まで返す
                )
                
                if matched_days:
                    # マッチした日記のIDリストを取得
                    matched_day_ids = [day.id for day in matched_days]
                    
                    # 元のクエリセットをマッチした日記に絞り込み
                    queryset = queryset.filter(id__in=matched_day_ids)
                    
                    # Vision-RAGの結果順序を保持するためのカスタム並び替え
                    preserved_order = {day_id: index for index, day_id in enumerate(matched_day_ids)}
                    queryset = sorted(queryset, key=lambda x: preserved_order.get(x.id, float('inf')))
                    
                    print(f"Vision-RAG検索結果: {len(matched_days)}件マッチ")
                else:
                    # マッチしなかった場合は空のクエリセットを返す
                    queryset = queryset.none()
                    print("Vision-RAG検索結果: マッチなし")
            except Exception as e:
                print(f"Vision-RAG検索中にエラーが発生しました: {e}")
                # エラー時は空の結果を返す
                queryset = queryset.none()
        # 検索クエリがない場合
        else:
            queryset = queryset
        
        return queryset
    
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
        
        # コメントフォーム（レビュアーかつ未レビューの場合のみ）
        comment_form = None
        if is_reviewer:
            # 自分がまだコメントしていない場合のみフォームを表示
            has_commented = Comment.objects.filter(day=day, author=user).exists()
            if not has_commented:
                comment_form = CommentForm()
        
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
    
    # 既にコメント済みかチェック
    if Comment.objects.filter(day=day, author=request.user).exists():
        return HttpResponse("<div class='text-red-500'>既にこの日記にコメント済みです</div>", status=400)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.day = day
            comment.author = request.user
            comment.save()
            
            # 新しいコメント一覧を返す（返信でないもののみ）
            comments = Comment.objects.filter(day=day, reply_to__isnull=True)
            
            return render(request, 'diary/partials/comment_section.html', {
                'comments': comments,
                # 'comment_form': form,
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
    form = ReviewerAddForm(diary_owner=request.user)
    
    return render(request, 'diary/manage_reviewers.html', {
        'form': form,
        'reviewers': my_reviewers
    })

@login_required
def add_reviewer_htmx(request):
    """HTMXを使用したレビュアー追加機能"""
    if request.method == 'POST':
        form = ReviewerAddForm(request.POST, diary_owner=request.user)
        if form.is_valid():
            form.save()
            # 成功時は新しい空のフォームとレビュアーリストの両方を更新
            new_form = ReviewerAddForm(diary_owner=request.user)
            my_reviewers = get_my_reviewers(request.user)
            
            # フォーム部分とリスト部分を含むHTMLを構築
            # out-of-band更新でレビュアーリストも同時に更新
            form_html = render_to_string('diary/partials/reviewer_form.html', {
                'form': new_form
            }, request=request)
            
            list_html = render_to_string('diary/partials/reviewer_list.html', {
                'reviewers': my_reviewers,
                'csrf_token': get_token(request)
            }, request=request)
            
            # メインのレスポンス（フォーム部分）とout-of-band更新（リスト部分）
            response_html = f'''
                {form_html}
                <div id="reviewer-list-section" hx-swap-oob="innerHTML">
                    {list_html}
                </div>
            '''
            
            return HttpResponse(response_html)
        else:
            # エラー時はフォーム部分のみを更新
            return render(request, 'diary/partials/reviewer_form.html', {
                'form': form
            })
    
    return HttpResponse(status=405)


@login_required
def delete_reviewer_htmx(request, reviewer_id):
    """HTMXを使用したレビュアー削除機能"""
    if request.method == 'DELETE':
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN')
        if not csrf_token:
            return HttpResponse(status=403)
            
        reviewer = get_object_or_404(Reviewer, id=reviewer_id, diary_owner=request.user)
        reviewer.delete()
        
        # 削除後の最新のレビュアーリストを取得
        updated_reviewers = get_my_reviewers(request.user)
        
        # リスト全体を更新
        list_html = render_to_string('diary/partials/reviewer_list.html', {
            'reviewers': updated_reviewers,
            'csrf_token': get_token(request)
        }, request=request)
        
        return HttpResponse(list_html)
    
    return HttpResponse(status=405)

@login_required
def review_list(request):
    """レビューページ - コメント可能な日記一覧（未レビューのみ）"""
    reviewable_days = get_reviewable_days(request.user)
    return render(request, 'diary/review_list.html', {
        'day_list': reviewable_days
    })

@login_required
def review_archive(request):
    """レビューアーカイブページ - レビュー済みの日記一覧"""
    reviewed_days = get_reviewed_days(request.user)
    return render(request, 'diary/review_archive.html', {
        'day_list': reviewed_days
    })