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
    """测验列表视图"""
    def get(self, request):
        # 学生视图 - 显示学生可以参加的测验
        if hasattr(request.user, 'is_student') and request.user.is_student():
            # 获取所有课程的测验
            # 不使用student_profile.enrolled_courses，因为自动注册逻辑
            course_filter = {}
            if 'course' in request.GET and request.GET['course']:
                try:
                    course_id = int(request.GET['course'])
                    course_filter = {'id': course_id}
                except (ValueError, TypeError):
                    pass
                
            enrolled_courses = Course.objects.filter(**course_filter)
            
            # 获取这些课程中已发布的测验
            available_quizzes = Quiz.objects.filter(
                course__in=enrolled_courses,
                is_published=True
            ).order_by('-created_at')
            
            # 获取已完成的测验及其尝试记录
            completed_attempts = QuizAttempt.objects.filter(
                student=request.user,
                is_completed=True
            ).select_related('quiz')
            
            completed_quiz_ids = [attempt.quiz_id for attempt in completed_attempts]
            completed_attempts_dict = {attempt.quiz_id: attempt for attempt in completed_attempts}
            
            # 为每个测验添加状态信息
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
                
                # 检查测验是否已完成
                if quiz.id in completed_quiz_ids:
                    quiz_status['status'] = 'completed'
                    quiz_status['attempt'] = completed_attempts_dict[quiz.id]
                # 检查测验是否可以参加
                elif (quiz.start_time is None or now >= quiz.start_time) and (quiz.end_time is None or now <= quiz.end_time):
                    quiz_status['status'] = 'available'
                # 检查测验是否即将开始
                elif quiz.start_time and now < quiz.start_time:
                    quiz_status['status'] = 'upcoming'
                # 检查测验是否已过期
                elif quiz.end_time and now > quiz.end_time:
                    quiz_status['status'] = 'expired'
                
                quizzes_with_status.append(quiz_status)
                
            return render(request, 'quizzes/quiz_list.html', {
                'quizzes': quizzes_with_status,
                'enrolled_courses': enrolled_courses
            })
        
        # 教师视图 - 显示教师创建的测验
        else:
            quizzes = Quiz.objects.filter(course__instructor=request.user).order_by('-created_at')
            return render(request, 'quizzes/teacher_quiz_list.html', {
                'quizzes': quizzes
            })

class QuizDetailView(LoginRequiredMixin, View):
    """测验详情视图"""
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # 确认是否是教师视图
        is_teacher_view = quiz.course.instructor == request.user
        
        # 确认是否是学生视图
        is_student_view = False
        is_enrolled = True  # 假设所有学生都已注册
        can_attempt = False
        
        if hasattr(request.user, 'is_student') and request.user.is_student():
            is_student_view = True
            
            # 检查是否已经尝试过该测验
            has_attempted = QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user,
                is_completed=True
            ).exists()
            
            # 检查测验是否可以参加
            now = timezone.now()
            is_available = (
                quiz.is_published and
                (quiz.start_time is None or now >= quiz.start_time) and
                (quiz.end_time is None or now <= quiz.end_time)
            )
            
            can_attempt = is_available and not has_attempted
        
        # 获取学生的尝试记录
        attempts = []
        if is_student_view:
            attempts = QuizAttempt.objects.filter(
                quiz=quiz,
                student=request.user
            ).order_by('-started_at')
        
        # 准备上下文
        context = {
            'quiz': quiz,
            'is_teacher_view': is_teacher_view,
            'is_student_view': is_student_view,
            'is_enrolled': is_enrolled,
            'can_attempt': can_attempt,
            'attempts': attempts
        }
        
        return render(request, 'quizzes/quiz_detail.html', context)

