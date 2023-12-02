from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from survey.models import Question, Answer, Vote


class ModelTests(TestCase):
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

    def test_vote_no_like_or_dislike(self):
        """Tests that the function create_vote won't create a vote without indicating like or dislike"""
        vote_data = self.new_vote_data.copy()
        del vote_data['is_like']
        with self.assertRaises(IntegrityError):
            Vote.objects.create(**vote_data)
