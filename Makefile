SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

PY := python3

# The purpose of this Makefile is to run the REST and grpc programs and 
# output timing files for local, samezone, different zone
# ===================== VM CONFIG =====================
PROJECT ?= lab6-488919
DIR ?= $$HOME/lab6-rest-vs-grpc

ZONE_CENTRAL := us-central1-a
ZONE_EU      := europe-west3-a

# VMs
VM_LOCAL          := lab6-local
VM_SAME_SERVER    := lab6-samezone-server
VM_SAME_CLIENT    := lab6-samezone-client
VM_DIFF_SERVER    := lab6-diffregion-server
VM_DIFF_CLIENT    := lab6-diffregion-client

# Internal IPs (use internal IPs for measurements)
IP_SAME_SERVER := $(shell gcloud compute instances describe $(VM_SAME_SERVER) --zone $(ZONE_CENTRAL) --format='get(networkInterfaces[0].networkIP)')
IP_DIFF_SERVER := $(shell gcloud compute instances describe $(VM_DIFF_SERVER) --zone $(ZONE_EU) --format='get(networkInterfaces[0].networkIP)')

# ===================== FILES =====================
IMAGE_FILE := Flatirons_Winter_Sunrise_edit_2.jpg

REST_SERVER := rest-server-final.py
REST_CLIENT := rest-client-final.py
REST_PORT   := 5000

GRPC_SERVER := grpc-server-final.py
GRPC_CLIENT := grpc-client-final.py
GRPC_PORT   := 50051

# Outputs
REST_MD := SOLUTION-rest.md
GRPC_MD := SOLUTION-grpc.md

# Per the lab instructions complete 1000 reps for local and same
# server and complete 100 reps for different region
# Reps
REPS_ADD  ?= 1000
REPS_IMG  ?= 1000
REPS_DOT  ?= 1000
REPS_JSON ?= 1000

# Reps for different region analysis
EU_REPS_ADD  ?= 100
EU_REPS_IMG  ?= 100
EU_REPS_DOT  ?= 100
EU_REPS_JSON ?= 100

# Extract numeric ms from output line: "Took <num> ms per operation"
define extract_ms
	awk '/Took/ {print $$2}' | tail -n 1
endef

# ===================== HELPERS =====================
define require_cmd
	@command -v "$(1)" >/dev/null 2>&1 || { echo "ERROR: missing command: $(1)"; exit 1; }
endef

.PHONY: check
check:
	$(call require_cmd,gcloud)
	$(call require_cmd,awk)
	$(call require_cmd,paste)
	@echo "OK: local tools found."
	@gcloud config set project $(PROJECT) >/dev/null

# ssh helper: $(call ssh,VM,ZONE,'command...')
define ssh
	gcloud compute ssh $(1) --zone $(2) --quiet --command $(3)
endef

# scp helper: $(call scp_from,VM,ZONE,remote_path,local_path)
define scp_from
	gcloud compute scp $(1):$(3) $(4) --zone $(2) --quiet
endef

# Start/stop servers on a VM without PID files
define start_rest_on
	$(call ssh,$(1),$(2),"'cd $(DIR) && nohup $(PY) $(REST_SERVER) > .rest_server.log 2>&1 < /dev/null & disown || true'")
endef

define start_grpc_on
	$(call ssh,$(1),$(2),"'cd $(DIR) && nohup $(PY) $(GRPC_SERVER) > .grpc_server.log 2>&1 < /dev/null & disown || true'")
endef

define stop_rest_on
	$(call ssh,$(1),$(2),"'pkill -f \"$(REST_SERVER)\" 2>/dev/null || true'")
endef

define stop_grpc_on
	$(call ssh,$(1),$(2),"'pkill -f \"$(GRPC_SERVER)\" 2>/dev/null || true'")
endef

# Run client benchmarks on a VM and save Tab-Separated Values (TSV) there:
# TSV is a plain text format where each line is a record and each field is separated
# by a tab character (\t)

define run_rest_tsv_on
	$(call ssh,$(1),$(2),"'cd $(DIR) && \
	  ADD_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) add $(REPS_ADD) )\"; ADD_MS=\"$$( echo \"$$ADD_OUT\" | $(extract_ms) )\"; \
	  RAW_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) rawImage $(REPS_IMG) )\"; RAW_MS=\"$$( echo \"$$RAW_OUT\" | $(extract_ms) )\"; \
	  DOT_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) dotProduct $(REPS_DOT) )\"; DOT_MS=\"$$( echo \"$$DOT_OUT\" | $(extract_ms) )\"; \
	  JSON_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) jsonImage $(REPS_JSON) )\"; JSON_MS=\"$$( echo \"$$JSON_OUT\" | $(extract_ms) )\"; \
	  printf \"add\\t%s\\nrawimg\\t%s\\ndotproduct\\t%s\\njsonimg\\t%s\\n\" \"$$ADD_MS\" \"$$RAW_MS\" \"$$DOT_MS\" \"$$JSON_MS\" > $(4)'")
