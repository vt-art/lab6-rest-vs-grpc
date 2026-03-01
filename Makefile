SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

PY := python3
HOST ?= localhost

# ---------- Files (edit if needed) ----------
IMAGE_FILE := Flatirons_Winter_Sunrise_edit_2.jpg

REST_SERVER := rest-server-final.py
REST_CLIENT := rest-client-final.py
REST_PORT   := 5000

GRPC_SERVER := grpc-server-final.py
GRPC_CLIENT := grpc-client-final.py
GRPC_PORT   := 50051

# ---------- Outputs ----------
REST_MD := SOLUTION-rest.md
GRPC_MD := SOLUTION-grpc.md

REST_PID := .rest_server.pid
GRPC_PID := .grpc_server.pid
REST_LOG := .rest_server.log
GRPC_LOG := .grpc_server.log

# ---------- Repetitions (override like: make all REPS_ADD=1000) ----------
REPS_ADD  ?= 1000
REPS_IMG  ?= 100
REPS_DOT  ?= 1000
REPS_JSON ?= 100

# ---------- Helpers ----------
define require_file
	@if [[ ! -f "$(1)" ]]; then \
		echo "ERROR: Missing required file: $(1)"; \
		exit 1; \
	fi
endef

define require_cmd
	@command -v "$(1)" >/dev/null 2>&1 || { echo "ERROR: missing command: $(1)"; exit 1; }
endef

# Extract numeric ms from output line: "Took <num> ms per operation"
define extract_ms
	awk '/Took/ {print $$2}' | tail -n 1
endef

.PHONY: all rest grpc clean rest-clean grpc-clean rest-start rest-stop grpc-start grpc-stop check

check:
	$(call require_cmd,curl)
	$(call require_cmd,$(PY))
	$(call require_file,$(IMAGE_FILE))
	$(call require_file,$(REST_SERVER))
	$(call require_file,$(REST_CLIENT))
	$(call require_file,$(GRPC_SERVER))
	$(call require_file,$(GRPC_CLIENT))
	@echo "OK: required files/commands found."

# ===================== REST =====================

rest-start:
	@echo "Starting REST server..."
	@nohup $(PY) $(REST_SERVER) >$(REST_LOG) 2>&1 & echo $$! > $(REST_PID)
	@for i in {1..60}; do \
		if curl -s "http://$(HOST):$(REST_PORT)/api/add/1/1" >/dev/null 2>&1; then \
			echo "REST server is up."; \
			exit 0; \
		fi; \
		sleep 0.1; \
	done; \
	echo "ERROR: REST server did not start. Check $(REST_LOG)"; \
	exit 1

rest-stop:
	@if [[ -f "$(REST_PID)" ]]; then \
		PID="$$(cat $(REST_PID) || true)"; \
		if [[ -n "$$PID" ]] && kill -0 "$$PID" >/dev/null 2>&1; then \
			echo "Stopping REST server (PID $$PID)"; \
			kill "$$PID" >/dev/null 2>&1 || true; \
			sleep 0.2; \
		fi; \
		rm -f "$(REST_PID)"; \
	else \
		echo "REST PID file not found (server not tracked)."; \
	fi

rest:
	@$(MAKE) check
	@$(MAKE) rest-start
	@echo "Running REST benchmarks..."
	@ADD_OUT="$$( $(PY) $(REST_CLIENT) $(HOST) add $(REPS_ADD) )"; \
	ADD_MS="$$( echo "$$ADD_OUT" | $(extract_ms) )"; \
	RAW_OUT="$$( $(PY) $(REST_CLIENT) $(HOST) rawImage $(REPS_IMG) )"; \
	RAW_MS="$$( echo "$$RAW_OUT" | $(extract_ms) )"; \
	DOT_OUT="$$( $(PY) $(REST_CLIENT) $(HOST) dotProduct $(REPS_DOT) )"; \
	DOT_MS="$$( echo "$$DOT_OUT" | $(extract_ms) )"; \
	JSON_OUT="$$( $(PY) $(REST_CLIENT) $(HOST) jsonImage $(REPS_JSON) )"; \
	JSON_MS="$$( echo "$$JSON_OUT" | $(extract_ms) )"; \
	TS="$$(date -u '+%Y-%m-%d %H:%M:%S UTC')"; \
	{ \
		echo "# REST Timing Results"; \
		echo ""; \
		echo "- Host: $(HOST)"; \
		echo "- Port: $(REST_PORT)"; \
		echo "- Timestamp: $$TS"; \
		echo ""; \
		echo "## Average latency (ms/op)"; \
		echo ""; \
		echo "| Method | Reps | ms/op |"; \
		echo "|---|---:|---:|"; \
		echo "| REST add | $(REPS_ADD) | $$ADD_MS |"; \
		echo "| REST rawimg | $(REPS_IMG) | $$RAW_MS |"; \
		echo "| REST dotproduct | $(REPS_DOT) | $$DOT_MS |"; \
		echo "| REST jsonimg | $(REPS_JSON) | $$JSON_MS |"; \
		echo ""; \
	} > "$(REST_MD)"
	@echo "Wrote $(REST_MD)"
	@$(MAKE) rest-stop

