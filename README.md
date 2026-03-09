# viernulvier-2

## Rolverdeling

| Rol           | Naam     |
|---------------|----------|
| Leader        | Tobit    |
| Tech Lead     | Elias    |
| SysAdmin      | Jasper   |
| Communicatie  | Arne     |
| Test          | Florian  |
| DB            | Daan     |
| Frontend      | Noah     |
| Backend       | Prince   |

## Backend

### Important things to change

- TODOS
- Test folder nice structure

### Packages

- django
- djangorestframework
- pytest
- pytest-django

### Belangrijke commands:

- make an app (i.e. genres): ```python manage.py startapp genres apps/genres```
- start de dev server: ```python manage.py runserver```
- migrations aanmaken voor X: ```python manage.py makemigrations X```
    -- bv. ```python manage.py makemigrations languages```
- migrate: ```python manage.py migrate```

## Frontend

See wiki pages

## Dependency Management

Dependencies are automatically monitored and updated using **Dependabot**. Updates run weekly on Mondays and are automatically approved and merged based on version type (patch/minor auto-merge, major requires manual review).

For information on how Dependabot is configured, what gets updated, and the auto-merge workflow, see [`DEPENDABOT`](.github/DEPENDABOT.md).

## Adding a Pull Request

When creating a PR, please follow these guidelines:

1. **Use the PR Template:**
   - The PR template will automatically show when you create a new pull request. Ensure that all relevant sections are filled out.

2. **Key Sections to Include:**
   - **Description:** Provide a brief description of the changes and their purpose.
   - **Related Issues:** Link any issues that this PR addresses.
   - **Type of Change:** Select the appropriate category.
   - **Testing Instructions:** Describe which tests and environments need to be ran.
   - **Checklist for Reviewers:** Confirm that all required tasks are complete before submission.

Thanks! ^^

## Frontend

See wiki pages
---