endef

define run_grpc_tsv_on
	$(call ssh,$(1),$(2),"'cd $(DIR) && \
	  ADD_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) add $(REPS_ADD) )\"; ADD_MS=\"$$( echo \"$$ADD_OUT\" | $(extract_ms) )\"; \
	  RAW_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) rawImage $(REPS_IMG) )\"; RAW_MS=\"$$( echo \"$$RAW_OUT\" | $(extract_ms) )\"; \
	  DOT_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) dotProduct $(REPS_DOT) )\"; DOT_MS=\"$$( echo \"$$DOT_OUT\" | $(extract_ms) )\"; \
	  JSON_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) jsonImage $(REPS_JSON) )\"; JSON_MS=\"$$( echo \"$$JSON_OUT\" | $(extract_ms) )\"; \
	  printf \"add\\t%s\\nrawimg\\t%s\\ndotproduct\\t%s\\njsonimg\\t%s\\n\" \"$$ADD_MS\" \"$$RAW_MS\" \"$$DOT_MS\" \"$$JSON_MS\" > $(4)'")
endef

define run_rest_tsv_on_eu
	$(call ssh,$(1),$(2),"'cd $(DIR) && \
	  ADD_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) add $(EU_REPS_ADD) )\"; ADD_MS=\"$$( echo \"$$ADD_OUT\" | $(extract_ms) )\"; \
	  RAW_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) rawImage $(EU_REPS_IMG) )\"; RAW_MS=\"$$( echo \"$$RAW_OUT\" | $(extract_ms) )\"; \
	  DOT_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) dotProduct $(EU_REPS_DOT) )\"; DOT_MS=\"$$( echo \"$$DOT_OUT\" | $(extract_ms) )\"; \
	  JSON_OUT=\"$$( $(PY) $(REST_CLIENT) $(3) jsonImage $(EU_REPS_JSON) )\"; JSON_MS=\"$$( echo \"$$JSON_OUT\" | $(extract_ms) )\"; \
	  printf \"add\\t%s\\nrawimg\\t%s\\ndotproduct\\t%s\\njsonimg\\t%s\\n\" \"$$ADD_MS\" \"$$RAW_MS\" \"$$DOT_MS\" \"$$JSON_MS\" > $(4)'")
endef

define run_grpc_tsv_on_eu
	$(call ssh,$(1),$(2),"'cd $(DIR) && \
	  ADD_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) add $(EU_REPS_ADD) )\"; ADD_MS=\"$$( echo \"$$ADD_OUT\" | $(extract_ms) )\"; \
	  RAW_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) rawImage $(EU_REPS_IMG) )\"; RAW_MS=\"$$( echo \"$$RAW_OUT\" | $(extract_ms) )\"; \
	  DOT_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) dotProduct $(EU_REPS_DOT) )\"; DOT_MS=\"$$( echo \"$$DOT_OUT\" | $(extract_ms) )\"; \
	  JSON_OUT=\"$$( $(PY) $(GRPC_CLIENT) $(3) jsonImage $(EU_REPS_JSON) )\"; JSON_MS=\"$$( echo \"$$JSON_OUT\" | $(extract_ms) )\"; \
	  printf \"add\\t%s\\nrawimg\\t%s\\ndotproduct\\t%s\\njsonimg\\t%s\\n\" \"$$ADD_MS\" \"$$RAW_MS\" \"$$DOT_MS\" \"$$JSON_MS\" > $(4)'")
endef

# ===================== LOCAL TARGETS  =====================
.PHONY: rest grpc all clean rest-clean grpc-clean

rest:
	@echo "Tip: use rest3 for Local/Same-Zone/Diff-Region tables. This target only does local on current machine."

grpc:
	@echo "Tip: use grpc3 for Local/Same-Zone/Diff-Region tables. This target only does local on current machine."

all:
	@$(MAKE) rest
	@$(MAKE) grpc

clean:
	@rm -f .rest_local.tsv .rest_same.tsv .rest_diff.tsv .grpc_local.tsv .grpc_same.tsv .grpc_diff.tsv
	@echo "Cleaned local result TSV files."

# ===================== ORCHESTRATED 3-COLUMN RESULTS =====================
.PHONY: servers-up servers-down rest3 grpc3 all3

servers-up: check
	@echo "Starting servers on VMs..."
	@# Local VM runs both servers for Local tests
	$(call start_rest_on,$(VM_LOCAL),$(ZONE_CENTRAL))
	$(call start_grpc_on,$(VM_LOCAL),$(ZONE_CENTRAL))
	@# Same-zone server VM
	$(call start_rest_on,$(VM_SAME_SERVER),$(ZONE_CENTRAL))
	$(call start_grpc_on,$(VM_SAME_SERVER),$(ZONE_CENTRAL))
	@# Diff-region server VM 
	$(call start_rest_on,$(VM_DIFF_SERVER),$(ZONE_EU))
	$(call start_grpc_on,$(VM_DIFF_SERVER),$(ZONE_EU))
	@echo "Servers started."

