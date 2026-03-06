#!/bin/bash

################################################################################
# TickerPulse CI Test Orchestration Script
#
# Usage:
#   ./scripts/run-tests.sh [--backend|--frontend|--e2e|--all|--coverage]
#
# Examples:
#   ./scripts/run-tests.sh                 # Run all tests
#   ./scripts/run-tests.sh --backend       # Backend tests only
#   ./scripts/run-tests.sh --frontend      # Frontend tests only
#   ./scripts/run-tests.sh --e2e           # E2E tests only
#   ./scripts/run-tests.sh --coverage      # All tests with coverage reports
#
# Exit codes:
#   0 - All tests passed
#   1 - Test failures
#   2 - Configuration error
#
################################################################################

set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_VERSION="3.11"
NODE_VERSION="20"

# Test results tracking
FAILED_TESTS=()
PASSED_TESTS=()
SKIPPED_TESTS=()
START_TIME=$(date +%s)

################################################################################
# Utility Functions
################################################################################

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_result() {
    local test_name=$1
    local result=$2

    if [ "$result" = "passed" ]; then
        log_success "$test_name"
        PASSED_TESTS+=("$test_name")
    elif [ "$result" = "failed" ]; then
        log_error "$test_name"
        FAILED_TESTS+=("$test_name")
    else
        log_warning "$test_name (skipped)"
        SKIPPED_TESTS+=("$test_name")
    fi
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

################################################################################
# Setup Functions
################################################################################

setup_python() {
    log_info "Setting up Python environment..."

    if ! check_command python3; then
        log_error "Python 3 is required but not installed"
        return 1
    fi

    cd "$PROJECT_ROOT"

    if [ ! -f requirements.txt ]; then
        log_error "requirements.txt not found"
        return 1
    fi

    log_info "Installing Python dependencies..."
    python -m pip install --upgrade pip -q || return 1
    pip install -r requirements.txt -q || return 1

    return 0
}

setup_node() {
    log_info "Setting up Node.js environment..."

    if ! check_command node; then
        log_error "Node.js is required but not installed"
        return 1
    fi

    cd "$PROJECT_ROOT/frontend"

    if [ ! -f package.json ]; then
        log_error "frontend/package.json not found"
        return 1
    fi

    log_info "Installing Node.js dependencies..."
    npm ci --silent || return 1

    return 0
}

################################################################################
# Backend Tests
################################################################################

run_backend_tests() {
    log_section "Backend Unit Tests"

    if ! setup_python; then
        log_result "Backend Setup" "failed"
        return 1
    fi

    cd "$PROJECT_ROOT"

    # Run pytest with coverage
    log_info "Running pytest suite..."
    PYTHONPATH=. pytest backend/tests/ \
        -v \
        --tb=short \
        --cov=backend \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/backend \
        --cov-fail-under=70 \
        --timeout=30 \
        2>&1 | tee pytest-output.log

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_result "Backend Tests" "passed"
        log_info "Coverage report: htmlcov/backend/index.html"
        return 0
    else
        log_result "Backend Tests" "failed"
        return 1
    fi
}

run_backend_lint() {
    log_section "Backend Linting"

    if ! setup_python; then
        log_result "Backend Lint Setup" "failed"
        return 1
    fi

    cd "$PROJECT_ROOT"

    local lint_failed=0

    # Black format check
    log_info "Checking format with Black..."
    if black --check backend/ 2>&1 | tee black-output.log; then
        log_result "Black Format Check" "passed"
    else
        log_result "Black Format Check" "failed"
        lint_failed=1
    fi

    # isort check
    log_info "Checking import sorting with isort..."
    if isort --check-only backend/ 2>&1 | tee isort-output.log; then
        log_result "isort Check" "passed"
    else
        log_result "isort Check" "failed"
        lint_failed=1
    fi

    # mypy type checking
    log_info "Type checking with mypy..."
    if mypy backend/ --ignore-missing-imports --allow-untyped-defs 2>&1 | tee mypy-output.log; then
        log_result "mypy Type Check" "passed"
    else
        log_result "mypy Type Check" "failed"
        lint_failed=1
    fi

    return $lint_failed
}

################################################################################
# Frontend Tests
################################################################################

run_frontend_tests() {
    log_section "Frontend Unit Tests"

    if ! setup_node; then
        log_result "Frontend Setup" "failed"
        return 1
    fi

    cd "$PROJECT_ROOT/frontend"

    # Check if test:unit script exists
    if ! npm run test:unit 2>&1 | grep -q "test:unit"; then
        log_warning "test:unit script not found in package.json"
        return 0
    fi

    log_info "Running Vitest suite..."
    if npm run test:unit -- --run --coverage 2>&1 | tee vitest-output.log; then
        log_result "Frontend Unit Tests" "passed"
        log_info "Coverage report: frontend/coverage/index.html"
        return 0
    else
        log_result "Frontend Unit Tests" "failed"
        return 1
    fi
}

run_frontend_lint() {
    log_section "Frontend Linting"

    if ! setup_node; then
        log_result "Frontend Lint Setup" "failed"
        return 1
    fi

    cd "$PROJECT_ROOT/frontend"

    local lint_failed=0

    # ESLint
    log_info "Linting with ESLint..."
    if npm run lint 2>&1 | tee eslint-output.log; then
        log_result "ESLint" "passed"
    else
        log_result "ESLint" "failed"
        lint_failed=1
    fi

    # TypeScript type check
    log_info "Type checking with TypeScript..."
    if npx tsc --noEmit 2>&1 | tee tsc-output.log; then
        log_result "TypeScript Type Check" "passed"
    else
        log_result "TypeScript Type Check" "failed"
        lint_failed=1
    fi

    return $lint_failed
}

################################################################################
# E2E Tests
################################################################################

run_e2e_tests() {
    log_section "E2E Tests (Playwright)"

    if ! setup_node; then
        log_result "E2E Setup" "failed"
        return 1
    fi

    cd "$PROJECT_ROOT/frontend"

    # Check if test:e2e script exists
    if ! npm run 2>&1 | grep -q "test:e2e"; then
        log_warning "test:e2e script not found, checking for playwright..."
        if ! check_command npx; then
            log_warning "npx not available, skipping E2E tests"
            return 0
        fi
    fi

    log_info "Starting backend server..."
    cd "$PROJECT_ROOT"
    export FLASK_ENV=testing
    export FLASK_DEBUG=false
    python -m flask run &> /tmp/flask.log &
    FLASK_PID=$!
    sleep 3

    log_info "Running Playwright E2E tests..."
    cd "$PROJECT_ROOT/frontend"

    if npm run test:e2e 2>&1 | tee playwright-output.log; then
        TEST_RESULT="passed"
    else
        TEST_RESULT="failed"
    fi

    # Cleanup Flask server
    kill $FLASK_PID 2>/dev/null || true

    log_result "E2E Tests" "$TEST_RESULT"

    if [ "$TEST_RESULT" = "passed" ]; then
        return 0
    else
        return 1
    fi
}

################################################################################
# Coverage Report
################################################################################

generate_coverage_report() {
    log_section "Coverage Summary"

    log_info "Backend coverage:"
    if [ -f "$PROJECT_ROOT/htmlcov/backend/index.html" ]; then
        echo "  📊 Report: htmlcov/backend/index.html"
    fi

    log_info "Frontend coverage:"
    if [ -f "$PROJECT_ROOT/frontend/coverage/index.html" ]; then
        echo "  📊 Report: frontend/coverage/index.html"
    fi
}

################################################################################
# Test Results Summary
################################################################################

print_summary() {
    local elapsed=$(($(date +%s) - START_TIME))
    local passed=${#PASSED_TESTS[@]}
    local failed=${#FAILED_TESTS[@]}
    local skipped=${#SKIPPED_TESTS[@]}

    log_section "Test Results Summary"

    echo ""
    echo "Passed:  ${GREEN}$passed${NC}"
    echo "Failed:  ${RED}$failed${NC}"
    echo "Skipped: ${YELLOW}$skipped${NC}"
    echo ""
    echo "Duration: ${elapsed}s"
    echo ""

    if [ $failed -gt 0 ]; then
        echo -e "${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
        echo ""
    fi

    if [ $passed -gt 0 ]; then
        echo -e "${GREEN}Passed Tests:${NC}"
        for test in "${PASSED_TESTS[@]}"; do
            echo "  - $test"
        done
        echo ""
    fi
}

################################################################################
# Main
################################################################################

main() {
    local test_type="${1:---all}"
    local exit_code=0

    log_info "TickerPulse CI Test Suite"
    log_info "Test Type: $test_type"
    echo ""

    case $test_type in
        --backend)
            run_backend_lint && run_backend_tests || exit_code=1
            ;;
        --frontend)
            run_frontend_lint && run_frontend_tests || exit_code=1
            ;;
        --e2e)
            setup_python
            run_e2e_tests || exit_code=1
            ;;
        --coverage)
            run_backend_lint && run_backend_tests && \
            run_frontend_lint && run_frontend_tests && \
            generate_coverage_report || exit_code=1
            ;;
        --all|"")
            run_backend_lint && run_backend_tests && \
            run_frontend_lint && run_frontend_tests || exit_code=1
            ;;
        --help)
            cat <<EOF
Usage: $0 [OPTION]

Options:
  --backend       Run backend tests only
  --frontend      Run frontend tests only
  --e2e           Run E2E tests only
  --all           Run all tests (default)
  --coverage      Run all tests and generate coverage reports
  --help          Show this help message

Examples:
  $0                    # Run all tests
  $0 --backend          # Backend tests only
  $0 --coverage         # All tests with coverage

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $test_type"
            echo "Use --help for usage information"
            exit 2
            ;;
    esac

    print_summary
    exit $exit_code
}

main "$@"
