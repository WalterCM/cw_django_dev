from datetime import datetime

from django.db import models, IntegrityError
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


class QuestionQuerySet(models.QuerySet):
    def ranked(self):
        """
        Question queryset that orders the questions by points.
        It uses Count, Case and When instead of the points property because it was too slow.
        It was not good when scaled.

        Usage:
        Question.objects.ranked()
        """
        answer_points = settings.RANKING_CONFIGURATION.get('answer_points', 0)
        like_points = settings.RANKING_CONFIGURATION.get('like_points', 0)
        dislike_points = settings.RANKING_CONFIGURATION.get('dislike_points', 0)
        daily_bonus_points = settings.RANKING_CONFIGURATION.get('daily_bonus_points', 0)
        return self.annotate(
            total_points=(
                Count('answers', distinct=True) * answer_points +
                Count('votes', filter=Q(votes__is_like=True), distinct=True) * like_points +
                Count('votes', filter=Q(votes__is_like=False), distinct=True) * dislike_points +
                Case(
                    When(
                        created=datetime.today().date(),
                        then=Value(daily_bonus_points)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        ).order_by('-total_points')


class QuestionManager(models.Manager):
    def create_question(self, author=None, title=None, **kwargs):
        """
        Creates a new question. Checks for integrity of arguments
        """
        if not author:
            raise IntegrityError('Question requires an author')
        if not title:
            raise IntegrityError('Question requires a title')
        question = self.model(author=author, title=title, **kwargs)
        question.save()

        return question

    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def ranked(self):
        return self.get_queryset().ranked()


class Question(models.Model):
    created = models.DateField('Creada', auto_now_add=True)
    author = models.ForeignKey(
        get_user_model(),
        related_name='questions',
        verbose_name='Pregunta',
        on_delete=models.CASCADE
    )
    title = models.CharField('Título', max_length=200, blank=False, null=False)
    description = models.TextField('Descripción')

    objects = QuestionManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('survey:question-edit', args=[self.pk])

    @property
    def is_today(self):
        return self.created == datetime.today().date()

    @property
    def points(self):
        """
        Returns the amount of points the question has, depending on its answers, likes, dislikes,
        if it was created today, and ranking configuration in settings.

        Used only for individual objects, not querysets.
        """
        answers = self.answers.all().count()
        likes = self.votes.filter(is_like=True).count()
        dislikes = self.votes.filter(is_like=False).count()

        answer_points = settings.RANKING_CONFIGURATION.get('answer_points', 0)
        likes_points = settings.RANKING_CONFIGURATION.get('like_points', 0)
        dislikes_points = settings.RANKING_CONFIGURATION.get('dislike_points', 0)
        daily_bonus_points = settings.RANKING_CONFIGURATION.get('daily_bonus_points', 0)

        # Calculate points without daily bonus
        total_points = (
            answers * answer_points +
            likes * likes_points +
            dislikes * dislikes_points
        )

        # Apply daily bonus if it's today's question
        if self.is_today:
            total_points += daily_bonus_points

        return total_points


class AnswerManager(models.Manager):
    def create_answer(self, question=None, author=None, value=None, **kwargs):
        if not question:
            raise IntegrityError('Answer requires a question')
        if not author:
            raise IntegrityError('Answer requires an author')
        if not value:
            raise IntegrityError('Answer requires a value')

        answer = self.model(question=question, author=author, value=value, **kwargs)
        answer.save()

        return answer


class Answer(models.Model):
    ANSWERS_VALUES = ((0, 'Sin Responder'),
                      (1, 'Muy Bajo'),
                      (2, 'Bajo'),
                      (3, 'Regular'),
                      (4, 'Alto'),
                      (5, 'Muy Alto'),)

    question = models.ForeignKey(Question, related_name='answers', verbose_name='Pregunta', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='answers', verbose_name='Autor', on_delete=models.CASCADE)
    value = models.PositiveIntegerField('Respuesta', default=0, choices=ANSWERS_VALUES)
    comment = models.TextField('Comentario', default='', blank=True)

    objects = AnswerManager()

    class Meta:
        unique_together = ('author', 'question')

    def __str__(self):
        return '{question} - {author}:{value}'.format(question=self.question, author=self.author, value=self.value)


class Vote(models.Model):
    question = models.ForeignKey(Question, related_name='votes', verbose_name='Pregunta', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='votes', verbose_name='Autor', on_delete=models.CASCADE)
    is_like = models.BooleanField(default=None, null=True)

    class Meta:
        unique_together = ('author', 'question')

    def __str__(self):
        return '{question} - {author}:{like}'.format(
            question=self.question,
            author=self.author,
            like='like' if self.is_like else 'dislike'
        )
