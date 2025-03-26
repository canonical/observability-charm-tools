PROJECT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

SRC := $(PROJECT)src
TESTS := $(PROJECT)tests
ALL := $(SRC) $(TESTS)

export PY_COLORS=1

# Update uv.lock with the latest deps
lock:
	uv lock --upgrade --no-cache

# Lint the code
lint:
	uv run --frozen --isolated --extra dev \
		ruff check $(ALL)
	uv run --frozen --isolated --extra dev \
		ruff format --check --diff $(ALL)

# Run static checks
static:
	uv run --frozen --isolated --extra dev pyright

# Format the code
fmt:
	uv run --frozen --isolated --extra dev \
		ruff check --fix-only $(ALL)
	uv run --frozen --isolated --extra dev \
		ruff format $(ALL)

# Run unit tests
unit:
	uv run --frozen --isolated --extra dev \
		coverage run \
		--source=$(SRC) \
		-m pytest \
		--tb native \
		--verbose \
		--capture=no \
		$(TESTS)/unit \
		$(ARGS)

	uv run --frozen --isolated --extra dev \
		coverage report