servers-down: check
	@echo "Stopping servers on VMs..."
	$(call stop_rest_on,$(VM_LOCAL),$(ZONE_CENTRAL))
	$(call stop_grpc_on,$(VM_LOCAL),$(ZONE_CENTRAL))
	$(call stop_rest_on,$(VM_SAME_SERVER),$(ZONE_CENTRAL))
	$(call stop_grpc_on,$(VM_SAME_SERVER),$(ZONE_CENTRAL))
	$(call stop_rest_on,$(VM_DIFF_SERVER),$(ZONE_EU))
	$(call stop_grpc_on,$(VM_DIFF_SERVER),$(ZONE_EU))
	@echo "Servers stopped."

rest3: check servers-up
	@echo "Collecting REST timings..."
	@# Local column: run client on lab6-local against localhost
	$(call run_rest_tsv_on,$(VM_LOCAL),$(ZONE_CENTRAL),localhost,.rest_local.tsv)
	@# Same-zone column: run client on samezone-client against samezone-server internal IP
	$(call run_rest_tsv_on,$(VM_SAME_CLIENT),$(ZONE_CENTRAL),$(IP_SAME_SERVER),.rest_same.tsv)
	@# Diff-region column: run client on diffregion-client (east) against diffregion-server internal IP (central)
	$(call run_rest_tsv_on_eu,$(VM_DIFF_CLIENT),$(ZONE_CENTRAL),$(IP_DIFF_SERVER),.rest_diff.tsv)

	@echo "Writing $(REST_MD)..."
	@TS="$$(date -u '+%Y-%m-%d %H:%M:%S UTC')"; \
	{ \
	  echo "# REST Timing Results"; \
	  echo ""; \
	  echo "- Timestamp: $$TS"; \
	  echo "- Reps: Local/Same-Zone add=$(REPS_ADD), dotproduct=$(REPS_DOT), rawimg=$(REPS_IMG), jsonimg=$(REPS_JSON); Different-Region add=$(EU_REPS_ADD), dotproduct=$(EU_REPS_DOT), rawimg=$(EU_REPS_IMG), jsonimg=$(EU_REPS_JSON)"; \
	  echo ""; \
	  echo "## Average latency (ms/op)"; \
	  echo ""; \
	  echo "| Method | Local | Same-Zone | Different Region |"; \
	  echo "|---|---:|---:|---:|"; \
	  paste .rest_local.tsv .rest_same.tsv .rest_diff.tsv | awk -F'\t' '{printf("| REST %s | %s | %s | %s |\n", $$1, $$2, $$4, $$6)}'; \
	  echo ""; \
	} > $(REST_MD)
	@echo "Wrote $(REST_MD)"
	@$(MAKE) servers-down

grpc3: check servers-up
	@echo "Collecting gRPC timings..."
	@# Local column: run client on lab6-local against localhost
	$(call run_grpc_tsv_on,$(VM_LOCAL),$(ZONE_CENTRAL),localhost,.grpc_local.tsv)
	@# Same-zone column: run client on samezone-client against samezone-server internal IP
	$(call run_grpc_tsv_on,$(VM_SAME_CLIENT),$(ZONE_CENTRAL),$(IP_SAME_SERVER),.grpc_same.tsv)
	@# Diff-region column: run client on diffregion-client (east) against diffregion-server internal IP (central)
	$(call run_grpc_tsv_on_eu,$(VM_DIFF_CLIENT),$(ZONE_CENTRAL),$(IP_DIFF_SERVER),.grpc_diff.tsv)

	@echo "Writing $(GRPC_MD)..."
	@TS="$$(date -u '+%Y-%m-%d %H:%M:%S UTC')"; \
	{ \
	  echo "# gRPC Timing Results"; \
	  echo ""; \
	  echo "- Timestamp: $$TS"; \
	  echo "- Reps: Local/Same-Zone add=$(REPS_ADD), dotproduct=$(REPS_DOT), rawimg=$(REPS_IMG), jsonimg=$(REPS_JSON); Different-Region add=$(EU_REPS_ADD), dotproduct=$(EU_REPS_DOT), rawimg=$(EU_REPS_IMG), jsonimg=$(EU_REPS_JSON)"; \
	  echo ""; \
	  echo "## Average latency (ms/op)"; \
	  echo ""; \
	  echo "| Method | Local | Same-Zone | Different Region |"; \
	  echo "|---|---:|---:|---:|"; \
	  paste .grpc_local.tsv .grpc_same.tsv .grpc_diff.tsv | awk -F'\t' '{printf("| gRPC %s | %s | %s | %s |\n", $$1, $$2, $$4, $$6)}'; \
	  echo ""; \
	} > $(GRPC_MD)
	@echo "Wrote $(GRPC_MD)"
	@$(MAKE) servers-down

all3:
	@$(MAKE) rest3
	@$(MAKE) grpc3