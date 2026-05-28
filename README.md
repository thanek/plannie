# Plannie

A Planning Poker (Scrum) estimation service with real-time updates over WebSocket.

## Requirements

- Python 3.11+
- bash (macOS / Linux)

## Quick start

```bash
# Start the service (venv and dependencies are installed automatically on first run)
./run.sh start
```

Open http://localhost:8000

## Configuration (`.env`)

Copy the example file and adjust as needed:

```bash
cp .env.example .env
```

All variables are loaded by the app via `python-dotenv`.

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Listening port |
| `HOST` | `0.0.0.0` | Listening address |
| `PUBLIC_HOST` | `localhost` | Host or full URL used to build the link and QR code |
| `PUBLIC_SCHEME` | request scheme | Optional scheme (`http`/`https`) when `PUBLIC_HOST` is a bare hostname |
| `PUBLIC_PORT` | none | Optional port when `PUBLIC_HOST` is a bare hostname |

If `PUBLIC_HOST` starts with `http://` or `https://`, the `PUBLIC_SCHEME` and `PUBLIC_PORT` variables are ignored.

Examples:

```dotenv
PORT=8888
HOST=0.0.0.0

# bare hostname with separate scheme and port
PUBLIC_HOST=planning.example.com
PUBLIC_SCHEME=https
PUBLIC_PORT=8443

# or full URL (PUBLIC_SCHEME and PUBLIC_PORT are ignored)
PUBLIC_HOST=https://planning.example.com
```

## Launcher (`run.sh`)

```
./run.sh <command>

Commands:
  start     Start the service
  test      Run tests (extra args are forwarded to pytest)
  install   Create venv and install dependencies
```

```bash
./run.sh start
./run.sh test
./run.sh test -k test_voting
./run.sh install
```

## User flow

1. Visit `/` without a cookie → redirect to the **login** page (enter your name)
2. **Home page** shows a list of active sessions and a form to create a new one
3. After creating a session the creator (**PM**) lands on the **session page** with a QR code and participant list
4. **Participants** scan the QR or open the link → if they have no cookie they go to login first, then straight into the session
5. Everyone (including the PM) sees estimation cards and can vote; the result is sent immediately on card selection
6. The PM sees in real time who has joined and who has voted (but not what value)
7. The PM clicks **"Close and reveal results"** → estimates are revealed to everyone
8. The PM can **reset the session** (new vote round on the same URL)

## Estimates

`1, 2, 3, 5, 8, 13, 21, 34, 55, 89, ☕, ?, ∞`

## Project structure

```
planing_estimator/
├── src/
│   ├── domain/
│   │   └── models.py           # Domain models: Session, Participant, Estimate
│   ├── repositories/
│   │   ├── base.py             # ABC SessionRepository
│   │   └── in_memory.py        # In-memory implementation
│   ├── services/
│   │   ├── session_service.py  # Business logic
│   │   └── name_generator.py   # Random session name generator
│   ├── api/
│   │   ├── dependencies.py     # FastAPI dependency injection
│   │   └── routes.py           # HTTP routes + WebSocket
│   └── main.py                 # FastAPI app + entry point
├── tests/
│   ├── test_session_service.py # Unit tests for the service
│   └── test_api.py             # API integration tests
├── web/
│   ├── static/style.css        # Styles (responsive)
│   └── templates/              # Jinja2 templates
│       ├── base.html
│       ├── login.html          # Login page (enter name)
│       ├── home.html           # Home page (session list + create)
│       └── session.html        # Session page (QR, participants, voting)
├── requirements.txt
├── .env.example
└── pytest.ini
```

## Swapping the storage backend

To replace the in-memory store with a database, implement `SessionRepository` (the ABC in `src/repositories/base.py`) and swap it in `src/api/dependencies.py`.
