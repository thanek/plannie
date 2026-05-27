#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="venv"
REQUIREMENTS="requirements.txt"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_ROOT"

# ── Kolory ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}[info]${RESET} $*"; }
success() { echo -e "${GREEN}[ok]${RESET}   $*"; }
warn()    { echo -e "${YELLOW}[warn]${RESET} $*"; }
error()   { echo -e "${RED}[err]${RESET}  $*" >&2; }

# ── Helpers ───────────────────────────────────────────────────────────────────
ensure_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        warn "Virtualenv nie istnieje – tworzę '$VENV_DIR'..."
        python3 -m venv "$VENV_DIR"
        success "Virtualenv utworzony."
    fi
}

activate_venv() {
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
}

needs_install() {
    # Minimalna walidacja kluczowych pakietów używanych przez aplikację.
    "$VENV_DIR/bin/python" -c "import fastapi, dotenv" 2>/dev/null && return 1 || return 0
}

do_install() {
    ensure_venv
    activate_venv
    info "Instaluję zależności z $REQUIREMENTS..."
    pip install --quiet --upgrade pip
    pip install --quiet -r "$REQUIREMENTS"
    success "Zależności zainstalowane."
}

ensure_deps() {
    ensure_venv
    if needs_install; then
        warn "Zależności nie są zainstalowane – uruchamiam install..."
        do_install
    else
        activate_venv
    fi
}

# ── Komendy ───────────────────────────────────────────────────────────────────
cmd_install() {
    do_install
}

cmd_start() {
    ensure_deps
    info "Uruchamiam Planning Estimator"
    echo -e "${BOLD}  Zatrzymaj serwis: Ctrl+C${RESET}"
    echo ""
    exec "$VENV_DIR/bin/python" -m src.main
}

cmd_test() {
    ensure_deps
    info "Uruchamiam testy..."
    echo ""
    python -m pytest tests/ -v "$@"
}

# ── Pomoc ─────────────────────────────────────────────────────────────────────
usage() {
    echo ""
    echo -e "${BOLD}Planning Estimator – launcher${RESET}"
    echo ""
    echo -e "  ${CYAN}./run.sh${RESET} ${BOLD}<komenda>${RESET}"
    echo ""
    echo -e "  ${BOLD}Komendy:${RESET}"
    echo -e "    ${GREEN}start${RESET}     Uruchom serwis (domyślnie http://0.0.0.0:8000)"
    echo -e "    ${GREEN}test${RESET}      Uruchom testy (dodatkowe args trafiają do pytest)"
    echo -e "    ${GREEN}install${RESET}   Utwórz venv i zainstaluj zależności"
    echo ""
    echo -e "  ${BOLD}Zmienne środowiskowe:${RESET}"
    echo -e "    HOST   Adres nasłuchiwania (domyślnie: 0.0.0.0)"
    echo -e "    PORT   Port nasłuchiwania  (domyślnie: 8000)"
    echo ""
    echo -e "  ${BOLD}Przykłady:${RESET}"
    echo -e "    ${YELLOW}./run.sh start${RESET}"
    echo -e "    ${YELLOW}PORT=9000 ./run.sh start${RESET}"
    echo -e "    ${YELLOW}./run.sh test${RESET}"
    echo -e "    ${YELLOW}./run.sh test -k test_voting${RESET}"
    echo -e "    ${YELLOW}./run.sh install${RESET}"
    echo ""
}

# ── Dispatcher ────────────────────────────────────────────────────────────────
COMMAND="${1:-}"
shift || true   # przesuń argumenty; reszta trafi do $@

case "$COMMAND" in
    start)   cmd_start "$@" ;;
    test)    cmd_test  "$@" ;;
    install) cmd_install ;;
    "")      usage ;;
    *)
        error "Nieznana komenda: '$COMMAND'"
        usage
        exit 1
        ;;
esac

