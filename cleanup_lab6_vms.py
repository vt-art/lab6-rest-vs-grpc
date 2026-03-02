#!/usr/bin/env python3
"""
Delete lab6 VMs and firewall rules safely.

Usage:
  python3 cleanup_lab6_vms.py --project lab6-488919
  python3 cleanup_lab6_vms.py --project lab6-488919 --yes
"""

from __future__ import annotations
import argparse
import subprocess
import shlex
import sys


def run(cmd, check=True, capture=False):
    print("$", " ".join(shlex.quote(c) for c in cmd))
    return subprocess.run(cmd, check=check, text=True, capture_output=capture)


def exists_instance(name, zone):
    cp = run(
        ["gcloud", "compute", "instances", "describe", name, f"--zone={zone}"],
        check=False,
        capture=True,
    )
    return cp.returncode == 0


def delete_instance(name, zone):
    if exists_instance(name, zone):
        run(
            [
                "gcloud",
                "compute",
                "instances",
                "delete",
                name,
                f"--zone={zone}",
                "--quiet",
            ]
        )
    else:
        print(f"VM not found (skipping): {name} ({zone})")


def exists_firewall_rule(name):
    cp = run(
        ["gcloud", "compute", "firewall-rules", "describe", name],
        check=False,
        capture=True,
    )
    return cp.returncode == 0


def delete_firewall_rule(name):
    if exists_firewall_rule(name):
        run(
            [
                "gcloud",
                "compute",
                "firewall-rules",
                "delete",
                name,
                "--quiet",
            ]
        )
    else:
        print(f"Firewall rule not found (skipping): {name}")


def main():
    parser = argparse.ArgumentParser(description="Delete lab6 VMs + firewall rules")
    parser.add_argument("--project", required=True, help="GCP project id")
    parser.add_argument("--zone1", default="us-central1-a")
    parser.add_argument("--zone2", default="europe-west3-a")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    run(["gcloud", "config", "set", "project", args.project])

    vms = [
        ("lab6-local", args.zone1),
        ("lab6-samezone-server", args.zone1),
        ("lab6-samezone-client", args.zone1),
        ("lab6-diffregion-server", args.zone2),
        ("lab6-diffregion-client", args.zone1),
    ]

    firewall_rules = [
        "allow-lab6-rest-5000",
        "allow-lab6-grpc-50051",
        "allow-lab6-icmp",
    ]

    if not args.yes:
        print("\nThis will DELETE the following VMs:")
        for name, zone in vms:
            print(f"  - {name} ({zone})")

        print("\nAnd DELETE these firewall rules:")
        for rule in firewall_rules:
            print(f"  - {rule}")

        confirm = input("\nType 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("Aborted.")
            sys.exit(0)

    print("\n=== Deleting VMs ===")
    for name, zone in vms:
        delete_instance(name, zone)

    print("\n=== Deleting Firewall Rules ===")
    for rule in firewall_rules:
        delete_firewall_rule(rule)

    print("\nCleanup complete.")


if __name__ == "__main__":
    main()