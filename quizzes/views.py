from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from django.forms import modelform_factory
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
import json

from courses.models import Course
from .models import Quiz, Question, Choice, QuizAttempt, StudentAnswer
from .forms import QuizForm, QuestionForm, ChoiceForm, StudentAnswerForm, ChoiceFormSet

class QuizListView(LoginRequiredMixin, View):
    """Quiz List View"""
    def get(self, request):
        # Student view - display quizzes available to the student
        if hasattr(request.user, 'is_student') and request.user.is_student():
            # Get quizzes from all courses
            # Not using student_profile.enrolled_courses due to auto-registration logic
            course_filter = {}
            if 'course' in request.GET and request.GET['course']:
                try:
                    course_id = int(request.GET['course'])
                    course_filter = {'id': course_id}
                except (ValueError, TypeError):
                    pass
                
            enrolled_courses = Course.objects.filter(**course_filter)
            
            # Get published quizzes from these courses
            available_quizzes = Quiz.objects.filter(
                course__in=enrolled_courses,
                is_published=True
            ).order_by('-created_at')
            
            # Get completed quizzes and their attempt records
            completed_attempts = QuizAttempt.objects.filter(
                student=request.user,
                is_completed=True
            ).select_related('quiz')
            
            completed_quiz_ids = [attempt.quiz_id for attempt in completed_attempts]
            completed_attempts_dict = {attempt.quiz_id: attempt for attempt in completed_attempts}
            
            # Add status information for each quiz
            now = timezone.now()
            quizzes_with_status = []
            
            for quiz in available_quizzes:
                quiz_status = {}
                quiz_status['id'] = quiz.id
                quiz_status['title'] = quiz.title
                quiz_status['description'] = quiz.description
                quiz_status['course'] = quiz.course
                quiz_status['time_limit'] = quiz.time_limit
                quiz_status['start_time'] = quiz.start_time
                quiz_status['end_time'] = quiz.end_time
                
                # Check if the quiz has been completed
                if quiz.id in completed_quiz_ids:
                    quiz_status['status'] = 'completed'
                    quiz_status['attempt'] = completed_attempts_dict[quiz.id]
                # Check if the quiz can be taken
                elif (quiz.start_time is None or now >= quiz.start_time) and (quiz.end_time is None or now <= quiz.end_time):
                    quiz_status['status'] = 'available'
                # Check if the quiz will start soon
                elif quiz.start_time and now < quiz.start_time:
                    quiz_status['status'] = 'upcoming'
                # Check if the quiz has expired
                elif quiz.end_time and now > quiz.end_time:
                    quiz_status['status'] = 'expired'
                
                quizzes_with_status.append(quiz_status)
                
            return render(request, 'quizzes/quiz_list.html', {
                'quizzes': quizzes_with_status,
                'enrolled_courses': enrolled_courses
            })
        
        # Teacher view - display quizzes created by the teacher
        else:
            quizzes = Quiz.objects.filter(course__instructor=request.user).order_by('-created_at')
            return render(request, 'quizzes/teacher_quiz_list.html', {
                'quizzes': quizzes
            })

