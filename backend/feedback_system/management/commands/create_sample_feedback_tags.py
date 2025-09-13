from django.core.management.base import BaseCommand
from feedback_system.models import FeedbackTag


class Command(BaseCommand):
    help = 'Create sample feedback tags'
    
    def handle(self, *args, **options):
        sample_tags = [
            # Content Tags
            ('Great Content', 'content', 'STAR', 'High-quality presentations and topics', True),
            ('Engaging Speakers', 'content', 'MIC', 'Excellent speakers and presentations', True),
            ('Relevant Topics', 'content', 'TARGET', 'Content relevant to audience interests', True),
            ('Poor Content', 'content', 'DOWN', 'Content needs improvement', False),
            ('Boring Presentations', 'content', 'SLEEP', 'Presentations lacked engagement', False),
            
            # Venue Tags
            ('Perfect Venue', 'venue', 'BUILDING', 'Excellent venue choice and setup', True),
            ('Good Location', 'venue', 'PIN', 'Convenient and accessible location', True),
            ('Poor Acoustics', 'venue', 'MUTE', 'Audio quality issues in venue', False),
            ('Uncomfortable Seating', 'venue', 'SEAT', 'Seating was uncomfortable', False),
            ('Hard to Find', 'venue', 'MAP', 'Venue was difficult to locate', False),
            
            # Organization Tags
            ('Well Organized', 'organization', 'STAR', 'Event was excellently organized', True),
            ('Smooth Check-in', 'organization', 'CHECK', 'Registration process was efficient', True),
            ('Great Communication', 'organization', 'SPEAKER', 'Clear communication before and during event', True),
            ('Poor Planning', 'organization', 'BOARD', 'Event organization needs improvement', False),
            ('Confusing Schedule', 'organization', 'CLOCK', 'Schedule was unclear or poorly communicated', False),
            
            # Technical Tags
            ('Great Tech Setup', 'technical', 'LAPTOP', 'Excellent technical infrastructure', True),
            ('Good WiFi', 'technical', 'WIFI', 'Reliable internet connectivity', True),
            ('Tech Issues', 'technical', 'WARNING', 'Technical problems during event', False),
            ('Poor AV Quality', 'technical', 'PROJECTOR', 'Audio/visual equipment had issues', False),
            
            # Catering Tags
            ('Delicious Food', 'catering', 'PLATE', 'Great food and beverages', True),
            ('Good Variety', 'catering', 'SALAD', 'Nice variety of food options', True),
            ('Poor Food Quality', 'catering', 'BURGER', 'Food quality was disappointing', False),
            ('Limited Options', 'catering', 'SANDWICH', 'Not enough food variety', False),
            
            # Networking Tags
            ('Great Networking', 'networking', 'HANDSHAKE', 'Excellent networking opportunities', True),
            ('Met New People', 'networking', 'PEOPLE', 'Connected with interesting people', True),
            ('Limited Networking', 'networking', 'BLOCK', 'Few networking opportunities', False),
            
            # General Tags
            ('Exceeded Expectations', 'general', 'STAR', 'Event was better than expected', True),
            ('Good Value', 'general', 'MONEY', 'Great value for money', True),
            ('Would Recommend', 'general', 'THUMBS_UP', 'Would recommend to others', True),
            ('Disappointing', 'general', 'THUMBS_DOWN', 'Event did not meet expectations', False),
            ('Too Expensive', 'general', 'MONEY_FLY', 'Not good value for the price', False),
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