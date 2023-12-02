from django.db import models
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth import get_user_model


User = get_user_model()


class QuestionManager(models.Manager):
    def create_question(self, author=None, title=None, **kwargs):
        if not author:
            raise IntegrityError('Question requires an author')
        if not title:
            raise IntegrityError('Question requires a title')
        question = self.model(author=author, title=title, **kwargs)
        question.save()

        return question


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
    value = models.PositiveIntegerField('Respuesta', default=0)
    comment = models.TextField('Comentario', default='', blank=True)

    objects = AnswerManager()

    def __str__(self):
        return '{question} - {author}:{value}'.format(question=self.question, author=self.author, value=self.value)


class Vote(models.Model):
    question = models.ForeignKey(Question, related_name='votes', verbose_name='Pregunta', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='votes', verbose_name='Autor', on_delete=models.CASCADE)
    is_like = models.BooleanField(null=False)

    def __str__(self):
        return '{question} - {author}:{like}'.format(
            question=self.question,
            author=self.author,
            like='like' if self.is_like else 'dislike'
        )