rest-clean: rest-stop
	@rm -f "$(REST_LOG)"
	@echo "Cleaned REST artifacts."

# ===================== gRPC =====================

grpc-start:
	@echo "Starting gRPC server..."
	@nohup $(PY) $(GRPC_SERVER) >$(GRPC_LOG) 2>&1 & echo $$! > $(GRPC_PID)
	@# Wait for port to open by attempting a lightweight client call (add 1 rep)
	@for i in {1..60}; do \
		if $(PY) $(GRPC_CLIENT) $(HOST) add 1 >/dev/null 2>&1; then \
			echo "gRPC server is up."; \
			exit 0; \
		fi; \
		sleep 0.1; \
	done; \
	echo "ERROR: gRPC server did not start. Check $(GRPC_LOG)"; \
	exit 1

grpc-stop:
	@if [[ -f "$(GRPC_PID)" ]]; then \
		PID="$$(cat $(GRPC_PID) || true)"; \
		if [[ -n "$$PID" ]] && kill -0 "$$PID" >/dev/null 2>&1; then \
			echo "Stopping gRPC server (PID $$PID)"; \
			kill "$$PID" >/dev/null 2>&1 || true; \
			sleep 0.2; \
		fi; \
		rm -f "$(GRPC_PID)"; \
	else \
		echo "gRPC PID file not found (server not tracked)."; \
	fi

grpc:
	@$(MAKE) check
	@$(MAKE) grpc-start
	@echo "Running gRPC benchmarks..."
	@ADD_OUT="$$( $(PY) $(GRPC_CLIENT) $(HOST) add $(REPS_ADD) )"; \
	ADD_MS="$$( echo "$$ADD_OUT" | $(extract_ms) )"; \
	RAW_OUT="$$( $(PY) $(GRPC_CLIENT) $(HOST) rawImage $(REPS_IMG) )"; \
	RAW_MS="$$( echo "$$RAW_OUT" | $(extract_ms) )"; \
	DOT_OUT="$$( $(PY) $(GRPC_CLIENT) $(HOST) dotProduct $(REPS_DOT) )"; \
	DOT_MS="$$( echo "$$DOT_OUT" | $(extract_ms) )"; \
	JSON_OUT="$$( $(PY) $(GRPC_CLIENT) $(HOST) jsonImage $(REPS_JSON) )"; \
	JSON_MS="$$( echo "$$JSON_OUT" | $(extract_ms) )"; \
	TS="$$(date -u '+%Y-%m-%d %H:%M:%S UTC')"; \
	{ \
		echo "# gRPC Timing Results"; \
		echo ""; \
		echo "- Host: $(HOST)"; \
		echo "- Port: $(GRPC_PORT)"; \
		echo "- Timestamp: $$TS"; \
		echo ""; \
		echo "## Average latency (ms/op)"; \
		echo ""; \
		echo "| Method | Reps | ms/op |"; \
		echo "|---|---:|---:|"; \
		echo "| gRPC add | $(REPS_ADD) | $$ADD_MS |"; \
		echo "| gRPC rawimg | $(REPS_IMG) | $$RAW_MS |"; \
		echo "| gRPC dotproduct | $(REPS_DOT) | $$DOT_MS |"; \
		echo "| gRPC jsonimg | $(REPS_JSON) | $$JSON_MS |"; \
		echo ""; \
	} > "$(GRPC_MD)"
	@echo "Wrote $(GRPC_MD)"
	@$(MAKE) grpc-stop

grpc-clean: grpc-stop
	@rm -f "$(GRPC_LOG)"
	@echo "Cleaned gRPC artifacts."

# ===================== Combined =====================

all:
	@$(MAKE) rest
	@$(MAKE) grpc

clean: rest-clean grpc-clean