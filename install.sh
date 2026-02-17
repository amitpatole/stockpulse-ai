#!/bin/bash
# ============================================================
# TickerPulse AI v3.0 - Installer
# Linux / macOS
# ============================================================
#
# Usage:
#   bash install.sh            (from inside the repo)
#   curl <raw-url> | bash      (remote install — clones first)
#
# This script:
#   1. Checks prerequisites (Python 3.10+, Node 18+, npm)
#   2. Creates a Python virtual environment & installs backend deps
#   3. Installs frontend npm packages & builds the Next.js app
#   4. Copies .env.example → .env (if .env doesn't exist)
#   5. Makes run.sh / stop.sh executable
# ============================================================

set -e

# ── Colours ────────────────────────────────────────────────
if [ -t 2 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null)" -ge 8 ]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    CYAN=$(tput setaf 6)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED="" GREEN="" YELLOW="" CYAN="" BOLD="" RESET=""
fi

info()  { echo "${CYAN}[INFO]${RESET}  $*" >&2; }
ok()    { echo "${GREEN}[OK]${RESET}    $*" >&2; }
warn()  { echo "${YELLOW}[WARN]${RESET}  $*" >&2; }
err()   { echo "${RED}[ERROR]${RESET} $*" >&2; }
fatal() { err "$@"; exit 1; }

# ── Banner ─────────────────────────────────────────────────
echo >&2
echo "${BOLD}========================================${RESET}" >&2
echo "${BOLD}  TickerPulse AI v3.0 — Installer${RESET}" >&2
echo "${BOLD}========================================${RESET}" >&2
echo >&2

# ── Helpers ────────────────────────────────────────────────

# Compare two version strings: returns 0 if $1 >= $2
version_gte() {
    # Try sort -V first (GNU coreutils); fall back to manual comparison
    if printf '%s\n%s' "$2" "$1" | sort -V -C 2>/dev/null; then
        return 0
    fi
    # Manual fallback: compare major.minor
    local IFS=.
    local i a=($1) b=($2)
    for ((i = 0; i < ${#b[@]}; i++)); do
        local va=${a[i]:-0}
        local vb=${b[i]:-0}
        if ((va > vb)); then return 0; fi
        if ((va < vb)); then return 1; fi
    done
    return 0
}

# ── Prerequisite Checks ───────────────────────────────────
MISSING=0

# Python
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if version_gte "$PY_VER" "3.10"; then
        ok "Python $PY_VER"
    else
        err "Python $PY_VER found — need 3.10+"
        MISSING=1
    fi
else
    err "Python 3 not found"
    MISSING=1
fi

# Node.js
if command -v node >/dev/null 2>&1; then
    NODE_VER=$(node -v | sed 's/^v//')
    NODE_MAJOR=${NODE_VER%%.*}
    if [ "$NODE_MAJOR" -ge 18 ] 2>/dev/null; then
        ok "Node.js $NODE_VER"
    else
        err "Node.js $NODE_VER found — need 18+"
        MISSING=1
    fi
else
    err "Node.js not found"
    MISSING=1
fi

# npm
if command -v npm >/dev/null 2>&1; then
    NPM_VER=$(npm -v)
    ok "npm $NPM_VER"
else
    err "npm not found"
    MISSING=1
fi

if [ "$MISSING" -ne 0 ]; then
    echo >&2
    err "Missing prerequisites. Please install them first:"
    echo "  Python 3.10+  — https://www.python.org/downloads/" >&2
    echo "  Node.js 18+   — https://nodejs.org/" >&2
    exit 1
fi

# ── Determine Install Directory ───────────────────────────
REPO_URL="https://github.com/amitpatole/tickerpulse-ai.git"

if [ -f "backend/app.py" ] && [ -f "frontend/package.json" ]; then
    # Already inside the repo
    PROJECT_DIR="$(pwd)"
    info "Detected existing repo at $PROJECT_DIR"
else
    # Clone the repo
    if ! command -v git >/dev/null 2>&1; then
        fatal "git is required to clone the repo. Install it from https://git-scm.com/"
    fi
    info "Cloning TickerPulse AI..."
    git clone "$REPO_URL" tickerpulse-ai
    PROJECT_DIR="$(pwd)/tickerpulse-ai"
    cd "$PROJECT_DIR"
    ok "Cloned to $PROJECT_DIR"
fi

# ── Python Virtual Environment ────────────────────────────
echo >&2
info "Setting up Python virtual environment..."

if [ -d "venv" ]; then
    warn "venv/ already exists — reusing"
else
    python3 -m venv venv
    ok "Created venv/"
fi

# Activate
# shellcheck disable=SC1091
source venv/bin/activate

info "Upgrading pip..."
pip install --upgrade pip --quiet

info "Installing backend dependencies..."
pip install -r backend/requirements.txt --quiet
ok "Backend dependencies installed"

# ── Frontend Setup ─────────────────────────────────────────
echo >&2
info "Installing frontend dependencies..."

cd "$PROJECT_DIR/frontend"
npm install --silent 2>&1 | tail -1 || npm install
ok "Frontend npm packages installed"

info "Building frontend (this may take a minute)..."
npm run build
ok "Frontend built"

cd "$PROJECT_DIR"

# ── Environment Configuration ──────────────────────────────
echo >&2
if [ ! -f ".env" ]; then
    cp .env.example .env
    ok "Created .env from .env.example"
else
    warn ".env already exists — skipping copy"
fi

# ── Make Scripts Executable ────────────────────────────────
chmod +x run.sh stop.sh 2>/dev/null || true

# ── Done ───────────────────────────────────────────────────
echo >&2
echo "${BOLD}========================================${RESET}" >&2
echo "${GREEN}${BOLD}  Installation complete!${RESET}" >&2
echo "${BOLD}========================================${RESET}" >&2
echo >&2
echo "  Next steps:" >&2
echo >&2
echo "  1. ${YELLOW}Edit .env${RESET} and add at least one AI provider API key" >&2
echo "     (Anthropic, OpenAI, Google, or xAI)" >&2
echo >&2
echo "  2. Start the application:" >&2
echo "     ${CYAN}./run.sh${RESET}" >&2
echo >&2
echo "  3. Open in your browser:" >&2
echo "     ${CYAN}http://localhost:3000${RESET}" >&2
echo >&2
