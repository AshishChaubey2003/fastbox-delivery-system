"""
Test runner for the FastBox Delivery System.
Runs the simulation against the base case and all 10 test cases,
and verifies key properties of the output.
"""

import json
import os
import sys
import math

# Add parent dir to path so we can import delivery_system
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from delivery_system import run_simulation, load_data, euclidean


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_report(report: dict, packages: list, agents: dict) -> list:
    """
    Check the report for correctness.  Returns a list of error strings
    (empty = all OK).
    """
    errors = []

    # All agent keys (excluding 'best_agent') must be present
    agent_ids = set(agents.keys())
    report_agent_ids = {k for k in report if k != "best_agent"}

    missing = agent_ids - report_agent_ids
    if missing:
        errors.append(f"Missing agents in report: {missing}")

    # Total packages delivered must equal total packages in input
    total_delivered = sum(
        v["packages_delivered"]
        for k, v in report.items()
        if k != "best_agent"
    )
    if total_delivered != len(packages):
        errors.append(
            f"Package count mismatch: delivered={total_delivered}, "
            f"expected={len(packages)}"
        )

    # best_agent must be one of the agents
    if report.get("best_agent") not in agent_ids:
        errors.append(f"best_agent '{report.get('best_agent')}' not in agents")

    # efficiency = total_distance / packages_delivered
    for aid, stats in report.items():
        if aid == "best_agent":
            continue
        if stats["packages_delivered"] > 0:
            expected_eff = round(
                stats["total_distance"] / stats["packages_delivered"], 4
            )
            if abs(stats["efficiency"] - expected_eff) > 0.01:
                errors.append(
                    f"{aid}: efficiency {stats['efficiency']} != "
                    f"expected {expected_eff}"
                )

    return errors


# ---------------------------------------------------------------------------
# Run all cases
# ---------------------------------------------------------------------------

def run_all():
    test_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_cases"
    )
    base_case = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "base_case.json"
    )

    cases = [("base_case", base_case)]
    for i in range(1, 11):
        path = os.path.join(test_dir, f"test_case_{i}.json")
        if os.path.exists(path):
            cases.append((f"test_case_{i}", path))

    passed = 0
    failed = 0

    for name, path in cases:
        print(f"\n{'='*60}")
        print(f"  Running: {name}")
        print(f"{'='*60}")

        out_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "outputs", name
        )

        try:
            report = run_simulation(
                input_path=path,
                output_dir=out_dir,
                delay_simulation=False,  # deterministic for testing
                show_ascii=True,
            )

            # Load original data for validation
            data = load_data(path)
            errors = validate_report(report, data["packages"], data["agents"])

            if errors:
                print(f"\n[FAIL] {name}:")
                for e in errors:
                    print(f"  ✗ {e}")
                failed += 1
            else:
                print(f"\n[PASS] {name} ✓")
                passed += 1

        except Exception as exc:
            import traceback
            print(f"\n[ERROR] {name}: {exc}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