class QuizDetailView(LoginRequiredMixin, View):
    """Quiz Detail View"""
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        now = timezone.now()
        
        # Confirm if it's a teacher view
        is_teacher = quiz.course.instructor == request.user
        
        # Prepare context
        context = {
            'quiz': quiz,
            'is_teacher': is_teacher,
            'can_attempt': False,
            'message': None,
            'now': now
        }

        # If it's a teacher, get all student attempt records
        if is_teacher:
            attempts = QuizAttempt.objects.filter(quiz=quiz).order_by('-started_at')
            context['attempts'] = attempts
            
            # Calculate average and highest scores
            if attempts.exists():
                total_score = sum(attempt.score for attempt in attempts)
                avg_score = total_score / attempts.count()
                highest_score = max(attempt.score for attempt in attempts)
                context['avg_score'] = avg_score
                context['highest_score'] = highest_score
            
            return render(request, 'quizzes/quiz_detail.html', context)
            
        # Student view below
        if hasattr(request.user, 'is_student') and request.user.is_student():
            # Check quiz status
            if not quiz.is_published:
                context['message'] = _("This quiz has not been published yet.")
                return render(request, 'quizzes/quiz_detail.html', context)
            
            # Check if already attempted the quiz
            has_completed = QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user,
                is_completed=True
            ).exists()
            
            # Get all attempt records (including incomplete ones)
            context['attempts'] = QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user
            ).order_by('-started_at')
            
            # Check quiz time limits
            if quiz.start_time and now < quiz.start_time:
                context['message'] = _("The quiz has not started yet.")
                return render(request, 'quizzes/quiz_detail.html', context)
                
            if quiz.end_time and now > quiz.end_time:
                context['message'] = _("The quiz has ended.")
                return render(request, 'quizzes/quiz_detail.html', context)
                
            if has_completed:
                context['message'] = _("You have already taken this quiz.")
                return render(request, 'quizzes/quiz_detail.html', context)
                
            # Can attempt quiz
            context['can_attempt'] = True
            context['message'] = _("You can take this quiz now. Note that each quiz can only be taken once.")
            
        return render(request, 'quizzes/quiz_detail.html', context)

