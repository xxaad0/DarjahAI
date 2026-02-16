```md
# DarjahAI — Gamified Task Manager + Analytics + AI Assistant (Flask)

DarjahAI is a Flask web app that combines **task + subtask management**, **productivity analytics**, and an integrated **LLM assistant**, wrapped in a **gamified leveling system** (XP, levels, streaks, classes).

This is an actively evolving personal system project built by me.

It started with sagyoai and now has developed into phase 2.

---

## What DarjahAI includes

### Core productivity features
- **Tasks + Subtasks**
  - Create / update / delete tasks
  - Create / update / delete subtasks under a selected task
  - Status + priority + category + due date + reminder fields
- **Dashboard experience**
  - Auth-protected dashboard
  - Subtask panel filtered by selected task

### Gamification layer
- **XP + leveling** when completing tasks
- **Character class progression** based on level
- **Daily streak tracking** and active-day totals

### Analytics
- **Stats page** showing:
  - latest “top terms” / scores from the task-analysis pipeline
  - historical analysis runs

### AI assistant (DarjahAI Chat)
- **Chat sessions + message history**
- **Usage limits** (free daily quota vs premium monthly quota)
- Chat endpoint API (`/chat/api`) used by the UI

### Accounts + security
- Register / login / logout
- **Email verification**
- **Forgot password / reset password**
- Account deletion flow that cleans up related user data

### Billing (Stripe)
- Subscription checkout flow for premium plan
- Stripe webhook to activate/deactivate premium access

---

## Tech stack

- **Backend:** Python, Flask, Jinja2
- **Auth & security:** Flask-Login, Flask-Bcrypt
- **Database:** Flask-SQLAlchemy + Flask-Migrate (Postgres via Docker Compose; SQLite fallback supported)
- **Mail:** flask-mailman (SMTP)
- **AI:** OpenAI SDK (model calls configured in app)
- **Data/ML utilities:** pandas, numpy, scikit-learn, NLTK
- **Billing:** Stripe
- **Deployment:** Gunicorn + Docker + Render

---

## Repository layout (high level)

```

DarjahAI/
├─ run.py
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ migrations/
└─ darjahai/
├─ **init**.py            # app factory + request hooks (streak tracking)
├─ config.py              # env-driven configuration
├─ extensions.py          # db/bcrypt/login/mail singletons
├─ models.py              # SQLAlchemy models (User, Character, Tasks, etc.)
├─ analysis.py            # task analysis pipeline (terms/scores/history)
├─ levelup.py             # XP + level logic
├─ chat.py                # AI assistant + quota logic
├─ auth/
│  └─ routes.py           # auth routes + account settings
└─ main/
└─ routes.py           # dashboard/tasks/subtasks/stats/chat/billing routes

```

---

## Configuration (environment variables)

DarjahAI is configured via environment variables:

---

## Author

**Saad Shahid**  
* Email: `dev@saadshahid.net`
* GitHub: `xxaad0`
* LinkedIn: `saad-shahid-560622217`
```
