from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import openai
from django.conf import settings
from .models import UserQuery

# Create your views here.

class AIAssistantHomeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ai_assistant/home.html')

class AIQueryAPIView(View):
    def post(self, request):
        try:
            # Parse request data
            data = json.loads(request.body)
            user_query = data.get('query', '')
            
            if not user_query:
                return JsonResponse({'error': 'Please provide query content'}, status=400)
            
            # Check if API key exists
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                print("Error: OpenAI API key not set")
                return JsonResponse({'error': 'OpenAI API key is not configured, please contact administrator'}, status=500)
            
            try:
                # Call OpenAI API
                client = openai.OpenAI(api_key=api_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use default model
                    messages=[
                        {"role": "system", "content": "You are a friendly learning assistant, focused on helping students answer learning questions."},
                        {"role": "user", "content": user_query}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )
                
                # Extract response content
                ai_response = response.choices[0].message.content
                
                # If user is logged in, save query record
                if request.user.is_authenticated:
                    UserQuery.objects.create(
                        user=request.user,
                        query=user_query,
                        response=ai_response
                    )
                
                return JsonResponse({'response': ai_response})
            
            except openai.APIError as e:
                error_msg = f"OpenAI API Error: {str(e)}"
                print(error_msg)
                return JsonResponse({'error': 'Error communicating with AI service, please try again later'}, status=500)
            
            except openai.APIConnectionError as e:
                error_msg = f"OpenAI API Connection Error: {str(e)}"
                print(error_msg)
                return JsonResponse({'error': 'Cannot connect to AI service, please check network connection'}, status=503)
            
            except openai.RateLimitError as e:
                error_msg = f"OpenAI API Rate Limit Error: {str(e)}"
                print(error_msg)
                return JsonResponse({'error': 'Too many requests to AI service, please try again later'}, status=429)
            
            except openai.AuthenticationError as e:
                error_msg = f"OpenAI API Authentication Error: {str(e)}"
                print(error_msg)
                return JsonResponse({'error': 'AI service authentication failed, please contact administrator'}, status=401)
            
            except Exception as e:
                error_msg = f"Unknown error occurred while calling OpenAI API: {str(e)}"
                print(error_msg)
                return JsonResponse({'error': 'Error processing your request, please try again later'}, status=500)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg)
            return JsonResponse({'error': 'Server error while processing request, please try again later'}, status=500)
