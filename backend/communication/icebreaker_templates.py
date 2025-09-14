"""
Icebreaker Template Packs for Automated Generation
"""
from datetime import timedelta
import random

# Template packs for different event types
CORPORATE_PACK = [
    {
        'title': '🏢 Company Culture Match',
        'description': 'Discover what work environment energizes our team most!',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'What work environment energizes you most?',
            'options': [
                'Collaborative team spaces',
                'Quiet focus zones',
                'Flexible remote setup',
                'Dynamic open office',
                'Hybrid mix of all'
            ]
        },
        'points_reward': 10,
        'is_featured': True,
        'schedule_days_before': 14
    },
    {
        'title': '💡 Innovation Challenge',
        'description': 'Share your creative ideas that could transform our industry',
        'activity_type': 'question',
        'activity_data': {
            'prompt': 'Share one unconventional idea that could improve our industry in the next year'
        },
        'points_reward': 15,
        'is_featured': False,
        'schedule_days_before': 10
    },
    {
        'title': '🎯 Career Journey',
        'description': 'Connect through sharing your unique professional path',
        'activity_type': 'introduction',
        'activity_data': {
            'prompt': 'What unexpected path led you to your current role? Share your story!'
        },
        'points_reward': 20,
        'is_featured': True,
        'schedule_days_before': 7
    },
    {
        'title': '🧠 Industry Knowledge Quiz',
        'description': 'Test your knowledge about our industry trends',
        'activity_type': 'quiz',
        'activity_data': {
            'question': 'What percentage of companies have adopted AI in their operations?',
            'options': ['Less than 25%', '35-45%', '50-60%', 'Over 70%'],
            'correct_answer': '35-45%'
        },
        'points_reward': 25,
        'is_featured': False,
        'schedule_days_before': 3
    }
]

SOCIAL_EVENTS_PACK = [
    {
        'title': '🎉 Party Personality',
        'description': 'Find your party twin by discovering everyone\'s social style!',
        'activity_type': 'quiz',
        'activity_data': {
            'question': 'What\'s your go-to party move?',
            'options': [
                '🕺 Dance floor commander',
                '💬 Deep conversation corner',
                '🎮 Game organizer',
                '🍕 Food station explorer',
                '📸 Photo booth enthusiast'
            ],
            'correct_answer': '🕺 Dance floor commander'  # For fun, any answer is "correct"
        },
        'points_reward': 10,
        'is_featured': True,
        'schedule_days_before': 7
    },
    {
        'title': '🌟 Hidden Talent Reveal',
        'description': 'Surprise everyone with your secret superpower!',
        'activity_type': 'challenge',
        'activity_data': {
            'prompt': 'Share a hidden talent nobody would guess you have! (The more surprising, the better!)'
        },
        'points_reward': 15,
        'is_featured': False,
        'schedule_days_before': 5
    },
    {
        'title': '🎭 Two Truths & a Lie',
        'description': 'Can others spot your lie? Share and let them guess!',
        'activity_type': 'question',
        'activity_data': {
            'prompt': 'Share two truths and one lie about yourself. Make it challenging!'
        },
        'points_reward': 20,
        'is_featured': True,
        'schedule_days_before': 3
    }
]

