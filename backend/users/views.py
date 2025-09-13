from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer
import logging

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    """Register a new user"""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create a token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        })

class LoginView(APIView):
    """Log in an existing user"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                "user": UserSerializer(user).data,
                "token": token.key
            })
        
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

class LogoutView(APIView):
    """Log out the current user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Delete the token associated with the user
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass
            
        logout(request)
        
        return Response({"message": "Successfully logged out"})

class UserDetailView(generics.RetrieveAPIView):
    """Get the current user's details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


# HTML Template Views for Better UX
@csrf_exempt
def register_page(request):
    """Custom registration page with beautiful design"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Basic validation
        errors = []
        if not username:
            errors.append('Username is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if password != password2:
            errors.append('Passwords do not match')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists')
        
        if errors:
            next_url = request.GET.get('next', '')
            html = generate_auth_page('register', errors=errors, email=email, username=username, next_url=next_url)
            return HttpResponse(html)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.save()
        
        # Log them in automatically
        user = authenticate(username=username, password=password)
        login(request, user)
        
        # Redirect to next URL or admin
        next_url = request.GET.get('next', '/admin/')
        return redirect(next_url)
    
    # GET request - show registration form
    email = request.GET.get('email', '')
    next_url = request.GET.get('next', '')
    html = generate_auth_page('register', email=email, next_url=next_url)
    return HttpResponse(html)


@csrf_exempt
def login_page(request):
    """Custom login page with beautiful design"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate with username or email
        user = None
        if '@' in username:
            # Try email login
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        else:
            # Regular username login
            user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/admin/')
            return redirect(next_url)
        else:
            next_url = request.GET.get('next', '')
            html = generate_auth_page('login', errors=['Invalid username/email or password'], username=username, next_url=next_url)
            return HttpResponse(html)
    
    # GET request - show login form
    email = request.GET.get('email', '')
    next_url = request.GET.get('next', '')
    html = generate_auth_page('login', email=email, next_url=next_url)
    return HttpResponse(html)


def generate_auth_page(page_type, errors=None, email='', username='', next_url=''):
    """Generate beautiful HTML auth pages"""
    is_login = (page_type == 'login')
    
    # Build the error HTML separately
    error_html = ''
    if errors:
        error_items = ''.join(f'<li>{error}</li>' for error in errors)
        error_html = f'<div class="error-messages"><ul>{error_items}</ul></div>'
    
    # Build form fields based on page type
    if is_login:
        form_fields = f'''
            <div class="form-group">
                <label for="username">Username or Email</label>
                <input type="text" id="username" name="username" value="{username or email}" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
        '''
        button_text = 'Login to Your Account'
        next_param = f'?next={next_url}' if next_url else ''
        alt_action = f'Don\'t have an account? <a href="/api/auth/register-page/{next_param}">Create one now</a>'
    else:
        form_fields = f'''
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" value="{username}" required autofocus>
            </div>
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" value="{email}" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group">
                <label for="password2">Confirm Password</label>
                <input type="password" id="password2" name="password2" required>
            </div>
        '''
        button_text = 'Create Account'
        next_param = f'?next={next_url}' if next_url else ''
        alt_action = f'Already have an account? <a href="/api/auth/login-page/{next_param}">Login here</a>'
    
    # Benefits section only for registration
    benefits_html = '''
        <div class="benefits">
            <div class="benefit-item">
                <span>TROPHY</span> Earn badges for attendance and punctuality
            </div>
            <div class="benefit-item">
                <span>FIRE</span> Build streaks and climb leaderboards
            </div>
            <div class="benefit-item">
                <span>STATS</span> Track your event participation stats
            </div>
            <div class="benefit-item">
                <span>TARGET</span> Unlock special rewards and achievements
            </div>
        </div>
    ''' if not is_login else ''
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{'Login' if is_login else 'Create Account'} - QR Check-in System</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            
            .auth-container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
                max-width: 450px;
                width: 100%;
                animation: slideUp 0.5s ease;
            }}
            
            @keyframes slideUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .logo {{
                text-align: center;
                margin-bottom: 30px;
            }}
            
            .logo-icon {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
            
            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 10px;
                font-size: 28px;
            }}
            
            .subtitle {{
                text-align: center;
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }}
            
            .form-group {{
                margin-bottom: 20px;
            }}
            
            label {{
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 500;
                font-size: 14px;
            }}
            
            input {{
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e1e8ed;
                border-radius: 10px;
                font-size: 16px;
                transition: all 0.3s;
            }}
            
            input:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            
            .error-messages {{
                background: #fee;
                border: 1px solid #fcc;
                color: #c33;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            
            .error-messages ul {{
                margin: 0;
                padding-left: 20px;
            }}
            
            .btn {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}
            
            .divider {{
                text-align: center;
                margin: 25px 0;
                position: relative;
            }}
            
            .divider::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 1px;
                background: #e1e8ed;
            }}
            
            .divider span {{
                background: white;
                padding: 0 15px;
                color: #888;
                font-size: 14px;
                position: relative;
            }}
            
            .alt-action {{
                text-align: center;
                margin-top: 20px;
                font-size: 14px;
                color: #666;
            }}
            
            .alt-action a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }}
            
            .alt-action a:hover {{
                text-decoration: underline;
            }}
            
            .benefits {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                font-size: 13px;
                color: #666;
            }}
            
            .benefit-item {{
                margin-bottom: 8px;
                display: flex;
                align-items: center;
            }}
            
            .benefit-item span {{
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">
                <div class="logo-icon">{'SECURE' if is_login else 'GAME'}</div>
            </div>
            
            <h1>{'Welcome Back!' if is_login else 'Join the Fun!'}</h1>
            <p class="subtitle">
                {'Login to view your event stats' if is_login else 'Create an account to start earning rewards'}
            </p>
            
            {error_html}
            
            <form method="POST">
                {form_fields}
                <button type="submit" class="btn">
                    {button_text}
                </button>
            </form>
            
            <div class="alt-action">
                {alt_action}
            </div>
            
            {benefits_html}
        </div>
    </body>
    </html>
    """
    return html