class QuizAttemptView(LoginRequiredMixin, View):
    """Quiz Attempt View"""
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Confirm that the user is a student
        if not request.user.is_student():
            return HttpResponseForbidden(_("Only students can take quizzes."))
        
        # Check if the quiz can be attempted
        now = timezone.now()
        if not quiz.is_published:
            messages.error(request, _("This quiz is not published yet."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        if quiz.start_time and now < quiz.start_time:
            messages.error(request, _("This quiz has not started yet."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        if quiz.end_time and now > quiz.end_time:
            messages.error(request, _("This quiz has already ended."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        # Check if the quiz has already been attempted
        has_attempted = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user,
            is_completed=True
        ).exists()
        
        if has_attempted:
            messages.error(request, _("You have already completed this quiz. Each quiz can only be taken once."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        # Get or create quiz attempt record
        attempt, created = QuizAttempt.objects.get_or_create(
            quiz=quiz,
            student=request.user,
            is_completed=False,
            defaults={'started_at': now}
        )
        
        # Get quiz questions
        questions = quiz.get_questions()
        
        # Prepare question forms
        question_forms = []
        for question in questions:
            # Check if there is already an answer
            try:
                answer = StudentAnswer.objects.get(attempt=attempt, question=question)
                form = StudentAnswerForm(instance=answer, question=question)
            except StudentAnswer.DoesNotExist:
                form = StudentAnswerForm(question=question)
            
            question_forms.append((question, form))
        
        # Prepare context
        context = {
            'quiz': quiz,
            'attempt': attempt,
            'question_forms': question_forms,
            'time_limit': quiz.time_limit,
            'end_time': attempt.started_at + timezone.timedelta(minutes=quiz.time_limit) if quiz.time_limit > 0 else None
        }
        
        return render(request, 'quizzes/quiz_attempt.html', context)
    
    @transaction.atomic
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Confirm that the user is a student
        if not request.user.is_student():
            return HttpResponseForbidden(_("Only students can take quizzes."))
        
        # Get quiz attempt record
        try:
            attempt = QuizAttempt.objects.get(
                quiz=quiz,
                student=request.user,
                is_completed=False
            )
        except QuizAttempt.DoesNotExist:
            messages.error(request, _("No attempt record found for this quiz."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        # Check if time limit has been exceeded
        if quiz.time_limit > 0:
            now = timezone.now()
            end_time = attempt.started_at + timezone.timedelta(minutes=quiz.time_limit)
            if now > end_time:
                attempt.is_completed = True
                attempt.completed_at = end_time
                attempt.save()
                attempt.calculate_score()
                messages.warning(request, _("Time is up! Your answers have been automatically submitted."))
                return redirect('quizzes:quiz_result', attempt_id=attempt.id)
        
        # Process student answers
        questions = quiz.get_questions()
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            if not choice_id:
                continue
            
            try:
                choice = Choice.objects.get(id=choice_id, question=question)
                # Create or update answer
                StudentAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={'selected_choice': choice}
                )
            except Choice.DoesNotExist:
                continue
        
        # Mark attempt as completed
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        # Calculate score
        attempt.calculate_score()
        
        messages.success(request, _("Quiz completed! You can now view your results."))
        return redirect('quizzes:quiz_result', attempt_id=attempt.id)

class QuizResultView(LoginRequiredMixin, View):
    """Quiz Result View"""
    def get(self, request, attempt_id):
        attempt = get_object_or_404(QuizAttempt, id=attempt_id)
        
        # Verify permission to view
        if attempt.student != request.user and attempt.quiz.course.instructor != request.user:
            return HttpResponseForbidden(_("You don't have permission to view this quiz result."))
        
        # Get questions and answers
        questions = attempt.quiz.get_questions()
        answers = []
        
        for question in questions:
            try:
                answer = StudentAnswer.objects.get(attempt=attempt, question=question)
                is_correct = answer.selected_choice.is_correct
                answers.append({
                    'question': question,
                    'selected_choice': answer.selected_choice,
                    'is_correct': is_correct
                })
            except StudentAnswer.DoesNotExist:
                # Questions without answers
                answers.append({
                    'question': question,
                    'selected_choice': None,
                    'is_correct': False
                })
        
        # Add debug information
        correct_count = sum(1 for a in answers if a['is_correct'])
        total_count = questions.count()
        expected_score = (correct_count / total_count) * 100 if total_count > 0 else 0
        print(f"Debug - view: correct_answers: {correct_count}, total_questions: {total_count}, expected_score: {expected_score}, actual_score: {attempt.score}")
        
        # Prepare context
        context = {
            'attempt': attempt,
            'quiz': attempt.quiz,
            'score': attempt.score,
            'answers': answers,
            'total_questions': total_count,
            'correct_answers': correct_count
        }
        
        return render(request, 'quizzes/quiz_result.html', context)

class QuizDeleteView(LoginRequiredMixin, View):
    """Quiz Delete View"""
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Verify that the teacher is the course instructor
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only delete quizzes you created."))
            return redirect('quizzes:teacher_quiz_list')
        
        quiz_title = quiz.title
        quiz.delete()
        
        messages.success(request, _(f"Quiz '{quiz_title}' has been deleted successfully."))
        return redirect('quizzes:teacher_quiz_list')

class QuizCreateView(LoginRequiredMixin, View):
    """Quiz Creation View"""
    def get(self, request):
        # Get courses taught by the teacher
        courses = Course.objects.filter(instructor=request.user)
        if not courses.exists():
            messages.error(request, _("You need to create a course before creating a quiz."))
            return redirect('courses:course_create')
        
        # Create quiz form
        form = QuizForm()
        form.fields['course'].queryset = courses
        
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'courses': courses,
            'is_create': True
        })
    
    @transaction.atomic
    def post(self, request):
        # Get courses taught by the teacher
        courses = Course.objects.filter(instructor=request.user)
        
        # Process quiz form
        form = QuizForm(request.POST)
        form.fields['course'].queryset = courses
        
        if form.is_valid():
            # Save quiz
            quiz = form.save()
            
            # Process 5 questions
            questions_data = []
            for i in range(1, 6):  # Fixed 5 questions
                question_text = request.POST.get(f'question_{i}')
                if not question_text:
                    messages.error(request, _("All questions must be filled out."))
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'courses': courses,
                        'is_create': True
                    })
                
                # Create question
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_text,
                    question_number=i
                )
                
                # Process 4 choices
                choices_data = []
                correct_option = request.POST.get(f'question_{i}_correct')
                
                if not correct_option:
                    messages.error(request, _(f"Question {i} must have a correct answer selected."))
                    # Delete created question and choices
                    question.delete()
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'courses': courses,
                        'is_create': True
                    })
                    
                correct_option_num = int(correct_option)
                
                for j in range(1, 5):  # Fixed 4 choices
                    choice_text = request.POST.get(f'question_{i}_choice_{j}')
                    is_correct = (j == correct_option_num)
                    
                    if not choice_text:
                        messages.error(request, _(f"All choices for question {i} must be filled out."))
                        return render(request, 'quizzes/quiz_form.html', {
                            'form': form,
                            'courses': courses,
                            'is_create': True
                        })
                    
                    # Create choice
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=is_correct,
                        choice_number=j
                    )
            
            messages.success(request, _("Quiz created successfully!"))
            return redirect('quizzes:teacher_quiz_list')
        
        # Form validation failed
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'courses': courses,
            'is_create': True
        })