class QuizAttemptView(LoginRequiredMixin, View):
    """测验尝试视图"""
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # 确认用户是学生
        if not request.user.is_student():
            return HttpResponseForbidden(_("Only students can take quizzes."))
        
        # 检查测验是否可以参加
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
        
        # 检查是否已经尝试过该测验
        has_attempted = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user,
            is_completed=True
        ).exists()
        
        if has_attempted:
            messages.error(request, _("You have already completed this quiz. Each quiz can only be taken once."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        # 获取或创建测验尝试记录
        attempt, created = QuizAttempt.objects.get_or_create(
            quiz=quiz,
            student=request.user,
            is_completed=False,
            defaults={'started_at': now}
        )
        
        # 获取测验问题
        questions = quiz.get_questions()
        
        # 准备问题表单
        question_forms = []
        for question in questions:
            # 检查是否已有答案
            try:
                answer = StudentAnswer.objects.get(attempt=attempt, question=question)
                form = StudentAnswerForm(instance=answer, question=question)
            except StudentAnswer.DoesNotExist:
                form = StudentAnswerForm(question=question)
            
            question_forms.append((question, form))
        
        # 准备上下文
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
        
        # 确认用户是学生
        if not request.user.is_student():
            return HttpResponseForbidden(_("Only students can take quizzes."))
        
        # 获取测验尝试记录
        try:
            attempt = QuizAttempt.objects.get(
                quiz=quiz,
                student=request.user,
                is_completed=False
            )
        except QuizAttempt.DoesNotExist:
            messages.error(request, _("No attempt record found for this quiz."))
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
        
        # 检查是否超时
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
        
        # 处理学生答案
        questions = quiz.get_questions()
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            if not choice_id:
                continue
            
            try:
                choice = Choice.objects.get(id=choice_id, question=question)
                # 创建或更新答案
                StudentAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={'selected_choice': choice}
                )
            except Choice.DoesNotExist:
                continue
        
        # 标记尝试为已完成
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        # 计算得分
        attempt.calculate_score()
        
        messages.success(request, _("Quiz completed! You can now view your results."))
        return redirect('quizzes:quiz_result', attempt_id=attempt.id)

class QuizResultView(LoginRequiredMixin, View):
    """测验结果视图"""
    def get(self, request, attempt_id):
        attempt = get_object_or_404(QuizAttempt, id=attempt_id)
        
        # 确认是否有权查看
        if attempt.student != request.user and attempt.quiz.course.instructor != request.user:
            return HttpResponseForbidden(_("You don't have permission to view this quiz result."))
        
        # 获取问题和答案
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
                # 没有回答的问题
                answers.append({
                    'question': question,
                    'selected_choice': None,
                    'is_correct': False
                })
        
        # 准备上下文
        context = {
            'attempt': attempt,
            'quiz': attempt.quiz,
            'score': attempt.score,
            'answers': answers,
            'total_questions': questions.count(),
            'correct_answers': sum(1 for a in answers if a['is_correct'])
        }
        
        return render(request, 'quizzes/quiz_result.html', context)

class QuizDeleteView(LoginRequiredMixin, View):
    """测验删除视图"""
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # 确认教师是课程的讲师
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only delete quizzes you created."))
            return redirect('quizzes:teacher_quiz_list')
        
        quiz_title = quiz.title
        quiz.delete()
        
        messages.success(request, _(f"Quiz '{quiz_title}' has been deleted successfully."))
        return redirect('quizzes:teacher_quiz_list')

class QuizCreateView(LoginRequiredMixin, View):
    """测验创建视图"""
    def get(self, request):
        # 获取教师教授的课程
        courses = Course.objects.filter(instructor=request.user)
        if not courses.exists():
            messages.error(request, _("You need to create a course before creating a quiz."))
            return redirect('courses:course_create')
        
        # 创建测验表单
        form = QuizForm()
        form.fields['course'].queryset = courses
        
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'courses': courses,
            'is_create': True
        })
    
    @transaction.atomic
    def post(self, request):
        # 获取教师教授的课程
        courses = Course.objects.filter(instructor=request.user)
        
        # 处理测验表单
        form = QuizForm(request.POST)
        form.fields['course'].queryset = courses
        
        if form.is_valid():
            # 保存测验
            quiz = form.save()
            
            # 处理5个问题
            questions_data = []
            for i in range(1, 6):  # 固定5个问题
                question_text = request.POST.get(f'question_{i}')
                if not question_text:
                    messages.error(request, _("All questions must be filled out."))
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'courses': courses,
                        'is_create': True
                    })
                
                # 创建问题
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=question_text,
                    question_number=i
                )
                
                # 处理4个选项
                choices_data = []
                has_correct = False
                for j in range(1, 5):  # 固定4个选项
                    choice_text = request.POST.get(f'question_{i}_choice_{j}')
                    is_correct = request.POST.get(f'question_{i}_correct_{j}') == 'on'
                    
                    if not choice_text:
                        messages.error(request, _(f"All choices for question {i} must be filled out."))
                        return render(request, 'quizzes/quiz_form.html', {
                            'form': form,
                            'courses': courses,
                            'is_create': True
                        })
                    
                    if is_correct:
                        has_correct = True
                    
                    # 创建选项
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=is_correct,
                        choice_number=j
                    )
                
                # 确保每个问题至少有一个正确答案
                if not has_correct:
                    messages.error(request, _(f"Question {i} must be marked with at least one correct answer."))
                    # 删除已创建的问题和选项
                    question.delete()
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'courses': courses,
                        'is_create': True
                    })
            
            messages.success(request, _("Quiz created successfully!"))
            return redirect('quizzes:teacher_quiz_list')
        
        # 表单验证失败
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'courses': courses,
            'is_create': True
        })

