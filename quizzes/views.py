from django.shortcuts import render
from django.views.generic import View

class QuizListView(View):
    def get(self, request):
        return render(request, 'quizzes/quiz_list.html')

class QuizDetailView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/quiz_detail.html')

class StartQuizView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/start_quiz.html')

class QuizAttemptView(View):
    def get(self, request, quiz_id, attempt_id):
        return render(request, 'quizzes/quiz_attempt.html')

class SubmitQuizView(View):
    def post(self, request, quiz_id, attempt_id):
        return render(request, 'quizzes/quiz_results.html')

class QuizResultsView(View):
    def get(self, request, quiz_id, attempt_id):
        return render(request, 'quizzes/quiz_results.html')

class TeacherQuizListView(View):
    def get(self, request):
        return render(request, 'quizzes/teacher_quiz_list.html')

class QuizCreateView(View):
    def get(self, request):
        return render(request, 'quizzes/quiz_form.html')

class QuizUpdateView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/quiz_form.html')

class QuizDeleteView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/quiz_confirm_delete.html')

class PublishQuizView(View):
    def post(self, request, quiz_id):
        return render(request, 'quizzes/teacher_quiz_list.html')

class QuestionListView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/question_list.html')

class QuestionCreateView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/question_form.html')

class QuestionUpdateView(View):
    def get(self, request, quiz_id, question_id):
        return render(request, 'quizzes/question_form.html')

class QuestionDeleteView(View):
    def get(self, request, quiz_id, question_id):
        return render(request, 'quizzes/question_confirm_delete.html')

class AssignmentListView(View):
    def get(self, request):
        return render(request, 'quizzes/assignment_list.html')

class AssignmentDetailView(View):
    def get(self, request, assignment_id):
        return render(request, 'quizzes/assignment_detail.html')

class SubmitAssignmentView(View):
    def post(self, request, assignment_id):
        return render(request, 'quizzes/assignment_detail.html')

class TeacherAssignmentListView(View):
    def get(self, request):
        return render(request, 'quizzes/teacher_assignment_list.html')

class AssignmentCreateView(View):
    def get(self, request):
        return render(request, 'quizzes/assignment_form.html')

class AssignmentUpdateView(View):
    def get(self, request, assignment_id):
        return render(request, 'quizzes/assignment_form.html')

class AssignmentDeleteView(View):
    def get(self, request, assignment_id):
        return render(request, 'quizzes/assignment_confirm_delete.html')

class AssignmentSubmissionListView(View):
    def get(self, request, assignment_id):
        return render(request, 'quizzes/assignment_submission_list.html')

class GradeSubmissionView(View):
    def get(self, request, assignment_id, submission_id):
        return render(request, 'quizzes/grade_submission.html')
