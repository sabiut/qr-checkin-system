# QR Code Check-in System

An automated check-in system that scans QR codes from invitations and marks guests as attending. The system can create invitations with QR codes and works in environments with limited internet connectivity.

## Live Demo

**Demo URL**: [https://eventqr.app/](https://eventqr.app/)

*Note: The demo may be a bit slow to load initially as it's hosted on a shared server.*

**Latest Updates**: Contact page with professional form validation and virtual event support (Zoom/Teams/Meet). Docker Hub credentials fixed - deployment should work now!

## Features

- Create and manage events
- Generate invitations with unique QR codes
- Generate personalized digital tickets with embedded QR codes
- Email delivery of tickets to attendees
- Scan QR codes for check-in
- Mark attendance status
- Offline capability for limited connectivity environments
- Guest management

## Ticket System

The system now generates personalized digital tickets for each invitation:

- **HTML Tickets**: Mobile-optimized for browser viewing
- **PDF Tickets**: For offline storage and printing
- **Email Delivery**: Tickets are sent directly to guests via email
- **Online Access**: Tickets can be viewed online via a direct URL

## Tech Stack

- **Frontend**: React with TypeScript
- **Backend**: Django REST Framework
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose
- **QR Code**: html5-qrcode
- **PDF Generation**: WeasyPrint

## Project Structure

```
qr-checkin-system/
├── frontend/             # React frontend app
│   ├── ...
├── backend/              # Django backend api
│   ├── ...
├── docker-compose.yml    # Docker compose configuration
├── .env                  # Environment variables
├── README.md             # Documentation
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js and npm (for local development)
- Python (for local development)

### Email Configuration

The system can be configured to send tickets via email:

1. Create a `.env` file in the backend directory based on `.env.example`
2. Configure the email settings:

```
# For development (logs emails to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# For production with Gmail
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

For Gmail, you need to use an App Password if 2FA is enabled.
Generate one at: https://myaccount.google.com/apppasswords

### Running with Docker

```bash
# Clone the repository
git clone <repository-url>
cd qr-checkin-system

# Start the development application
docker-compose up -d

# Access the application (Development)
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Production Deployment

```bash
# Start the production application
docker-compose -f docker-compose.prod.yml up -d

# Access the application (Production)
# Frontend: http://localhost:3000 (or via nginx on port 80/443)
# Backend API: http://localhost:8000
```

### Local Development

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Offline Capabilities

The system is designed to work with limited internet connectivity:

- Frontend uses service workers for offline capabilities
- Backend can operate in offline mode, syncing when connectivity is restored
- Local storage for temporary data storage
- Tickets can be downloaded and stored locally.
# Pipeline test - fix container permissions
# Test production deployment fix