class QuizUpdateView(LoginRequiredMixin, View):
    """Quiz Update View"""
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Verify that the teacher is the course instructor
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only edit quizzes you created."))
            return redirect('quizzes:teacher_quiz_list')
        
        # Prepare quiz form
        form = QuizForm(instance=quiz)
        courses = Course.objects.filter(instructor=request.user)
        form.fields['course'].queryset = courses
        
        # Get quiz questions and choices
        questions = quiz.get_questions()
        
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'quiz': quiz,
            'questions': questions,
            'courses': courses,
            'is_create': False
        })
    
    @transaction.atomic
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Verify that the teacher is the course instructor
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only edit quizzes you created."))
            return redirect('quizzes:teacher_quiz_list')
        
        # Process quiz form
        form = QuizForm(request.POST, instance=quiz)
        courses = Course.objects.filter(instructor=request.user)
        form.fields['course'].queryset = courses
        
        if form.is_valid():
            # Save quiz
            quiz = form.save()
            
            # Process 5 questions
            for i in range(1, 6):  # Fixed 5 questions
                question_text = request.POST.get(f'question_{i}')
                
                if not question_text:
                    messages.error(request, _("All questions must be filled out."))
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'quiz': quiz,
                        'questions': quiz.get_questions(),
                        'courses': courses,
                        'is_create': False
                    })
                
                # Get or create question
                question = Question.objects.get_or_create(
                    quiz=quiz,
                    question_number=i,
                    defaults={'question_text': question_text}
                )[0]
                
                # Update question text
                question.question_text = question_text
                question.save()
                
                # Process 4 choices
                correct_option = request.POST.get(f'question_{i}_correct')
                
                if not correct_option:
                    messages.error(request, _(f"Question {i} must have a correct answer selected."))
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'quiz': quiz,
                        'questions': quiz.get_questions(),
                        'courses': courses,
                        'is_create': False
                    })
                    
                correct_option_num = int(correct_option)
                
                # First, reset all choices to not correct
                existing_choices = Choice.objects.filter(question=question)
                for choice in existing_choices:
                    choice.is_correct = False
                    choice.save()
                
                for j in range(1, 5):  # Fixed 4 choices
                    choice_text = request.POST.get(f'question_{i}_choice_{j}')
                    is_correct = (j == correct_option_num)
                    
                    if not choice_text:
                        messages.error(request, _(f"All choices for question {i} must be filled out."))
                        return render(request, 'quizzes/quiz_form.html', {
                            'form': form,
                            'quiz': quiz,
                            'questions': quiz.get_questions(),
                            'courses': courses,
                            'is_create': False
                        })
                    
                    # Get or create choice
                    choice = Choice.objects.get_or_create(
                        question=question,
                        choice_number=j,
                        defaults={'choice_text': choice_text, 'is_correct': is_correct}
                    )[0]
                    
                    # Update choice
                    choice.choice_text = choice_text
                    choice.is_correct = is_correct
                    choice.save()
            
            messages.success(request, _("Quiz updated successfully!"))
            return redirect('quizzes:teacher_quiz_list')
        
        # Form validation failed
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'quiz': quiz,
            'questions': quiz.get_questions(),
            'courses': courses,
            'is_create': False
        })

class TeacherQuizListView(LoginRequiredMixin, View):
    """Teacher Quiz List View"""
    def get(self, request):
        # Get all quizzes created by the current teacher
        quizzes = Quiz.objects.filter(course__instructor=request.user).order_by('-created_at')
        return render(request, 'quizzes/teacher_quiz_list.html', {
            'quizzes': quizzes
        })

