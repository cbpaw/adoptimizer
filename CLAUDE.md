# Codebase Guidelines

## Architecture

- This is a Django project built on Python 3.12.
- User authentication uses `django-allauth`.
- The front end is mostly standard Django views and templates.
- The front end also uses React for dynamic user interfaces and interactions.
- React components are built using TypeScript and communicate with Django via a REST API.
- JavaScript files are kept in the `/assets/` folder and built by vite.
  JavaScript code is typically loaded via the static files framework inside Django templates using `django-vite`.
- APIs use Django Rest Framework, and JavaScript code that interacts with APIs uses an
  auto-generated OpenAPI-schema-baesd client.
- The front end uses Tailwind (Version 4) and DaisyUI.
- The main database is Postgres.
- Celery is used for background jobs and scheduled tasks.
- Redis is used as the default cache, and the message broker for Celery (if enabled).

## Commands you can run

The following commands can be used for various tools and workflows:
- Build front-end: `make npm-build` (production) or `make npm-dev` (development)
- Type checking: `make npm-type-check`
- Run server: `make start` or `make start-bg` (background)
- Run all tests: `make test`
- Run specific test: `make test ARGS='apps.module.tests.test_file'`
- Lint Python: `make ruff-lint`
- Format Python: `make ruff-format`
- Update translations: `make translations`
- Generate API docs: `make manage ARGS='generate_openapi --output=static/openapi.yaml'`

Additional useful commands:
- Start all services: `make start`
- Stop all services: `make stop`
- SSH into web container: `make ssh`
- Django shell: `make shell`
- Database shell: `make dbshell`
- Run Django management commands: `make manage ARGS='command'`

## General Coding Preferences

- Always prefer simple solutions.
- Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already have similar code and functionality.
- You are careful to only make changes that are requested or you are confident are well understood and related to the change being requested.
- When fixing an issue or bug, do not introduce a new pattern or technology without first exhausting all options for the existing implementation. And if you finally do this, make sure to remove the old implementation afterwards so we don’t have duplicate logic.
- Keep the codebase clean and organized.
- Avoid writing scripts in files if possible, especially if the script is likely only to be run once.
- Try to avoid having files over 200-300 lines of code. Refactor at that point.
- Don't ever add mock data to functions. Only add mocks to tests or utilities that are only used by tests.
- Always think about what other areas of code might be affected by any changes made.
- Never overwrite my .env file without first asking and confirming.

## Python Code Guidelines

### Code Style

- Follow PEP 8 with 120 character line limit.
- Use double quotes for Python strings (ruff enforced).
- Sort imports with isort (via ruff).
- Try to use type hints where possible, but strict type-checking is not enforced and you can leave them out if it's burdensome. There is no need to add type hints to existing code that does not use them.

### Preferred Practices

- Use Django signals sparingly and document them well.
- Always use the Django ORM if possible. Use best practices like lazily evaluating querysets
  and selecting or prefetching related objects when necessary.
- Use function-based views by default, unless using a framework that relies on class-based views (e.g. Django Rest Framework).
- Always validate user input server-side.
- Handle errors explicitly, avoid silent failures.
- Use translation markup, usually `gettext_lazy` whenever using user-facing strings.

#### Django models

- All Django models should extend `apps.utils.models.BaseModel` (which adds `created_at` and `updated_at` fields).
- The project's user model is `apps.users.models.CustomUser` and should be imported directly.

## Django Template Coding Guidelines for HTML files

- Indent templates with two spaces.
- Use standard Django template syntax.
- Use translation markup, usually `translate` or `blocktranslate trimmed` with user-facing text.
  Don't forget to `{% load i18n %}` if needed.
- JavaScript and CSS files built with vite should be included with the `{% vite_asset %}` template tag provided by `django-vite` (must have `{% load django_vite %}` at the top of the template)
- Any react components also need `{% vite_react_refresh %}` for Vite + React's HMR functionality, from the same `django_vite` template library)
- Use the Django `{% static %}` tag for loading images and external JavaScript / CSS files not managed by vite.
- Break re-usable template components into separate templates with `{% include %}` statements.
  These normally go into a `components` folder.
- Use DaisyUI styling markup for available components. When not available, fall back to standard TailwindCSS classes.
- Stick with the DaisyUI color palette whenever possible.

## JavaScript Code Guidelines

### Code Style

- Use ES6+ syntax for JavaScript code.
- Use 2 spaces for indentation in JavaScript, JSX, and HTML files.
- Use single quotes for JavaScript strings.
- End statements with semicolons.
- Use camelCase for variable and function names.
- Use PascalCase for component names (React).
- For React components, use functional components with hooks rather than class components.
- Use explicit type annotations in TypeScript files.
- Use ES6 import/export syntax for module management.

### Preferred Practices
- React components should be kept small and focused on a single responsibility.
- Store state at an appropriate level; avoid prop drilling by using context when necessary.
- Where possible, use TypeScript for React components to leverage type safety.
- Use the generated OpenAPI client for API calls instead of raw fetch or axios calls.
- Validate user input on both client and server side.
- Handle errors explicitly in promise chains and async functions.

### Build System

- Code is bundled using vite and served with `django-vite`.
