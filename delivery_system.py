"""
FastBox Delivery System Simulator
==================================
Simulates one day of logistics operations:
  - Reads input data (warehouses, agents, packages) from a JSON file
  - Assigns each package to the nearest agent (by Euclidean distance to warehouse)
  - Simulates delivery: agent → warehouse → destination
  - Computes total distance per agent and efficiency (distance / packages)
  - Determines the most efficient (lowest distance-per-package) agent
  - Outputs a report.json and optionally a CSV of top performers

Supports two JSON input formats:
  Format A (dict-based):  {"warehouses": {"W1": [x, y], ...}, "agents": {...}, "packages": [...]}
  Format B (list-based):  {"warehouses": [{"id": "W1", "location": [x, y]}, ...], ...}
"""

import json
import math
import csv
import sys
import os
import random
from typing import Union


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def euclidean(p1: list, p2: list) -> float:
    """Return the Euclidean distance between two 2-D points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# ---------------------------------------------------------------------------
# Data loading  (handles both JSON formats)
# ---------------------------------------------------------------------------

def load_data(filepath: str) -> dict:
    """
    Load and normalise the JSON input file.

    Always returns a dict with:
        warehouses : {id: [x, y]}
        agents     : {id: [x, y]}
        packages   : [{"id": ..., "warehouse_id": ..., "destination": [...]}]
    """
    with open(filepath, "r") as f:
        raw = json.load(f)

    # ---- warehouses ----
    if isinstance(raw["warehouses"], dict):
        # Format A: {"W1": [x, y], ...}
        warehouses = {wid: loc for wid, loc in raw["warehouses"].items()}
    else:
        # Format B: [{"id": "W1", "location": [x, y]}, ...]
        warehouses = {w["id"]: w["location"] for w in raw["warehouses"]}

    # ---- agents ----
    if isinstance(raw["agents"], dict):
        agents = {aid: loc for aid, loc in raw["agents"].items()}
    else:
        agents = {a["id"]: a["location"] for a in raw["agents"]}

    # ---- packages ----
    packages = []
    for pkg in raw["packages"]:
        packages.append({
            "id": pkg["id"],
            # support both "warehouse" and "warehouse_id" keys
            "warehouse_id": pkg.get("warehouse_id") or pkg.get("warehouse"),
            "destination": pkg["destination"],
        })

    return {"warehouses": warehouses, "agents": agents, "packages": packages}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def assign_packages(packages: list, agents: dict, warehouses: dict) -> dict:
    """
    Assign each package to the nearest agent.

    'Nearest' is measured from the agent's current position to the
    warehouse that holds the package (first leg of the journey).

    Returns:
        agent_packages: {agent_id: [pkg, ...]}
    """
    agent_packages = {aid: [] for aid in agents}

    for pkg in packages:
        warehouse_loc = warehouses[pkg["warehouse_id"]]

        # Find the agent with minimum distance to this package's warehouse
        nearest_agent = min(
            agents.keys(),
            key=lambda aid: euclidean(agents[aid], warehouse_loc)
        )

        agent_packages[nearest_agent].append(pkg)
        print(f"  Package {pkg['id']} (warehouse {pkg['warehouse_id']}) → assigned to {nearest_agent}")

    return agent_packages


def simulate_deliveries(
    agent_packages: dict,
    agents: dict,
    warehouses: dict,
    delay_simulation: bool = False
) -> dict:
    """
    Simulate the delivery journey for every agent.

    Journey per package:
        agent_start → warehouse → destination

    If delay_simulation is True, a random delay (0–30 min) is added to
    each package delivery (bonus feature).

    Returns:
        results: {agent_id: {"packages_delivered": int,
                              "total_distance": float,
                              "efficiency": float,
                              "deliveries": [...]}}
    """
    results = {}

    for aid, pkgs in agent_packages.items():
        agent_start = agents[aid]
        total_dist = 0.0
        deliveries = []

        # Current position of the agent (updated after each delivery)
        current_pos = list(agent_start)

        for pkg in pkgs:
            warehouse_loc = warehouses[pkg["warehouse_id"]]
            destination = pkg["destination"]

            # Leg 1: agent travels from current position to warehouse
            leg1 = euclidean(current_pos, warehouse_loc)
            # Leg 2: agent travels from warehouse to destination
            leg2 = euclidean(warehouse_loc, destination)

            pkg_distance = leg1 + leg2
            total_dist += pkg_distance

            # Optional bonus: random delay in minutes (0–30)
            delay = random.randint(0, 30) if delay_simulation else 0

            deliveries.append({
                "package_id": pkg["id"],
                "warehouse": pkg["warehouse_id"],
                "destination": destination,
                "distance_traveled": round(pkg_distance, 4),
                "delay_minutes": delay,
            })

            # Agent is now at the destination after delivering
            current_pos = destination

        pkg_count = len(pkgs)
        # Efficiency = average distance per package (lower = more efficient)
        efficiency = round(total_dist / pkg_count, 4) if pkg_count > 0 else 0.0

        results[aid] = {
            "packages_delivered": pkg_count,
            "total_distance": round(total_dist, 4),
            "efficiency": efficiency,
            "deliveries": deliveries,
        }

    return results


def find_best_agent(results: dict) -> str:
    """
    Return the agent ID with the lowest efficiency score
    (i.e. least average distance per package).
    Agents with zero deliveries are excluded.
    """
    active = {aid: r for aid, r in results.items() if r["packages_delivered"] > 0}
    if not active:
        return None
    return min(active.keys(), key=lambda aid: active[aid]["efficiency"])


# ---------------------------------------------------------------------------
# ASCII route visualiser (bonus)
# ---------------------------------------------------------------------------

def ascii_visualise(agents: dict, warehouses: dict, agent_packages: dict,
                    width: int = 60, height: int = 30) -> str:
    """
    Render an ASCII map showing warehouses (W), agents (A),
    and delivery destinations (d).
    """
    # Collect all coordinates to compute bounding box
    all_coords = list(warehouses.values()) + list(agents.values())
    for pkgs in agent_packages.values():
        for pkg in pkgs:
            all_coords.append(pkg["destination"])

    min_x = min(c[0] for c in all_coords)
    max_x = max(c[0] for c in all_coords)
    min_y = min(c[1] for c in all_coords)
    max_y = max(c[1] for c in all_coords)

    # Avoid division by zero for degenerate cases
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    def to_grid(x, y):
        col = int((x - min_x) / span_x * (width - 1))
        row = int((y - min_y) / span_y * (height - 1))
        return row, col

    # Build blank grid
    grid = [["." for _ in range(width)] for _ in range(height)]

    # Plot destinations
    for pkgs in agent_packages.values():
        for pkg in pkgs:
            r, c = to_grid(*pkg["destination"])
            grid[r][c] = "d"

    # Plot warehouses (override destinations)
    for wid, loc in warehouses.items():
        r, c = to_grid(*loc)
        grid[r][c] = "W"

    # Plot agents (highest priority)
    for aid, loc in agents.items():
        r, c = to_grid(*loc)
        grid[r][c] = "A"

    lines = ["FastBox Route Map", "-" * width]
    for row in reversed(grid):          # flip so y increases upward
        lines.append("".join(row))
    lines.append("-" * width)
    lines.append("A=Agent  W=Warehouse  d=destination  .=empty")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_report(results: dict, best_agent: str) -> dict:
    """
    Build the final report dictionary matching the required output schema.
    """
    report = {}
    for aid, data in results.items():
        report[aid] = {
            "packages_delivered": data["packages_delivered"],
            "total_distance": data["total_distance"],
            "efficiency": data["efficiency"],
        }
    report["best_agent"] = best_agent
    return report


def save_report(report: dict, output_path: str) -> None:
    """Save the report dictionary to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)
    print(f"\nReport saved → {output_path}")


