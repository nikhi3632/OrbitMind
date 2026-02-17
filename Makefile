# OrbitMind Makefile
PYTHON = .venv/bin/python

.PHONY: help install migrate db-status db-delete db-reset db-shell db-count collect collect-start collect-stop collect-logs collect-status test clean

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
	@echo "Collector (Railway):"
	@echo "  make collect        Stop, reset DB, and start collector"
	@echo "  make collect-start  Start collector on Railway"
	@echo "  make collect-stop   Stop collector on Railway"
	@echo "  make collect-logs   View Railway logs"
	@echo "  make collect-status Show Railway status"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run tests"
	@echo "  make clean         Remove cache files"

# Setup
install:
	$(PYTHON) -m pip install -r requirements.txt

# Database
migrate:
	$(PYTHON) scripts/migrate.py

db-status:
	$(PYTHON) scripts/migrate.py --status

db-delete:
	$(PYTHON) scripts/db_delete.py

db-reset:
	$(PYTHON) scripts/db_reset.py

db-shell:
	psql "$$($(PYTHON) scripts/db_url.py)"

db-count:
	$(PYTHON) scripts/db_count.py

# Collector (Railway)
collect:
	railway down --service OrbitMind -y || true
	echo "y" | $(PYTHON) scripts/db_reset.py
	railway up --service OrbitMind --detach

collect-start:
	railway up --service OrbitMind --detach

collect-stop:
	railway down --service OrbitMind -y

collect-logs:
	railway logs --service OrbitMind

collect-status:
	$(PYTHON) scripts/collect_status.py

# Development
test:
	$(PYTHON) -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
