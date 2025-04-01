# Email Setup for QR Check-in System

This document explains how to configure email sending for sending tickets to attendees.

## Local Development with Console Backend

For local development, emails are printed to the console instead of actually being sent. This is the default configuration, and you don't need to do anything special to use it.

## Setting Up Real Email Delivery

When you're ready to use a real email service, follow these steps:

### 1. Create a `.env` file

Create a `.env` file in the backend directory by copying the example:

```bash
cp backend/.env.example backend/.env
```

### 2. Edit the `.env` file

Update the email settings in your `.env` file with your actual email provider details:

```
# Email Settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 3. Email Provider-Specific Instructions

#### Gmail

If you're using Gmail, you'll need to:

1. Set up 2-Step Verification on your Google account
2. Generate an App Password (NOT your regular password)
3. Use that App Password in your `.env` file

Visit: https://myaccount.google.com/apppasswords to create an App Password.

#### Other Providers

For other email providers, you'll need to adjust the EMAIL_HOST, EMAIL_PORT, and other settings accordingly:

- **SendGrid**: 
  - EMAIL_HOST=smtp.sendgrid.net
  - EMAIL_PORT=587
  
- **Mailgun**:
  - EMAIL_HOST=smtp.mailgun.org
  - EMAIL_PORT=587

- **Amazon SES**:
  - EMAIL_HOST=email-smtp.us-east-1.amazonaws.com (region may vary)
  - EMAIL_PORT=587

### 4. Update Docker Compose (if using Docker)

When using Docker, you'll need to uncomment and update the email settings in docker-compose.yml or make sure it reads from your .env file:

```yaml
environment:
  # Email Settings
  - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  - EMAIL_HOST=smtp.gmail.com
  - EMAIL_PORT=587
  - EMAIL_USE_TLS=True
  - EMAIL_HOST_USER=your-email@gmail.com
  - EMAIL_HOST_PASSWORD=your-app-password
  - DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 5. Test Email Delivery

Use the test endpoint to verify that emails are being sent correctly:

```
POST http://localhost:8000/api/invitations/debug/test-email/<invitation_id>/
```

With request body:
```json
{
  "email": "your-test-email@example.com"
}
```

### Security Considerations

- Never commit your `.env` file or real email credentials to version control
- Consider using a dedicated email account for your application
- Regularly rotate email passwords/app passwords
- For production, consider using environment variables directly on your hosting platform