class QuizUpdateView(LoginRequiredMixin, View):
    """测验更新视图"""
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # 确认教师是课程的讲师
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only edit quizzes you created."))
            return redirect('quizzes:teacher_quiz_list')
        
        # 准备测验表单
        form = QuizForm(instance=quiz)
        courses = Course.objects.filter(instructor=request.user)
        form.fields['course'].queryset = courses
        
        # 获取测验的问题和选项
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
        
        # 确认教师是课程的讲师
        if quiz.course.instructor != request.user:
            messages.error(request, _("You can only edit quizzes you created."))
            return redirect('quizzes:teacher_quiz_list')
        
        # 处理测验表单
        form = QuizForm(request.POST, instance=quiz)
        courses = Course.objects.filter(instructor=request.user)
        form.fields['course'].queryset = courses
        
        if form.is_valid():
            # 保存测验
            quiz = form.save()
            
            # 处理5个问题
            for i in range(1, 6):  # 固定5个问题
                question = Question.objects.get_or_create(
                    quiz=quiz,
                    question_number=i,
                    defaults={'question_text': ''}
                )[0]
                
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
                
                question.question_text = question_text
                question.save()
                
                # 处理4个选项
                has_correct = False
                for j in range(1, 5):  # 固定4个选项
                    choice = Choice.objects.get_or_create(
                        question=question,
                        choice_number=j,
                        defaults={'choice_text': '', 'is_correct': False}
                    )[0]
                    
                    choice_text = request.POST.get(f'question_{i}_choice_{j}')
                    is_correct = request.POST.get(f'question_{i}_correct_{j}') == 'on'
                    
                    if not choice_text:
                        messages.error(request, _(f"All choices for question {i} must be filled out."))
                        return render(request, 'quizzes/quiz_form.html', {
                            'form': form,
                            'quiz': quiz,
                            'questions': quiz.get_questions(),
                            'courses': courses,
                            'is_create': False
                        })
                    
                    if is_correct:
                        has_correct = True
                    
                    choice.choice_text = choice_text
                    choice.is_correct = is_correct
                    choice.save()
                
                # 确保每个问题至少有一个正确答案
                if not has_correct:
                    messages.error(request, _(f"Question {i} must be marked with at least one correct answer."))
                    return render(request, 'quizzes/quiz_form.html', {
                        'form': form,
                        'quiz': quiz,
                        'questions': quiz.get_questions(),
                        'courses': courses,
                        'is_create': False
                    })
            
            messages.success(request, _("Quiz updated successfully!"))
            return redirect('quizzes:teacher_quiz_list')
        
        # 表单验证失败
        return render(request, 'quizzes/quiz_form.html', {
            'form': form,
            'quiz': quiz,
            'questions': quiz.get_questions(),
            'courses': courses,
            'is_create': False
        })

class TeacherQuizListView(LoginRequiredMixin, View):
    """教师测验列表视图"""
    def get(self, request):
        # 获取当前教师创建的所有测验
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
        
        # 从会话中获取问题数据并处理
        question_data = request.session.pop('question_data', None)
        if question_data:
            # 直接在这里处理问题数据，不使用post方法
            import json
            try:
                questions_list = json.loads(question_data)
                
                # 创建问题和选项
                for idx, q_data in enumerate(questions_list):
                    if not q_data.get('question', '') or not any(q_data.get('options', [])):
                        continue  # 跳过空问题
                    
                    # 创建问题
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        question_type='multiple_choice',
                        points=1,
                        order=idx
                    )
                    
                    # 创建选项
                    for opt_idx, option_text in enumerate(q_data['options']):
                        if not option_text:
                            continue  # 跳过空选项
                            
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
        
        # 从请求或会话中获取问题数据
        question_data = request.POST.get('question_data', '')
        if not question_data and hasattr(request, 'session'):
            question_data = request.session.get('question_data', '')
        
        if question_data:
            import json
            try:
                questions_list = json.loads(question_data)
                
                # 创建问题和选项
                for idx, q_data in enumerate(questions_list):
                    if not q_data.get('question', '') or not any(q_data.get('options', [])):
                        continue  # 跳过空问题
                    
                    # 创建问题
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        question_type='multiple_choice',
                        points=1,
                        order=idx
                    )
                    
                    # 创建选项
                    for opt_idx, option_text in enumerate(q_data['options']):
                        if not option_text:
                            continue  # 跳过空选项
                            
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
        
        # 检查教师是否是该课程的讲师
        if question.quiz.course.instructor != request.user:
            messages.error(request, _("You can only delete questions for quizzes in courses you teach."))
            return redirect('quizzes:teacher_quiz_list')
            
        context = {
            'question': question
        }
        return render(request, 'quizzes/question_confirm_delete.html', context)
        
    def post(self, request, quiz_id, question_id):
        question = get_object_or_404(Question, id=question_id, quiz_id=quiz_id)
        
        # 检查教师是否是该课程的讲师
        if question.quiz.course.instructor != request.user:
            messages.error(request, _("You can only delete questions for quizzes in courses you teach."))
            return redirect('quizzes:teacher_quiz_list')
        
        # 删除问题
        question.delete()
        
        # 添加成功消息
        messages.success(request, _("Question has been deleted successfully."))
        
        # 重定向到问题列表
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
