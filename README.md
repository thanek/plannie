# Plannie

Serwis do estymowania zadań w stylu Planning Poker (Scrum), z real-time aktualizacjami przez WebSocket.

## Wymagania

- Python 3.11+
- bash (macOS / Linux)

## Szybki start

```bash
# Uruchom serwis (venv i zależności zostaną zainstalowane automatycznie przy pierwszym uruchomieniu)
./run.sh start
```

Otwórz http://localhost:8000

## Konfiguracja (`.env`)

Skopiuj plik przykładowy i dostosuj:

```bash
cp .env.example .env
```

Wszystkie zmienne są wczytywane przez aplikację przez `python-dotenv`.

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `PORT` | `8000` | Port nasłuchiwania |
| `HOST` | `0.0.0.0` | Adres nasłuchiwania |
| `PUBLIC_HOST` | `localhost` | Host lub pełny URL używany do budowania linku i QR |
| `PUBLIC_SCHEME` | schemat requestu | Opcjonalny schemat (`http`/`https`), gdy `PUBLIC_HOST` jest samym hostem |
| `PUBLIC_PORT` | brak | Opcjonalny port, gdy `PUBLIC_HOST` jest samym hostem |

Jeśli `PUBLIC_HOST` zaczyna się od `http://` lub `https://`, zmienne `PUBLIC_SCHEME` i `PUBLIC_PORT` są ignorowane.

Przykłady:

```dotenv
PORT=8888
HOST=0.0.0.0

# sam host z osobnym schematem i portem
PUBLIC_HOST=planning.example.com
PUBLIC_SCHEME=https
PUBLIC_PORT=8443

# lub pełny URL (PUBLIC_SCHEME i PUBLIC_PORT ignorowane)
PUBLIC_HOST=https://planning.example.com
```

## Launcher (`run.sh`)

```
./run.sh <komenda>

Komendy:
  start     Uruchom serwis
  test      Uruchom testy (dodatkowe args trafiają do pytest)
  install   Utwórz venv i zainstaluj zależności
```

```bash
./run.sh start
./run.sh test
./run.sh test -k test_voting
./run.sh install
```

## Flow użytkownika

1. Wejście na `/` bez ciasteczka → przekierowanie na stronę **logowania** (podanie imienia)
2. **Strona główna** pokazuje listę aktywnych sesji i formularz tworzenia nowej
3. Po utworzeniu sesji twórca (**PM**) trafia na **stronę sesji** z QR kodem i listą uczestników
4. **Uczestnicy** skanują QR lub otwierają link → jeśli nie mają ciasteczka, trafiają na logowanie, a potem od razu do sesji
5. Każdy (w tym PM) widzi karty estymacji i może zagłosować; wynik jest wysyłany natychmiast po wybraniu karty
6. PM widzi na żywo kto dołączył i kto oddał głos (ale nie jaką wartość)
7. PM klika **„Zamknij i pokaż wyniki"** → estymaty się ujawniają wszystkim
8. PM może **zresetować sesję** (nowe głosowanie na tym samym URL)

## Estymaty

`1, 2, 3, 5, 8, 13, 21, 34, 55, 89, ☕, ?, ∞`

## Struktura projektu

```
planing_estimator/
├── src/
│   ├── domain/
│   │   └── models.py           # Modele domenowe: Session, Participant, Estimate
│   ├── repositories/
│   │   ├── base.py             # ABC SessionRepository
│   │   └── in_memory.py        # Implementacja in-memory
│   ├── services/
│   │   ├── session_service.py  # Logika biznesowa
│   │   └── name_generator.py   # Generator losowych nazw sesji
│   ├── api/
│   │   ├── dependencies.py     # FastAPI dependency injection
│   │   └── routes.py           # HTTP routes + WebSocket
│   └── main.py                 # Aplikacja FastAPI + punkt wejścia
├── tests/
│   ├── test_session_service.py # Testy jednostkowe serwisu
│   └── test_api.py             # Testy integracyjne API
├── web/
│   ├── static/style.css        # Style (RWD)
│   └── templates/              # Szablony Jinja2
│       ├── base.html
│       ├── login.html          # Strona logowania (podanie imienia)
│       ├── home.html           # Strona główna (lista sesji + tworzenie)
│       └── session.html        # Strona sesji (QR, uczestnicy, głosowanie)
├── requirements.txt
├── .env.example
└── pytest.ini
```

## Podmianka storage

Żeby zastąpić in-memory bazą danych, wystarczy zaimplementować `SessionRepository` (ABC z `src/repositories/base.py`) i podmienić w `src/api/dependencies.py`.