class QuestionListView(LoginRequiredMixin, View):
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check if the teacher is the instructor of the course
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only manage questions for courses you teach."))
            return redirect('quizzes:teacher_quiz_list')
        
        # Get question data from session and process
        question_data = request.session.pop('question_data', None)
        if question_data:
            # Process question data directly here, not using post method
            import json
            try:
                questions_list = json.loads(question_data)
                
                # Create questions and choices
                for idx, q_data in enumerate(questions_list):
                    if not q_data.get('question', '') or not any(q_data.get('options', [])):
                        continue  # Skip empty questions
                    
                    # Create question
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        question_type='multiple_choice',
                        points=1,
                        order=idx
                    )
                    
                    # Create choices
                    for opt_idx, option_text in enumerate(q_data['options']):
                        if not option_text:
                            continue  # Skip empty options
                            
                        Choice.objects.create(
                            question=question,
                            choice_text=option_text,
                            is_correct=opt_idx in q_data.get('correctOptions', [])
                        )
                
                messages.success(request, _("Questions added successfully!"))
            except json.JSONDecodeError:
                messages.error(request, _("Invalid question data format."))
            except Exception as e:
                messages.error(request, _("Error adding questions: {}").format(str(e)))
        
        # Get questions for this quiz
        questions = quiz.questions.all().order_by('order')
        
        context = {
            'quiz': quiz,
            'questions': questions,
            'course': quiz.course,
            'success_message': request.GET.get('success', '')
        }
        
        return render(request, 'quizzes/question_list.html', context)
    
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check if the teacher is the instructor of the course
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only manage questions for courses you teach."))
            return redirect('quizzes:teacher_quiz_list')
        
        # Get question data from request or session
        question_data = request.POST.get('question_data', '')
        if not question_data and hasattr(request, 'session'):
            question_data = request.session.get('question_data', '')
        
        if question_data:
            import json
            try:
                questions_list = json.loads(question_data)
                
                # Create questions and choices
                for idx, q_data in enumerate(questions_list):
                    if not q_data.get('question', '') or not any(q_data.get('options', [])):
                        continue  # Skip empty questions
                    
                    # Create question
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        question_type='multiple_choice',
                        points=1,
                        order=idx
                    )
                    
                    # Create choices
                    for opt_idx, option_text in enumerate(q_data['options']):
                        if not option_text:
                            continue  # Skip empty options
                            
                        Choice.objects.create(
                            question=question,
                            choice_text=option_text,
                            is_correct=opt_idx in q_data.get('correctOptions', [])
                        )
                
                messages.success(request, _("Questions added successfully!"))
            except json.JSONDecodeError:
                messages.error(request, _("Invalid question data format."))
            except Exception as e:
                messages.error(request, _("Error adding questions: {}").format(str(e)))
        
        return redirect('quizzes:question_list', quiz_id=quiz.id)

class QuestionCreateView(View):
    def get(self, request, quiz_id):
        return render(request, 'quizzes/question_form.html')

class QuestionUpdateView(View):
    def get(self, request, quiz_id, question_id):
        return render(request, 'quizzes/question_form.html')

class QuestionDeleteView(View):
    def get(self, request, quiz_id, question_id):
        question = get_object_or_404(Question, id=question_id, quiz_id=quiz_id)
        
        # Check if the teacher is the instructor of the course
        if question.quiz.course.instructor != request.user:
            messages.error(request, _("You can only delete questions for quizzes in courses you teach."))
            return redirect('quizzes:teacher_quiz_list')
            
        context = {
            'question': question
        }
        return render(request, 'quizzes/question_confirm_delete.html', context)
        
    def post(self, request, quiz_id, question_id):
        question = get_object_or_404(Question, id=question_id, quiz_id=quiz_id)
        
        # Check if the teacher is the instructor of the course
        if question.quiz.course.instructor != request.user:
            messages.error(request, _("You can only delete questions for quizzes in courses you teach."))
            return redirect('quizzes:teacher_quiz_list')
        
        # Delete question
        question.delete()
        
        # Add success message
        messages.success(request, _("Question has been deleted successfully."))
        
        # Redirect to question list
        return redirect('quizzes:question_list', quiz_id=quiz_id)

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
