#!/usr/bin/env python3
"""
Script to create sample icebreaker activities
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, '/home/sabiut/Documents/Personal/qr-checkin-system/backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qrcheckin.settings')
django.setup()

from communication.models import IcebreakerActivity
from events.models import Event
from django.contrib.auth.models import User

def create_sample_activities():
    print("Creating sample icebreaker activities...")

    # Get the first event and user
    try:
        event = Event.objects.first()
        user = User.objects.first()

        if not event:
            print("❌ No events found. Please create an event first.")
            return

        if not user:
            print("❌ No users found. Please create a user first.")
            return

        print(f"📅 Using event: {event.name}")
        print(f"👤 Using creator: {user.username}")

        # Sample activities to create
        activities = [
            {
                'title': '🗳️ Welcome Poll: What excites you most?',
                'description': 'Help us understand what attendees are looking forward to most at this event!',
                'activity_type': 'poll',
                'activity_data': {
                    'question': 'What excites you most about this event?',
                    'options': [
                        'Networking opportunities',
                        'Learning new skills',
                        'Meeting industry experts',
                        'Product demos',
                        'Panel discussions'
                    ]
                },
                'is_featured': True,
                'points_reward': 10,
            },
            {
                'title': '🧠 Tech Knowledge Quiz',
                'description': 'Test your tech knowledge with this quick quiz!',
                'activity_type': 'quiz',
                'activity_data': {
                    'question': 'What does API stand for?',
                    'options': [
                        'Application Programming Interface',
                        'Advanced Program Integration',
                        'Automated Process Interaction',
                        'Application Process Interface'
                    ],
                    'correct_answer': 'Application Programming Interface'
                },
                'is_featured': False,
                'points_reward': 15,
            },
            {
                'title': '👋 Introduce Yourself!',
                'description': 'Share a bit about yourself with other attendees. Tell us your name, role, and what you hope to learn!',
                'activity_type': 'introduction',
                'activity_data': {},
                'is_featured': True,
                'points_reward': 5,
                'anonymous_responses': False,
            },
            {
                'title': '🎯 Networking Goal Challenge',
                'description': 'What is your main networking goal for this event?',
                'activity_type': 'question',
                'activity_data': {
                    'prompt': 'Share your networking goal in one sentence'
                },
                'is_featured': False,
                'points_reward': 8,
            },
            {
                'title': '🔮 Prediction Poll: Future of Tech',
                'description': 'What do you think will be the biggest tech trend next year?',
                'activity_type': 'poll',
                'activity_data': {
                    'question': 'What will be the biggest tech trend next year?',
                    'options': [
                        'Artificial Intelligence',
                        'Quantum Computing',
                        'Sustainable Technology',
                        'Virtual Reality',
                        'Blockchain & Web3'
                    ]
                },
                'is_featured': False,
                'points_reward': 12,
            }
        ]

        created_count = 0
        for activity_data in activities:
            # Check if activity with this title already exists
            if IcebreakerActivity.objects.filter(
                title=activity_data['title'],
                event=event
            ).exists():
                print(f"⚠️  Activity '{activity_data['title']}' already exists, skipping...")
                continue

            # Create the activity
            activity = IcebreakerActivity.objects.create(
                event=event,
                creator=user,
                title=activity_data['title'],
                description=activity_data['description'],
                activity_type=activity_data['activity_type'],
                activity_data=activity_data['activity_data'],
                is_featured=activity_data['is_featured'],
                points_reward=activity_data['points_reward'],
                is_active=True,
                anonymous_responses=activity_data.get('anonymous_responses', False),
                allow_multiple_responses=False,
            )

            created_count += 1
            print(f"✅ Created: {activity.title}")

        print(f"\n🎉 Successfully created {created_count} icebreaker activities!")
        print(f"🌐 You can now view them at: http://localhost:5173/ → Communication Hub → Icebreakers")
        print(f"⚙️  Or manage them at: http://localhost:8000/admin/communication/icebreakeractivity/")

    except Exception as e:
        print(f"❌ Error creating activities: {e}")

if __name__ == '__main__':
    create_sample_activities()