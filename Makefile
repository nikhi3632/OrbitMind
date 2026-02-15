# OrbitMind Makefile

.PHONY: help install migrate db-status db-delete db-reset db-shell db-count collect test clean

help:
	@echo "OrbitMind Commands"
	@echo "=================="
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       Run pending migrations"
	@echo "  make db-status     Show migration status"
	@echo "  make db-delete     Drop all tables (DESTRUCTIVE)"
	@echo "  make db-reset      Drop and recreate all tables (DESTRUCTIVE)"
	@echo "  make db-shell      Open psql shell to database"
	@echo "  make db-count      Show row counts"
	@echo ""
	@echo "Collector:"
	@echo "  make collect       Run collector (foreground)"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run tests"
	@echo "  make clean         Remove cache files"

# Setup
install:
	pip install -r requirements.txt

# Database
migrate:
	python scripts/migrate.py

db-status:
	python scripts/migrate.py --status

db-delete:
	python scripts/db_delete.py

db-reset:
	python scripts/db_reset.py

db-shell:
	psql "$$(python scripts/db_url.py)"

db-count:
	python scripts/db_count.py

# Collector
collect:
	python scripts/run_collector.py

# Development
test:
	python -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
