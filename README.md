# QR Code Check-in System

An automated check-in system that scans QR codes from invitations and marks guests as attending. The system can create invitations with QR codes and works in environments with limited internet connectivity.

## Features

- Create and manage events
- Generate invitations with unique QR codes
- Scan QR codes for check-in
- Mark attendance status
- Offline capability for limited connectivity environments
- Guest management

## Tech Stack

- **Frontend**: React with TypeScript
- **Backend**: Django REST Framework
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose
- **QR Code**: html5-qrcode

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

### Running with Docker

```bash
# Clone the repository
git clone <repository-url>
cd qr-checkin-system

# Start the application
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
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