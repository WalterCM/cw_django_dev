from datetime import datetime, timedelta

from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse

from survey.models import Question, Answer, Vote


class BasicModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.question = Question.objects.create(
            title='Que te parecio el ejercicio?',
            description='Esta es una pregunta sobre la prueba tecnica',
            author=self.user
        )
        self.new_question_data = {
            'title': 'Te gusta el futbol?',
            'description': 'Esta es una pregunta sobre futbol',
            'author': self.user
        }
        self.new_answer_data = {
            'question': self.question,
            'author': self.user,
            'value': 5,
            'comment': 'El ejercicio me parecio muy bueno'
        }

        self.new_vote_data = {
            'question': self.question,
            'author': self.user,
            'is_like': True
        }

    def test_question_creation(self):
        """Tests the creation of a question with expected data"""
        question = Question.objects.create_question(**self.new_question_data)
        self.assertEqual(question.title, self.new_question_data.get('title'))
        self.assertEqual(question.description, self.new_question_data.get('description'))
        self.assertEqual(question.author, self.new_question_data.get('author'))

    def test_question_creation_no_title(self):
        """Tests that the function create_question won't create a question without title"""
        question_data = self.new_question_data.copy()
        del question_data['title']
        with self.assertRaises(IntegrityError):
            Question.objects.create_question(**question_data)

    def test_question_creation_no_author(self):
        """Tests that the function create_question won't create a question without an author"""
        question_data = self.new_question_data.copy()
        del question_data['author']
        with self.assertRaises(IntegrityError):
            Question.objects.create_question(**question_data)

    def test_answer_creation(self):
        """Tests the creation of an answer with expected data"""
        answer = Answer.objects.create(**self.new_answer_data)
        self.assertEqual(answer.value, self.new_answer_data.get('value'))
        self.assertEqual(answer.question, self.new_answer_data.get('question'))
        self.assertEqual(answer.author, self.new_answer_data.get('author'))
        self.assertEqual(answer.comment, self.new_answer_data.get('comment'))

    def test_answer_creation_no_value(self):
        """Tests that the function create_answer won't create an answer without a value"""
        answer_data = self.new_answer_data.copy()
        del answer_data['value']
        with self.assertRaises(IntegrityError):
            Answer.objects.create_answer(**answer_data)

    def test_answer_creation_no_question(self):
        """Tests that the function create_answer won't create an answer without a question"""
        answer_data = self.new_answer_data.copy()
        del answer_data['question']
        with self.assertRaises(IntegrityError):
            Answer.objects.create_answer(**answer_data)

    def test_answer_creation_no_author(self):
        """Tests that the function create_answer won't create an answer without an author"""
        answer_data = self.new_answer_data.copy()
        del answer_data['author']
        with self.assertRaises(IntegrityError):
            Answer.objects.create_answer(**answer_data)

    def test_vote_creation(self):
        """Tests the creation of a vote with expected data"""
        vote = Vote.objects.create(**self.new_vote_data)
        self.assertEqual(vote.question, self.new_vote_data.get('question'))
        self.assertEqual(vote.author, self.new_vote_data.get('author'))
        self.assertEqual(vote.is_like, self.new_vote_data.get('is_like'))

    def test_vote_no_question(self):
        """Tests that the function create_vote won't create a vote without a question"""
        vote_data = self.new_vote_data.copy()
        del vote_data['question']
        with self.assertRaises(IntegrityError):
            Vote.objects.create(**vote_data)

    def test_vote_no_author(self):
        """Tests that the function create_vote won't create a vote without an author"""
        vote_data = self.new_vote_data.copy()
        del vote_data['author']
        with self.assertRaises(IntegrityError):
            Vote.objects.create(**vote_data)


class RankingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.user2 = User.objects.create_user(username='test_user2', password='22345')
        self.user3 = User.objects.create_user(username='test_user3', password='33345')
        self.user4 = User.objects.create_user(username='test_user4', password='44445')

        self.today_question = Question.objects.create(
            title='Today question',
            author=self.user
        )

        self.non_today_question = Question.objects.create(
            title='Yesterday question',
            author=self.user
        )
        self.non_today_question.created = datetime.today().date() - timedelta(days=1)
        self.non_today_question.save()

        self.answer_points = settings.RANKING_CONFIGURATION.get('answer_points', 0)
        self.like_points = settings.RANKING_CONFIGURATION.get('like_points', 0)
        self.dislike_points = settings.RANKING_CONFIGURATION.get('dislike_points', 0)
        self.daily_bonus_points = settings.RANKING_CONFIGURATION.get('daily_bonus_points', 0)

    def test_points_for_answers(self):
        """Tests that answers increases points by the amount in settings for answers"""
        self.non_today_question.answers.create(author=self.user, value=1)
        self.assertEqual(self.non_today_question.points, self.answer_points)
        self.non_today_question.answers.create(author=self.user2, value=2)
        self.non_today_question.answers.create(author=self.user3, value=3)
        self.assertEqual(self.non_today_question.points, self.answer_points * 3)

    def test_points_for_likes(self):
        """Tests that likes increases points by the amount in settings for likes"""
        self.non_today_question.votes.create(author=self.user, is_like=True)
        self.assertEqual(self.non_today_question.points, self.like_points)
        self.non_today_question.votes.create(author=self.user2, is_like=True)
        self.assertEqual(self.non_today_question.points, self.like_points * 2)

    def test_points_for_dislikes(self):
        """Tests that dislikes increases points by the amount in settings for dislikes"""
        self.non_today_question.votes.create(author=self.user, is_like=False)
        self.assertEqual(self.non_today_question.points, self.dislike_points)
        self.non_today_question.votes.create(author=self.user2, is_like=False)
        self.assertEqual(self.non_today_question.points, self.dislike_points * 2)

    def test_points_for_today_questions(self):
        """Tests there is a bonus to questions that are created today"""
        expected_points = self.daily_bonus_points
        self.assertEqual(self.today_question.points, expected_points)
        self.assertEqual(self.non_today_question.points, 0)

    def test_points_mix(self):
        """Tests different combinations of answers, likes, dislikes and the daily bonus"""
        self.non_today_question.votes.create(author=self.user, is_like=True)
        self.non_today_question.votes.create(author=self.user2, is_like=False)
        expected_points = self.like_points + self.dislike_points
        self.assertEqual(self.non_today_question.points, expected_points)

        self.non_today_question.answers.create(author=self.user, value=3)
        self.non_today_question.votes.create(author=self.user3, is_like=True)
        expected_points += self.like_points + self.answer_points
        self.assertEqual(self.non_today_question.points, expected_points)

        self.today_question.answers.create(author=self.user, value=2)
        self.today_question.votes.create(author=self.user, is_like=False)
        expected_points = self.answer_points + self.dislike_points + self.daily_bonus_points
        self.assertEqual(self.today_question.points, expected_points)

        self.today_question.votes.create(author=self.user2, is_like=True)
        self.today_question.votes.create(author=self.user3, is_like=True)
        self.today_question.votes.create(author=self.user4, is_like=True)
        expected_points += self.like_points * 3
        self.assertEqual(self.today_question.points, expected_points)

    def test_ranked_queryset(self):
        """Tests the ranked queryset of Questions"""

        # Add a dislike to the yesterday questioun
        self.non_today_question.votes.create(author=self.user, is_like=False)
        # Create a few more questions to test ranking
        for i in range(5):
            Question.objects.create(title='Test question', author=self.user)

        # Get the questions in a ranking
        ranked_questions = Question.objects.ranked()

        # First is today question because of the bonus
        self.assertEqual(ranked_questions.first(), self.today_question)
        # Last is yesterday question because it also has a dislike
        self.assertEqual(ranked_questions.last(), self.non_today_question)

        # Ensure the queryset is ordered by total_points in descending order
        last_question_points = float('inf')
        for question in ranked_questions:
            self.assertLessEqual(question.points, last_question_points)
            last_question_points = question.points


class ViewTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'test_user',
            'password': 'qwerty'
        }
        self.user = User.objects.create_user(**self.user_data)

        self.question_data = {
            'title': 'Test Question',
            'description': 'This is a test question.',
        }
        Question.objects.create_question(author=self.user, **self.question_data)

    def test_question_list_view_no_auth(self):
        response = self.client.get(reverse('survey:question-list'))
        self.assertEqual(response.status_code, 200)

    def test_question_list_view(self):
        self.client.login(**self.user_data)
        response = self.client.get(reverse('survey:question-list'))
        self.assertEqual(response.status_code, 200)

    def test_question_create_view_no_auth(self):
        create_url = reverse('survey:question-create')
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/registration/login/?next={}'.format(create_url))

    def test_question_create_view(self):
        create_url = reverse('survey:question-create')
        self.client.login(**self.user_data)

        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(create_url, data=self.question_data)
        self.assertEqual(response.status_code, 302)

        created_question = Question.objects.first()
        self.assertEqual(created_question.title, self.question_data.get('title'))
        self.assertEqual(created_question.description, self.question_data.get('description'))

    def test_question_create_view_no_title(self):
        create_url = reverse('survey:question-create')
        self.client.login(**self.user_data)

        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)

        question_data = self.question_data.copy()
        del question_data['title']

        response = self.client.post(create_url, data=question_data)
        # it doesn't redirect, just returns with the invalid form errors
        self.assertEqual(response.status_code, 200)

    def test_question_update_view(self):
        self.client.login(**self.user_data)
        question_id = 1
        response = self.client.get(reverse('survey:question-edit', kwargs={'pk': question_id}))
        self.assertEqual(response.status_code, 200)

    def test_answer_question_view(self):
        self.client.login(**self.user_data)
        question_id = 1
        data = {'question_pk': question_id, 'value': 5}
        response = self.client.post(reverse('survey:question-answer'), data=data)
        self.assertEqual(response.status_code, 200)

    def test_like_dislike_question_view(self):
        self.client.login(**self.user_data)
        question_id = 1
        data = {'question_pk': question_id, 'value': 'like'}
        response = self.client.post(reverse('survey:question-like'), data=data)
        self.assertEqual(response.status_code, 200)