CONFERENCE_PACK = [
    {
        'title': '🚀 Tech Predictions 2025',
        'description': 'Vote on the technology that will transform our field',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'Which technology will have the biggest impact in 2025?',
            'options': [
                '🤖 AI/Machine Learning',
                '⚛️ Quantum Computing',
                '🔗 Blockchain/Web3',
                '🥽 AR/VR/Metaverse',
                '🧬 Biotech/Health Tech',
                '🌱 Green/Climate Tech'
            ]
        },
        'points_reward': 10,
        'is_featured': True,
        'schedule_days_before': 14
    },
    {
        'title': '💬 Session Wishlist',
        'description': 'What topics do you want to explore at the conference?',
        'activity_type': 'question',
        'activity_data': {
            'prompt': 'What\'s one topic you\'re hoping to learn more about at this conference?'
        },
        'points_reward': 12,
        'is_featured': False,
        'schedule_days_before': 10
    },
    {
        'title': '🏆 Conference Goals',
        'description': 'Share your main objective for attending',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'What\'s your primary goal for this conference?',
            'options': [
                '📚 Learn new skills',
                '🤝 Network with peers',
                '💼 Find new opportunities',
                '🎯 Discover industry trends',
                '🚀 Get inspired',
                '🛠️ Find solutions to challenges'
            ]
        },
        'points_reward': 15,
        'is_featured': False,
        'schedule_days_before': 7
    },
    {
        'title': '🌍 Where in the World?',
        'description': 'Let\'s see how global our audience is!',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'Where are you joining us from?',
            'options': [
                '🌎 Americas',
                '🌍 Europe/Africa',
                '🌏 Asia/Pacific',
                '🏠 Local (same city)',
                '✈️ Traveling specifically for this'
            ]
        },
        'points_reward': 8,
        'is_featured': False,
        'schedule_days_before': 3
    }
]

NETWORKING_PACK = [
    {
        'title': '🔗 Collaboration Interests',
        'description': 'Find potential collaborators by sharing your interests',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'What type of collaboration excites you most?',
            'options': [
                '🚀 Startup ventures',
                '📚 Research projects',
                '🎨 Creative partnerships',
                '💻 Open source contributions',
                '📝 Content creation',
                '🌍 Social impact initiatives'
            ]
        },
        'points_reward': 12,
        'is_featured': True,
        'schedule_days_before': 10
    },
    {
        'title': '☕ Coffee Chat Topics',
        'description': 'What would you love to discuss over coffee?',
        'activity_type': 'question',
        'activity_data': {
            'prompt': 'If we had 15 minutes for coffee, what topic would you want to discuss?'
        },
        'points_reward': 10,
        'is_featured': False,
        'schedule_days_before': 7
    },
    {
        'title': '🎯 Expertise Exchange',
        'description': 'Share what you can teach and what you want to learn',
        'activity_type': 'introduction',
        'activity_data': {
            'prompt': 'One skill I can teach: ___ | One skill I want to learn: ___'
        },
        'points_reward': 20,
        'is_featured': True,
        'schedule_days_before': 5
    }
]

TEAM_BUILDING_PACK = [
    {
        'title': '🦸 Team Superpowers',
        'description': 'What superpower would help your team most?',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'If your team could have one superpower, what would it be?',
            'options': [
                '🧠 Mind reading (perfect communication)',
                '⏰ Time control (never miss deadlines)',
                '🔮 Future sight (perfect planning)',
                '♾️ Cloning (unlimited resources)',
                '⚡ Super speed (instant delivery)'
            ]
        },
        'points_reward': 10,
        'is_featured': True,
        'schedule_days_before': 7
    },
    {
        'title': '🏝️ Desert Island Challenge',
        'description': 'What would you bring to help the team survive?',
        'activity_type': 'question',
        'activity_data': {
            'prompt': 'Your team is stranded on a desert island. What one item would you contribute and why?'
        },
        'points_reward': 15,
        'is_featured': False,
        'schedule_days_before': 5
    },
    {
        'title': '🎮 Team Building Activity Vote',
        'description': 'Choose our next team building activity!',
        'activity_type': 'poll',
        'activity_data': {
            'question': 'What team building activity sounds most fun?',
            'options': [
                '🎯 Escape room challenge',
                '🍳 Cooking class together',
                '🎮 Gaming tournament',
                '🏃 Outdoor adventure',
                '🎨 Creative workshop',
                '🍷 Wine/coffee tasting'
            ]
        },
        'points_reward': 12,
        'is_featured': False,
        'schedule_days_before': 3
    }
]

