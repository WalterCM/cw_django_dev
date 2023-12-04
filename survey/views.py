from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.db.models import IntegerField, BooleanField, Value, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from survey.models import Question, Answer, Vote


class QuestionListView(ListView):
    model = Question
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().ranked()

        if self.request.user.is_authenticated:
            # Annotates user_value (answer value) and is_like (if user liked or disliked the question) to each question
            user_answers = self.request.user.answers.filter(
                question_id=OuterRef('pk')
            ).values('value')

            user_votes = self.request.user.votes.filter(
                question_id=OuterRef('pk')
            ).values('is_like')

            queryset = queryset.annotate(
                user_value=Coalesce(Subquery(user_answers), Value(0), output_field=IntegerField()),
                is_like=Coalesce(Subquery(user_votes), Value(None), output_field=BooleanField())
            )

        return queryset


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    fields = ['title', 'description']
    redirect_url = ''
    success_url = reverse_lazy('survey:question-list')

    def form_valid(self, form):
        form.instance.author = self.request.user

        return super().form_valid(form)


class QuestionUpdateView(UpdateView):
    model = Question
    fields = ['title', 'description']
    template_name = 'survey/question_form.html'
    success_url = reverse_lazy('survey:question-list')


def answer_question(request):
    question_pk = request.POST.get('question_pk')
    if not question_pk:
        return JsonResponse({'ok': False})
    question = get_object_or_404(Question, pk=question_pk)
    answer, _ = Answer.objects.get_or_create(question=question, author=request.user)
    answer.value = request.POST.get('value')
    answer.save()
    return JsonResponse({'ok': True})


def like_dislike_question(request):
    question_pk = request.POST.get('question_pk')
    if not request.POST.get('question_pk'):
        return JsonResponse({'ok': False})
    question = get_object_or_404(Question, pk=question_pk)
    value = request.POST.get('value')
    vote, _ = Vote.objects.get_or_create(question=question, author=request.user)
    vote.is_like = True if value == 'like' else False
    vote.save()
    return JsonResponse({'ok': True})
