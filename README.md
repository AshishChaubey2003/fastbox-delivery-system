# 📦 FastBox Delivery System Simulator

A Python-based logistics simulator for the **FastBox** delivery company.  
Simulates one day of operations — assigning packages to agents, computing distances, and generating a delivery report.

---

## 📁 Project Structure

```
fastbox_delivery_system/
├── delivery_system.py       # Main simulator (core logic)
├── run_tests.py             # Test runner for all 10 test cases
├── base_case.json           # Sample input data
└── test_cases/
    ├── test_case_1.json
    ├── test_case_2.json
    └── ... (up to test_case_10.json)
```

---

## ✅ Requirements

- **Python 3.x** (no external libraries needed)
- Only uses built-in modules: `json`, `math`, `csv`, `os`, `random`, `sys`

Check your Python version:
```bash
python3 --version
```

---

## 🚀 How to Run

### Option 1 — Run on the base case
```bash
python3 delivery_system.py base_case.json output/
```

### Option 2 — Run on any test case
```bash
python3 delivery_system.py test_cases/test_case_1.json output/test1/
```

### Option 3 — Run all 10 test cases at once
```bash
python3 run_tests.py
```

---

## 📤 Output Files

After running, an output folder is created containing:

| File | Description |
|------|-------------|
| `report.json` | Final report: packages delivered, total distance, efficiency, best agent |
| `report_detailed.json` | Same as above + per-package delivery breakdown |
| `top_performers.csv` | All agents ranked; best performer marked |

### Sample `report.json`
```json
{
    "A1": {
        "packages_delivered": 2,
        "total_distance": 121.2132,
        "efficiency": 60.6066
    },
    "A2": {
        "packages_delivered": 2,
        "total_distance": 79.2081,
        "efficiency": 39.604
    },
    "A3": {
        "packages_delivered": 1,
        "total_distance": 14.1421,
        "efficiency": 14.1421
    },
    "best_agent": "A3"
}
```

---

## 🧠 How It Works

1. **Reads** the JSON input file (supports both dict and list formats)
2. **Assigns** each package to the nearest agent (Euclidean distance from agent → warehouse)
3. **Simulates** delivery: agent travels `current position → warehouse → destination`
4. **Calculates** total distance and efficiency per agent
5. **Generates** `report.json` and prints a summary table

---

## 🎁 Bonus Features

| Feature | How to Enable |
|--------|---------------|
| Random delivery delays | Set `delay_simulation=True` in `run_simulation()` |
| ASCII route map | Set `show_ascii=True` (enabled by default) |
| New agent joins mid-day | Pass `mid_day_agent={"id": "A_NEW", "location": [x, y]}` |
| CSV export | Auto-generated as `top_performers.csv` |

---

## 📥 Input Format

The simulator supports **two JSON formats**:

**Format A (dict-based):**
```json
{
  "warehouses": { "W1": [0, 0], "W2": [50, 75] },
  "agents":     { "A1": [5, 5], "A2": [60, 60] },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

**Format B (list-based):**
```json
{
  "warehouses": [{ "id": "W1", "location": [0, 0] }],
  "agents":     [{ "id": "A1", "location": [5, 5] }],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
}
```

---

## 🧪 Test Results

All 11 cases (base case + 10 test cases) pass validation:
- ✅ Total packages delivered = total packages in input
- ✅ Efficiency = total_distance / packages_delivered
- ✅ best_agent is always a valid agent ID

---

*Assignment: Python Assignment 2026 — Mystery Delivery System*
