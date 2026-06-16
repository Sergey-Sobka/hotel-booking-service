# Hotel Booking Service

Team-ready Django foundation for the assignment described in the
[project documentation](https://docs.google.com/document/d/1dug9m85_Ck0J3Lno9P_2m0y4aAGLmnQy/edit).

The repository contains empty Django applications, Docker infrastructure, and
CI checks. Models, migrations, business logic, API endpoints, background jobs,
Stripe, and Telegram integrations remain separate feature tasks.

- [Trello board](https://trello.com/b/1C5FZifF/hotel-booking-service)
- [Sprint plan](docs/SPRINT_PLAN.md)

## Requirements

- Python 3.12+
- Django 5.2
- Docker with Docker Compose

## Setup

```bash
git clone https://github.com/Sergey-Sobka/hotel-booking-service.git
cd hotel-booking-service

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Docker setup

Start Django, PostgreSQL, and Redis together:

```bash
cp .env.sample .env
docker compose up --build
```

The `web` service waits for healthy dependencies, applies migrations, and
starts Django at `http://127.0.0.1:8000/`.

```bash
docker compose down
docker compose down -v  # also removes local database and Redis data
```

## Project structure

- `config` - Django configuration.
- `users` - user service application scaffold.
- `rooms` - room service application scaffold.
- `bookings` - booking service application scaffold.
- `payments` - payment service application scaffold.

Models, migrations, serializers, views, permissions, filters, lifecycle
actions, and integrations belong in their corresponding Trello cards.

## Quality checks

```bash
python manage.py makemigrations --check --dry-run
python manage.py test
```

GitHub Actions installs Flake8 separately and runs linting, Django configuration,
migration, and test checks for pushes and pull requests targeting `main` or
`develop`.

## Joining the repository

The repository is public, so anyone can view and clone it. The owner must still
invite each developer in `Settings -> Collaborators -> Add people` using their
GitHub username so they can push branches.

After accepting the invitation, each developer runs:

```bash
git clone https://github.com/Sergey-Sobka/hotel-booking-service.git
cd hotel-booking-service
git switch develop
git pull origin develop
```

## Team workflow

1. Choose an assigned card from `To Do` and move it to `In Progress`.
2. Pull the latest `develop`.
3. Create a branch named `feature/HBS-<card-number>-short-name` from `develop`.
4. Implement only the assigned Trello card.
5. Open a pull request into `develop` and attach its link to the Trello card.
6. Move the card to `On Review`.
7. Receive approvals from two teammates and resolve all comments.
8. Merge the pull request into `develop`, then move the card to `Done`.

At the end of the sprint, open one release pull request from `develop` into
`main`. Do not push feature work directly to `main` or `develop`. Do not use
forks; all developers work in the same shared repository.

The Trello card ID must also appear in the branch name, commit messages, and
pull request title.

## Telegram notifications setup

The project uses Telegram Bot API to send staff/admin notifications.

### Environment variables

Add these variables to `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_API_URL=https://api.telegram.org


