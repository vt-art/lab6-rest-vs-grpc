#!/usr/bin/env python3
"""
Create VMs + firewall rules for a REST vs gRPC latency lab.

Requires:
  - gcloud CLI installed (Cloud Shell already has it)
  - gcloud auth/login done
  - a project set (or pass --project)

Example:
  python3 create_lab6_vms.py --project lab6-488919
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from typing import List, Optional


def run(cmd: List[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return the CompletedProcess."""
    # Print the command 
    print("$", " ".join(shlex.quote(c) for c in cmd))
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture,
    )


def gcloud_value(args: List[str]) -> str:
    """Return a single value from gcloud (stripped)."""
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
    cp = run(
        ["gcloud", "compute", "instances", "describe", name, f"--zone={zone}"],
        check=False,
        capture=True,
    )
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Create lab VMs + firewall rules (REST vs gRPC).")
    parser.add_argument("--project", default=None, help="GCP project id (defaults to gcloud config project)")

    # Free e2-micro is only available in us-west1 (Oregon), us-central1 (Iowa), us-east1 (South Carolina)    
    parser.add_argument("--zone1", default="us-central1-a", help="Zone for local + same-zone + diff-server (default us-central1-a)")
    parser.add_argument("--zone2", default="us-east1-b", help="Zone for diff-region client (default us-east1-b)")
    parser.add_argument("--machine-type", default="e2-micro", help="Machine type (default e2-micro)")
    parser.add_argument("--image-family", default="debian-12", help="Image family (default debian-12)")
    parser.add_argument("--image-project", default="debian-cloud", help="Image project (default debian-cloud)")
    parser.add_argument("--network", default="default", help="VPC network name (default: default)")

    args = parser.parse_args()

    # Ensure project is set (either via flag or existing config)
    project = args.project or gcloud_value(["config", "get-value", "project"])
    if not project:
        print("ERROR: No project set. Run `gcloud config set project YOUR_PROJECT` or pass --project.", file=sys.stderr)
        return 2

    run(["gcloud", "config", "set", "project", project], check=True)

    tag_server = "lab6-server"
    tag_client = "lab6-client"

    # VM names
    vm_local = "lab6-local"
    vm_same_server = "lab6-samezone-server"
    vm_same_client = "lab6-samezone-client"
    vm_diff_server = "lab6-diffregion-server"
    vm_diff_client = "lab6-diffregion-client"

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
    create_instance_if_missing(
        vm_local,
        zone=args.zone1,
        machine_type=args.machine_type,
        image_family=args.image_family,
        image_project=args.image_project,
        tags=f"{tag_server},{tag_client}",
    )
    create_instance_if_missing(
        vm_same_server,
        zone=args.zone1,
        machine_type=args.machine_type,
        image_family=args.image_family,
        image_project=args.image_project,
        tags=tag_server,
    )
    create_instance_if_missing(
        vm_same_client,
        zone=args.zone1,
        machine_type=args.machine_type,
        image_family=args.image_family,
        image_project=args.image_project,
        tags=tag_client,
    )
    create_instance_if_missing(
        vm_diff_server,
        zone=args.zone1,
        machine_type=args.machine_type,
        image_family=args.image_family,
        image_project=args.image_project,
        tags=tag_server,
    )
    create_instance_if_missing(
        vm_diff_client,
        zone=args.zone2,
        machine_type=args.machine_type,
        image_family=args.image_family,
        image_project=args.image_project,
        tags=tag_client,
    )

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