from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import DayCreateForm, ReviewerAddForm
from .models import Day, Reviewer
from .utils import get_my_reviewers
from django.views import generic
from django.urls import reverse_lazy


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
        return Day.objects.filter(author=self.request.user)


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
