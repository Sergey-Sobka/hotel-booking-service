# Hotel Booking Service

Empty Django project for the team assignment described in the
[project documentation](https://docs.google.com/document/d/1dug9m85_Ck0J3Lno9P_2m0y4aAGLmnQy/edit).

The initial project intentionally contains no applications, models, business
logic, API endpoints, Docker configuration, or integrations. Each feature must
be implemented in a separate branch and pull request.

- [Trello board](https://trello.com/b/1C5FZifF/hotel-booking-service)
- [Sprint plan](docs/SPRINT_PLAN.md)

## Requirements

- Python 3.12+
- Django 5.2

## Setup

```bash
git clone <repository-url>
cd hotel-booking-service

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

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
