from django.core.management.base import BaseCommand
from gamification.models import Badge


class Command(BaseCommand):
    help = 'Create sample badges for gamification system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing badges before creating new ones',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing badges...')
            Badge.objects.all().delete()
        
        sample_badges = [
            {
                'name': 'First Steps',
                'description': 'Attend your first event',
                'badge_type': 'attendance',
                'icon': 'target',
                'color': '#4CAF50',
                'criteria': {'events_required': 1, 'time_period': 'all_time'},
                'points_reward': 10
            },
            {
                'name': 'Early Bird',
                'description': 'Check in 30 minutes before event starts',
                'badge_type': 'punctuality',
                'icon': '🐦',
                'color': '#FFD700',
                'criteria': {'min_minutes_early': 30, 'max_minutes_early': 180},
                'points_reward': 15
            },
            {
                'name': 'Punctual Pro',
                'description': 'Check in within 15 minutes of start time',
                'badge_type': 'punctuality',
                'icon': '⏰',
                'color': '#2196F3',
                'criteria': {'min_minutes_early': 0, 'max_minutes_early': 15},
                'points_reward': 10
            },
            {
                'name': 'Attendance Champion',
                'description': 'Attend 10 events',
                'badge_type': 'attendance',
                'icon': 'trophy',
                'color': '#4CAF50',
                'criteria': {'events_required': 10, 'time_period': 'all_time'},
                'points_reward': 50
            },
            {
                'name': 'Dedication Master',
                'description': 'Attend 25 events',
                'badge_type': 'attendance',
                'icon': '👑',
                'color': '#9C27B0',
                'criteria': {'events_required': 25, 'time_period': 'all_time'},
                'points_reward': 100
            },
            {
                'name': 'Event Enthusiast',
                'description': 'Attend 50 events',
                'badge_type': 'attendance',
                'icon': 'star',
                'color': '#FF9800',
                'criteria': {'events_required': 50, 'time_period': 'all_time'},
                'points_reward': 200
            },
            {
                'name': 'Three Day Streak',
                'description': 'Maintain a 3-day attendance streak',
                'badge_type': 'streak',
                'icon': 'fire',
                'color': '#FF5722',
                'criteria': {'streak_required': 3, 'streak_type': 'current'},
                'points_reward': 25
            },
            {
                'name': 'Week Warrior',
                'description': 'Maintain a 7-day attendance streak',
                'badge_type': 'streak',
                'icon': 'fire',
                'color': '#F44336',
                'criteria': {'streak_required': 7, 'streak_type': 'current'},
                'points_reward': 50
            },
            {
                'name': 'Streak Legend',
                'description': 'Maintain a 14-day attendance streak',
                'badge_type': 'streak',
                'icon': '🌋',
                'color': '#D32F2F',
                'criteria': {'streak_required': 14, 'streak_type': 'current'},
                'points_reward': 100
            },
            {
                'name': 'Monthly Achiever',
                'description': 'Attend 30 days in a row',
                'badge_type': 'streak',
                'icon': 'mountain',
                'color': '#B71C1C',
                'criteria': {'streak_required': 30, 'streak_type': 'current'},
                'points_reward': 250
            },
            {
                'name': 'Social Butterfly',
                'description': 'Attend 5 networking events',
                'badge_type': 'networking',
                'icon': '🦋',
                'color': '#E91E63',
                'criteria': {'events_for_networking': 5},
                'points_reward': 30
            },
            {
                'name': 'Network Builder',
                'description': 'Attend 10 networking events',
                'badge_type': 'networking',
                'icon': '🌐',
                'color': '#9C27B0',
                'criteria': {'events_for_networking': 10},
                'points_reward': 75
            },
            {
                'name': 'VIP Guest',
                'description': 'Special badge for VIP attendees',
                'badge_type': 'special',
                'icon': '⭐',
                'color': '#FFD700',
                'criteria': {'event_type': 'vip'},
                'points_reward': 100
            },
            {
                'name': 'Weekend Warrior',
                'description': 'Attend weekend events',
                'badge_type': 'special',
                'icon': 'celebration',
                'color': '#795548',
                'criteria': {'weekend_events': 5},
                'points_reward': 40
            },
            {
                'name': 'Night Owl',
                'description': 'Attend evening events (after 6 PM)',
                'badge_type': 'special',
                'icon': '🦉',
                'color': '#607D8B',
                'criteria': {'evening_events': 3},
                'points_reward': 25
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for badge_data in sample_badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created badge: {badge.icon} {badge.name}')
                )
            else:
                # Update existing badge with new data
                for key, value in badge_data.items():
                    if key != 'name':  # Don't update the name (unique identifier)
                        setattr(badge, key, value)
                badge.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated badge: {badge.icon} {badge.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample badges setup complete:\n'
                f'- Created: {created_count} new badges\n'
                f'- Updated: {updated_count} existing badges\n'
                f'- Total badges: {Badge.objects.count()}'
            )
        )