def export_top_performers_csv(results: dict, best_agent: str,
                               csv_path: str) -> None:
    """
    Bonus: Export all agent stats to a CSV file, with the best agent
    marked in a dedicated column.
    """
    fieldnames = ["agent_id", "packages_delivered", "total_distance",
                  "efficiency", "is_top_performer"]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for aid, data in results.items():
            writer.writerow({
                "agent_id": aid,
                "packages_delivered": data["packages_delivered"],
                "total_distance": data["total_distance"],
                "efficiency": data["efficiency"],
                "is_top_performer": "YES" if aid == best_agent else "NO",
            })
    print(f"CSV exported   → {csv_path}")


# ---------------------------------------------------------------------------
# Bonus: new agent joins mid-day
# ---------------------------------------------------------------------------

def add_agent_mid_day(agents: dict, new_id: str, location: list,
                      agent_packages: dict) -> None:
    """
    Bonus: Register a new agent that joins mid-day.
    The agent starts with no packages but is added to the roster
    so it appears (with 0 deliveries) in the final report.
    """
    agents[new_id] = location
    agent_packages[new_id] = []
    print(f"\n[MID-DAY] New agent {new_id} joined at {location} with no packages.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_simulation(input_path: str, output_dir: str = ".",
                   delay_simulation: bool = False,
                   mid_day_agent: Union[dict, None] = None,
                   show_ascii: bool = True) -> dict:
    """
    Full simulation pipeline.

    Args:
        input_path      : Path to the input JSON file.
        output_dir      : Directory where report.json and top_performers.csv are saved.
        delay_simulation: If True, add random delays to deliveries (bonus).
        mid_day_agent   : Optional dict {"id": "A_NEW", "location": [x, y]} (bonus).
        show_ascii      : If True, print ASCII route map (bonus).

    Returns:
        The final report dict.
    """
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  FastBox Delivery System Simulator")
    print("=" * 60)

    # 1. Load data
    print(f"\n[1] Loading data from: {input_path}")
    data = load_data(input_path)
    warehouses = data["warehouses"]
    agents = data["agents"]
    packages = data["packages"]
    print(f"    Warehouses : {list(warehouses.keys())}")
    print(f"    Agents     : {list(agents.keys())}")
    print(f"    Packages   : {[p['id'] for p in packages]}")

    # Bonus: new agent joins mid-day (before assignment so it can be considered)
    if mid_day_agent:
        add_agent_mid_day(agents, mid_day_agent["id"], mid_day_agent["location"],
                          {})  # temp placeholder; handled inside assign step

    # 2. Assign packages
    print("\n[2] Assigning packages to nearest agents …")
    agent_packages = assign_packages(packages, agents, warehouses)

    # Bonus: ensure mid-day agent appears in assignment dict even if empty
    if mid_day_agent and mid_day_agent["id"] not in agent_packages:
        agent_packages[mid_day_agent["id"]] = []

    # 3. Simulate deliveries
    print("\n[3] Simulating deliveries …")
    results = simulate_deliveries(agent_packages, agents, warehouses,
                                  delay_simulation=delay_simulation)

    # 4. Determine best agent
    best_agent = find_best_agent(results)
    print(f"\n[4] Best agent: {best_agent}")

    # 5. ASCII visualisation (bonus)
    if show_ascii:
        print("\n[BONUS] ASCII Route Map:")
        print(ascii_visualise(agents, warehouses, agent_packages))

    # 6. Build & save report
    report = build_report(results, best_agent)
    report_path = os.path.join(output_dir, "report.json")
    detailed_path = os.path.join(output_dir, "report_detailed.json")
    save_report(report, report_path)

    # Save detailed report (with per-delivery breakdown)
    detailed = {aid: results[aid] for aid in results}
    detailed["best_agent"] = best_agent
    with open(detailed_path, "w") as f:
        json.dump(detailed, f, indent=4)
    print(f"Detailed report→ {detailed_path}")

    # 7. Bonus: export CSV
    csv_path = os.path.join(output_dir, "top_performers.csv")
    export_top_performers_csv(results, best_agent, csv_path)

    # 8. Print summary table
    print("\n" + "=" * 60)
    print("  FINAL REPORT SUMMARY")
    print("=" * 60)
    print(f"{'Agent':<10} {'Packages':>10} {'Distance':>14} {'Efficiency':>12}")
    print("-" * 50)
    for aid in sorted(results.keys()):
        r = results[aid]
        marker = " ★" if aid == best_agent else ""
        print(f"{aid:<10} {r['packages_delivered']:>10} "
              f"{r['total_distance']:>14.4f} {r['efficiency']:>12.4f}{marker}")
    print("-" * 50)
    print(f"Best agent: {best_agent}  (lowest avg distance per package)")
    print("=" * 60)

    return report


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Default to base_case.json if no argument provided
    input_file = sys.argv[1] if len(sys.argv) > 1 else "base_case.json"
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "output"

    # Optional bonus features (uncomment to enable):
    # mid_day = {"id": "A_NEW", "location": [50, 50]}
    mid_day = None

    run_simulation(
        input_path=input_file,
        output_dir=output_directory,
        delay_simulation=True,   # bonus: random delays
        mid_day_agent=mid_day,   # bonus: new agent mid-day
        show_ascii=True,         # bonus: ASCII map
    )