# Fun seasonal/holiday additions
SEASONAL_MODIFIERS = {
    'winter': [
        {
            'title': '❄️ Winter Favorites',
            'activity_type': 'poll',
            'activity_data': {
                'question': 'What\'s your favorite winter activity?',
                'options': ['⛷️ Skiing/Snowboarding', '☕ Cozy indoor reading', '⛸️ Ice skating', '🔥 Fireplace gatherings', '🎿 Winter hiking']
            }
        }
    ],
    'summer': [
        {
            'title': '☀️ Summer Vibes',
            'activity_type': 'poll',
            'activity_data': {
                'question': 'Perfect summer day activity?',
                'options': ['🏖️ Beach day', '🏔️ Mountain hiking', '🍔 BBQ party', '🏊 Pool/lake swimming', '🎪 Outdoor festival']
            }
        }
    ],
    'holiday': [
        {
            'title': '🎁 Holiday Traditions',
            'activity_type': 'question',
            'activity_data': {
                'prompt': 'Share your favorite or most unique holiday tradition!'
            }
        }
    ]
}

def get_template_pack(event_type):
    """Get the appropriate template pack based on event type"""
    packs = {
        'corporate': CORPORATE_PACK,
        'social': SOCIAL_EVENTS_PACK,
        'conference': CONFERENCE_PACK,
        'networking': NETWORKING_PACK,
        'team_building': TEAM_BUILDING_PACK
    }
    return packs.get(event_type, CONFERENCE_PACK)  # Default to conference

def get_smart_pack(event):
    """Generate a smart pack based on event context"""
    import datetime

    # Determine event type from name or description
    event_name_lower = event.name.lower()
    event_desc_lower = (event.description or '').lower()

    # Detect event type
    if any(word in event_name_lower + event_desc_lower for word in ['conference', 'summit', 'symposium', 'expo']):
        base_pack = CONFERENCE_PACK
    elif any(word in event_name_lower + event_desc_lower for word in ['party', 'celebration', 'social', 'mixer']):
        base_pack = SOCIAL_EVENTS_PACK
    elif any(word in event_name_lower + event_desc_lower for word in ['corporate', 'business', 'company', 'annual']):
        base_pack = CORPORATE_PACK
    elif any(word in event_name_lower + event_desc_lower for word in ['network', 'meetup', 'connect']):
        base_pack = NETWORKING_PACK
    elif any(word in event_name_lower + event_desc_lower for word in ['team', 'staff', 'employee']):
        base_pack = TEAM_BUILDING_PACK
    else:
        # Mix and match from different packs
        base_pack = [
            random.choice(CONFERENCE_PACK),
            random.choice(NETWORKING_PACK),
            random.choice(SOCIAL_EVENTS_PACK),
            random.choice(CORPORATE_PACK)
        ]

    # Add seasonal elements if applicable
    current_month = datetime.datetime.now().month
    if current_month in [12, 1, 2]:  # Winter
        if random.random() > 0.5:  # 50% chance to add seasonal
            base_pack = base_pack[:3] + SEASONAL_MODIFIERS['winter'][:1] + base_pack[3:]
    elif current_month in [6, 7, 8]:  # Summer
        if random.random() > 0.5:
            base_pack = base_pack[:3] + SEASONAL_MODIFIERS['summer'][:1] + base_pack[3:]
    elif current_month == 12:  # December - holidays
        if random.random() > 0.7:  # 30% chance
            base_pack = base_pack[:2] + SEASONAL_MODIFIERS['holiday'][:1] + base_pack[2:]

    # Limit to 4-5 activities
    return base_pack[:5] if len(base_pack) > 5 else base_pack

def calculate_schedule_dates(event_date, activities):
    """Calculate when each activity should be sent based on event date"""
    scheduled_activities = []
    for activity in activities:
        days_before = activity.get('schedule_days_before', 7)
        schedule_date = event_date - timedelta(days=days_before)
        activity['starts_at'] = schedule_date
        scheduled_activities.append(activity)

    # Sort by schedule date (earliest first)
    return sorted(scheduled_activities, key=lambda x: x['starts_at'])