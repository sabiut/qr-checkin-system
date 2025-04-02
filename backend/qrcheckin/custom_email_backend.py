"""
Custom console email backend with more verbose logging
"""
import sys
import threading
import logging

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend

logger = logging.getLogger(__name__)

class VerboseConsoleEmailBackend(ConsoleEmailBackend):
    """
    A wrapper around Django's console email backend that logs more details
    """
    
    def send_messages(self, email_messages):
        """Write all messages to the console, with added logging"""
        if not email_messages:
            return 0
            
        msg_count = 0
        for message in email_messages:
            logger.info(f"===== SENDING EMAIL {threading.get_ident()} =====")
            logger.info(f"From: {message.from_email}")
            logger.info(f"To: {', '.join(message.to)}")
            logger.info(f"Subject: {message.subject}")
            
            if hasattr(message, 'body') and message.body:
                logger.info(f"Body: {message.body[:100]}...")
                
            if hasattr(message, 'alternatives') and message.alternatives:
                for content, mimetype in message.alternatives:
                    if mimetype == 'text/html':
                        logger.info(f"HTML Content: {content[:100]}...")
                        
            if hasattr(message, 'attachments') and message.attachments:
                logger.info(f"Attachments: {len(message.attachments)}")
                for attachment in message.attachments:
                    if isinstance(attachment, tuple) and len(attachment) >= 2:
                        logger.info(f"  - {attachment[0]}")
                
            logger.info("=============================")
            
            # Call the parent method to write to the console
            self.write_message(message)
            msg_count += 1
            
        return msg_count
        
    def write_message(self, message):
        """Write a message to the console with a clear separator"""
        msg = message.message()
        msg_data = msg.as_string()
        sys.stdout.write('\n' + '-' * 70 + '\n')
        sys.stdout.write('EMAIL SENT:\n')
        sys.stdout.write(msg_data)
        sys.stdout.write('\n' + '-' * 70 + '\n')
        sys.stdout.flush()