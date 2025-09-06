from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # User-specific endpoints
    path('profile/stats/', views.UserStatsView.as_view(), name='user-stats'),
    path('profile/badges/', views.UserBadgesView.as_view(), name='user-badges'),
    path('profile/achievements/', views.UserAchievementsView.as_view(), name='user-achievements'),
    path('profile/progress/', views.user_progress_view, name='user-progress'),
    
    # Badge information
    path('badges/available/', views.AvailableBadgesView.as_view(), name='available-badges'),
    
    # Leaderboards
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard-monthly'),
    path('leaderboard/<str:period>/', views.LeaderboardView.as_view(), name='leaderboard'),
    
    # Global statistics
    path('stats/global/', views.global_stats_view, name='global-stats'),
    
    # Development/testing endpoints
    path('dev/simulate-checkin/', views.simulate_check_in_view, name='simulate-checkin'),
]