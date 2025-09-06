from django.core.management.base import BaseCommand
from feedback_system.models import FeedbackTag


class Command(BaseCommand):
    help = 'Create sample feedback tags'
    
    def handle(self, *args, **options):
        sample_tags = [
            # Content Tags
            ('Great Content', 'content', '✨', 'High-quality presentations and topics', True),
            ('Engaging Speakers', 'content', '🎤', 'Excellent speakers and presentations', True),
            ('Relevant Topics', 'content', '🎯', 'Content relevant to audience interests', True),
            ('Poor Content', 'content', '📉', 'Content needs improvement', False),
            ('Boring Presentations', 'content', '😴', 'Presentations lacked engagement', False),
            
            # Venue Tags
            ('Perfect Venue', 'venue', '🏢', 'Excellent venue choice and setup', True),
            ('Good Location', 'venue', '📍', 'Convenient and accessible location', True),
            ('Poor Acoustics', 'venue', '🔇', 'Audio quality issues in venue', False),
            ('Uncomfortable Seating', 'venue', '💺', 'Seating was uncomfortable', False),
            ('Hard to Find', 'venue', '🗺️', 'Venue was difficult to locate', False),
            
            # Organization Tags
            ('Well Organized', 'organization', '⭐', 'Event was excellently organized', True),
            ('Smooth Check-in', 'organization', '✅', 'Registration process was efficient', True),
            ('Great Communication', 'organization', '📢', 'Clear communication before and during event', True),
            ('Poor Planning', 'organization', '📋', 'Event organization needs improvement', False),
            ('Confusing Schedule', 'organization', '⏰', 'Schedule was unclear or poorly communicated', False),
            
            # Technical Tags
            ('Great Tech Setup', 'technical', '💻', 'Excellent technical infrastructure', True),
            ('Good WiFi', 'technical', '📶', 'Reliable internet connectivity', True),
            ('Tech Issues', 'technical', '⚠️', 'Technical problems during event', False),
            ('Poor AV Quality', 'technical', '📽️', 'Audio/visual equipment had issues', False),
            
            # Catering Tags
            ('Delicious Food', 'catering', '🍽️', 'Great food and beverages', True),
            ('Good Variety', 'catering', '🥗', 'Nice variety of food options', True),
            ('Poor Food Quality', 'catering', '🍔', 'Food quality was disappointing', False),
            ('Limited Options', 'catering', '🥪', 'Not enough food variety', False),
            
            # Networking Tags
            ('Great Networking', 'networking', '🤝', 'Excellent networking opportunities', True),
            ('Met New People', 'networking', '👥', 'Connected with interesting people', True),
            ('Limited Networking', 'networking', '🚫', 'Few networking opportunities', False),
            
            # General Tags
            ('Exceeded Expectations', 'general', '🌟', 'Event was better than expected', True),
            ('Good Value', 'general', '💰', 'Great value for money', True),
            ('Would Recommend', 'general', '👍', 'Would recommend to others', True),
            ('Disappointing', 'general', '👎', 'Event did not meet expectations', False),
            ('Too Expensive', 'general', '💸', 'Not good value for the price', False),
        ]
        
        created_count = 0
        for name, category, icon, description, is_positive in sample_tags:
            tag, created = FeedbackTag.objects.get_or_create(
                name=name,
                category=category,
                defaults={
                    'icon': icon,
                    'description': description,
                    'is_positive': is_positive
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created tag: {name} ({category})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tag already exists: {name} ({category})')
                )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully created {created_count} new feedback tags')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nAll sample feedback tags already exist')
            )