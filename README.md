# viernulvier-2

Web application project with a Django backend and a React + Vite frontend.

## Wiki

Project documentation is available in the GitHub Wiki:

- [GitHub Wiki](https://github.com/SELab-2/viernulvier-2/wiki)

## Team Roles

| Role                       | Name    |
| -------------------------- | ------- |
| Group Leader               | Tobit   |
| Technical Lead             | Elias   |
| SysAdmin                   | Jasper  |
| Customer Relations Officer | Arne    |
| Test Manager               | Florian |
| Database Manager           | Daan    |
| Frontend Manager           | Noah    |
| Backend Manager            | Prince  |

## Project Structure

- `backend/`: Django API, models, serializers, tests
- `frontend/`: React/Vite frontend in TypeScript
- `infrastructure/`: Docker Compose and Nginx configuration

## Quick Start

### Backend (Django)

Go to the backend folder:

```bash
cd backend
```

Common commands:

- Create app: `python manage.py startapp <app_name> apps/<app_name>`
- Dev server: `python manage.py runserver`
- Create migrations: `python manage.py makemigrations <app_name>`
- Apply migrations: `python manage.py migrate`

### Frontend (React + Vite)

Go to the frontend folder:

```bash
cd frontend
```

Common commands:

- Install dependencies: `npm install`
- Start dev server: `npm run dev`
- Run tests: `npm test`
- Build for production: `npm run build`

## Dependencies

Dependencies are automatically monitored with Dependabot.

More information about configuration and auto-merge flow:

- [Dependabot documentation](.github/DEPENDABOT.md)

## Pull Requests

Use the PR template for every pull request and include at least:

1. Description of the change
2. Linked issue(s)
3. Type of change
4. Testing instructions
5. Reviewer checklist

## Additional Documentation

- [GitHub Wiki](https://github.com/SELab-2/viernulvier-2/wiki)
