from django.shortcuts import render, redirect, get_object_or_404
from .forms import DayCreateForm
from .models import Day
from django.views import generic
from django.urls import reverse_lazy

class IndexView(generic.ListView):
    model = Day
    template_name = 'diary/day_list.html'
    context_object_name = 'day_list'

class DetailView(generic.DetailView):
    model = Day
    template_name = 'diary/day_detail.html'
    context_object_name = 'day'

class CreateView(generic.CreateView):
    model = Day
    form_class = DayCreateForm
    template_name = 'diary/day_form.html'
    success_url = reverse_lazy('diary:index')

class UpdateView(generic.UpdateView):
    model = Day
    form_class = DayCreateForm
    template_name = 'diary/day_form.html'
    success_url = reverse_lazy('diary:index')

class DeleteView(generic.DeleteView):
    model = Day
    template_name = 'diary/day_confirm_delete.html'
    success_url = reverse_lazy('diary:index')
    context_object_name = 'day'


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
