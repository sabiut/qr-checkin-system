# QR Check-in System Developer Guide

## Build Commands
- Frontend development: `cd frontend && npm run dev`
- Backend development: `cd backend && python manage.py runserver`
- Docker development: `docker-compose up frontend-dev backend db`
- Production: `docker-compose up frontend backend db`
- TypeScript check: `cd frontend && npm run typecheck`
- Database migrations: `cd backend && python manage.py migrate`

## Code Style Guidelines

### React/TypeScript
- **Imports**: Group by React, third-party, local modules
- **Formatting**: 2-space indentation
- **Components**: PascalCase for components (`NavBar`), camelCase for functions (`handleSubmit`)
- **Types**: Define interfaces for props, use type annotations for hooks
- **Error handling**: Try/catch blocks for async operations, manage error states with useState

### Python/Django
- **Imports**: Django imports first, then third-party, then local
- **Formatting**: 4-space indentation (Python standard)
- **Naming**: PascalCase for classes, snake_case for methods/variables
- **Error handling**: Try/except with specific exceptions, proper HTTP status codes

### Architecture
- Frontend: React + TypeScript + React Router
- Backend: Django + Django REST Framework + PostgreSQL
- Authentication: JWT-based auth with secure HTTP-only cookies