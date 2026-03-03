#!/usr/bin/env python3
# This program creates VMs + firewall rules for the REST vs gRPC lab 6.
# It also configures the VMs with a copy of the lab6 materials,
# the python package installations and generates the protobuf stubs. 
# Creates five vms as follows:
#   - vm_local
#   - vm_same_server
#   - vm_same_client
#   - vm_diff_server
#   - vm_diff_client
# And create three firewall rules as follows: 
#   - allow-lab6-rest-5000
#   - allow-lab6-grpc-50051
#   - allow-lab6-icmp

"""
Create VMs + firewall rules AND configure them for the REST vs gRPC lab 6.

Configuration (AKA bootstrapping) steps (per VM):
  - Copy local lab directory (default: ~/lab6-rest-vs-grpc) to VM home dir
  - Install Python deps via pip (user install)
  - Generate protobuf stubs (grpc_service_pb2*.py)

Usage:
  python3 create_lab6_vms.py --project lab6-488919

Notes:
  - Designed for running from Cloud Shell.
  - Different-region server is placed in zone2 (Frankfurt by default).
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


def run(cmd: List[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(shlex.quote(c) for c in cmd))
    return subprocess.run(cmd, check=check, text=True, capture_output=capture)


def gcloud_value(args: List[str]) -> str:
    cp = run(["gcloud", *args], capture=True)
    return (cp.stdout or "").strip()


def exists_firewall_rule(name: str) -> bool:
    cp = run(["gcloud", "compute", "firewall-rules", "describe", name], check=False, capture=True)
    return cp.returncode == 0


def create_firewall_rule_if_missing(
    name: str,
    *,
    target_tags: str,
    rules: str,
    source_ranges: str = "0.0.0.0/0",
    network: str = "default",
) -> None:
    if exists_firewall_rule(name):
        print(f"Firewall rule exists: {name} (skipping)")
        return

    run(
        [
            "gcloud",
            "compute",
            "firewall-rules",
            "create",
            name,
            "--direction=INGRESS",
            "--priority=1000",
            f"--network={network}",
            "--action=ALLOW",
            f"--rules={rules}",
            f"--source-ranges={source_ranges}",
            f"--target-tags={target_tags}",
        ]
    )


def exists_instance(name: str, zone: str) -> bool:
    cp = run(["gcloud", "compute", "instances", "describe", name, f"--zone={zone}"], check=False, capture=True)
    return cp.returncode == 0


def create_instance_if_missing(
    name: str,
    *,
    zone: str,
    machine_type: str,
    image_family: str,
    image_project: str,
    tags: str,
    scopes: str = "https://www.googleapis.com/auth/cloud-platform",
) -> None:
    if exists_instance(name, zone):
        print(f"VM exists: {name} ({zone}) (skipping)")
        return

    run(
        [
            "gcloud",
            "compute",
            "instances",
            "create",
            name,
            f"--zone={zone}",
            f"--machine-type={machine_type}",
            f"--image-family={image_family}",
            f"--image-project={image_project}",
            f"--tags={tags}",
            f"--scopes={scopes}",
        ]
    )


def ssh(vm: str, zone: str, command: str) -> None:
    # Use --quiet to avoid prompts; command runs on remote
    run(["gcloud", "compute", "ssh", vm, f"--zone={zone}", "--quiet", "--command", command])


# Copies the folder to the vm without copying the .git and .venv 
def copy_lab_dir_tar(local_dir: str, vm: str, zone: str, remote_dir: str) -> None:
    local_dir = shlex.quote(local_dir)
    remote_dir = shlex.quote(remote_dir)

    cmd = (
        f"tar --exclude='.git' --exclude='__pycache__' --exclude='.venv' "
        f"-C {local_dir} -cf - . "
        f"| gcloud compute ssh {shlex.quote(vm)} --zone {shlex.quote(zone)} --quiet --command "
        f"\"mkdir -p {remote_dir} && tar -C {remote_dir} -xf -\""
    )
    print("$", cmd)
    subprocess.run(cmd, shell=True, check=True, text=True)


@dataclass(frozen=True)
class VM:
    name: str
    zone: str
    tags: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Create lab VMs + firewall rules + configure code/deps.")
    parser.add_argument("--project", default=None, help="GCP project id (defaults to gcloud config project)")

    # Assignment: zone2 should be Frankfurt for different region server
    parser.add_argument("--zone1", default="us-central1-a", help="Home zone (default us-central1-a)")
    parser.add_argument("--zone2", default="europe-west3-a", help="Different region zone (default europe-west3-a)")

    parser.add_argument("--machine-type", default="e2-micro", help="Machine type (default e2-micro)")
    parser.add_argument("--image-family", default="debian-12", help="Image family (default debian-12)")
    parser.add_argument("--image-project", default="debian-cloud", help="Image project (default debian-cloud)")
    parser.add_argument("--network", default="default", help="VPC network name (default: default)")

    parser.add_argument(
        "--lab-dir",
        default=os.path.expanduser("~/lab6-rest-vs-grpc"),
        help="Local path to lab directory to copy to VMs (default: ~/lab6-rest-vs-grpc)",
    )

    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Only create firewall rules and VMs; do not copy code/install deps/protoc",
    )

    args = parser.parse_args()

    lab_dir = os.path.abspath(os.path.expanduser(args.lab_dir))
    if not args.skip_bootstrap and not os.path.isdir(lab_dir):
        print(f"ERROR: lab dir not found: {lab_dir}", file=sys.stderr)
        print("Make sure you run this from Cloud Shell where that folder exists, or pass --lab-dir PATH.", file=sys.stderr)
        return 2

    project = args.project or gcloud_value(["config", "get-value", "project"])
    if not project:
        print("ERROR: No project set. Run `gcloud config set project YOUR_PROJECT` or pass --project.", file=sys.stderr)
        return 2

    run(["gcloud", "config", "set", "project", project], check=True)

    tag_server = "lab6-server"
    tag_client = "lab6-client"

    # VM names
    vm_local = VM("lab6-local", args.zone1, f"{tag_server},{tag_client}")
    vm_same_server = VM("lab6-samezone-server", args.zone1, tag_server)
    vm_same_client = VM("lab6-samezone-client", args.zone1, tag_client)

    # Per assignment: diff-region SERVER in zone2 (Frankfurt), client stays in zone1 (US)
    vm_diff_server = VM("lab6-diffregion-server", args.zone2, tag_server)
    vm_diff_client = VM("lab6-diffregion-client", args.zone1, tag_client)

    vms = [vm_local, vm_same_server, vm_same_client, vm_diff_server, vm_diff_client]

    print("\n=== Creating firewall rules ===")
    create_firewall_rule_if_missing(
        "allow-lab6-rest-5000",
        target_tags=tag_server,
        rules="tcp:5000",
        network=args.network,
    )
    create_firewall_rule_if_missing(
        "allow-lab6-grpc-50051",
        target_tags=tag_server,
        rules="tcp:50051",
        network=args.network,
    )
    create_firewall_rule_if_missing(
        "allow-lab6-icmp",
        target_tags=tag_server,
        rules="icmp",
        network=args.network,
    )

    print("\n=== Creating VM instances ===")
    for vm in vms:
        create_instance_if_missing(
            vm.name,
            zone=vm.zone,
            machine_type=args.machine_type,
            image_family=args.image_family,
            image_project=args.image_project,
            tags=vm.tags,
        )

    if args.skip_bootstrap:
        print("\nSkipping bootstrap as requested (--skip-bootstrap).")
    else:
        print("\n=== Bootstrapping VMs (copy code + install deps + generate protobuf) ===")

        # Copy code to each VM
        for vm in vms:
            print(f"\n--- Copying {lab_dir} -> {vm.name}:{vm.zone} ---")
            copy_lab_dir_tar(lab_dir, vm.name, vm.zone, remote_dir="/home/vath9383/lab6-rest-vs-grpc")

        # Install dependencies and run protoc on each VM

        remote_lab = "$HOME/lab6-rest-vs-grpc"
        venv_dir = f"{remote_lab}/.venv"

        install_cmd = (
            "set -euo pipefail; "
            "sudo apt-get update -y; "
            # venv module is in python3-venv
            "sudo apt-get install -y python3-venv python3-pip; "
            f"cd {remote_lab}; "
            # create venv if missing
            f"python3 -m venv {venv_dir}; "
            # upgrade pip inside venv + install deps inside venv
            f"{venv_dir}/bin/python -m pip install --upgrade pip setuptools wheel; "
            f"{venv_dir}/bin/python -m pip install flask jsonpickle pillow requests grpcio grpcio-tools"
        )

        verify_cmd = (
            "set -euo pipefail; "
            f"{venv_dir}/bin/python -c \"import flask, jsonpickle, requests; from PIL import Image; import grpc; import grpc_tools; print('deps ok')\""
        )

        protoc_cmd = (
            "set -euo pipefail; "
            f"cd {remote_lab}; "
            f"{venv_dir}/bin/python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. grpc_service.proto; "
            "test -f grpc_service_pb2.py -a -f grpc_service_pb2_grpc.py"
        )

        for vm in vms:
            print(f"\n--- Installing deps on {vm.name} ({vm.zone}) ---")
            ssh(vm.name, vm.zone, install_cmd)
            print(f"--- Verifying deps on {vm.name} ({vm.zone}) ---")
            ssh(vm.name, vm.zone, verify_cmd)
            print(f"--- Running protoc on {vm.name} ({vm.zone}) ---")
            ssh(vm.name, vm.zone, protoc_cmd)
    
    print("\n=== Instances (name, zone, internal/external IP, tags) ===")
    run(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            "--format=table(name,zone,networkInterfaces[0].networkIP:label=INTERNAL_IP,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP,tags.items)",
        ]
    )

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())