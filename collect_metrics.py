import os
import subprocess
import yaml
from pathlib import Path
from collections import defaultdict
import argparse
from datetime import date
import time

parser = argparse.ArgumentParser()
parser.add_argument("--synthetic", action="store_true", help="enable evaluation mode")
parser.add_argument("--date", type=str, default=str(date.today()), help="date in YYYY-MM-DD format (default: today)")
args = parser.parse_args()

unix_ts = int(time.time())

PAPER_DIR_BASE = Path("paper/tmp")
PAPER_DIR_BASE.mkdir(parents=True, exist_ok=True)

os.makedirs("results", exist_ok=True)
os.makedirs("results/versions", exist_ok=True)

do_get_locs = not args.synthetic
do_get_rpcs = True

if args.synthetic:
    INPUT_DIR = f"aletheia/eval/metrics/{args.date}/synthetic"
else:
    INPUT_DIR = f"aletheia/eval/metrics/{args.date}/realistic"

print(f"[INFO] collecting all metric results in: {INPUT_DIR}/")

if args.synthetic and not os.path.isdir(INPUT_DIR):
    print(f"[WARNING] synthetic results not available at {INPUT_DIR}, skipping...\n")
    exit(0)

if args.synthetic:
    OUTPUT_FILE1 = f"results/metrics-synthetic.yaml"
    OUTPUT_FILE2 = f"results/versions/metrics-synthetic-{unix_ts}.yaml"
else:
    OUTPUT_FILE1 = f"results/metrics-realistic.yaml"
    OUTPUT_FILE2 = f"results/versions/metrics-realistic-{unix_ts}.yaml"

APP_ORDER = [
    "digota",
    "eshopmicroservices",
    "sockshop",
    "postnotification",
    "dsb_socialnetwork",
    "dsb_mediamicroservices",
    "trainticket",
]

NAME_MAP = {
    "dsb_mediamicroservices":   "MediaMicroservices",
    "dsb_socialnetwork":        "SocialNetwork",
    "postnotification":         "PostNotification",
    "sockshop":                 "SockShop",
    "trainticket":              "TrainTicket",
    "eshopmicroservices":       "EShopMicroservices",
    "digota":                   "Digota",
    "synthetic_app1":           "App 1",
    "synthetic_app2":           "App 2",
    "synthetic_app3":           "App 3",
    "synthetic_app4":           "App 4",
    "synthetic_app5":           "App 5",
    "synthetic_app6":           "App 6",
}

BLUEPRINT_EXAMPLES_DIR = "aletheia/blueprint/examples"

app_dir_map = {}
if not args.synthetic:
    with open("registry/apps_realistic.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    for app_cfg in cfg["apps"]:
        app_name = app_cfg["name"]
        app_dir = app_cfg["package_path"].split("/")[0]
        app_dir_map[app_name] = app_dir

def get_loc(app_name):
    app_dir = app_dir_map.get(app_name)
    if not app_dir:
        return None
    path = os.path.join(BLUEPRINT_EXAMPLES_DIR, app_dir, "workflow")
    if not os.path.isdir(path):
        return None
    try:
        out = subprocess.check_output(["cloc", "."], cwd=path, stderr=subprocess.DEVNULL, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for line in out.splitlines():
        if line.startswith("Go"):
            parts = line.split()
            return int(parts[-1])
    return None

apps_data = defaultdict(list)
for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".yaml"):
        continue
    path = os.path.join(INPUT_DIR, filename)

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if "app" in data:
        key = (data["app"], data["ms_count"], data["ds_count"], data["callgraphs"])
        apps_data[key].append(data)

results = {}
for (app, ms_count, ds_count, callgraphs), entries in apps_data.items():
    avg = {}
    n = len(entries)

    for key, value in entries[0].items():
        if key == "app": # skip non-numeric
            continue

        # if the value is numeric, then average it
        if isinstance(value, (int, float)):
            avg[key] = sum(entry[key] for entry in entries) / n
        else:
            # keep the value as-is (e.g., ms_count, ds_count always same)
            avg[key] = value

    # add the app name back
    avg["app"] = app
    avg["ms_count"] = ms_count
    avg["ds_count"] = ds_count
    avg["callgraphs"] = callgraphs
    results[(app, ms_count, ds_count, callgraphs)] = avg

weights = {
    "ms_weight": 1.0,
    "ds_weight": 1.0,
}

ordered_results = []
for (app, ms_count, ds_count, callgraphs), avg in results.items():
    final_name = NAME_MAP.get(app, app)

    entry = {
        "app":          final_name,
        "iterations":   len(apps_data[(app, ms_count, ds_count, callgraphs)]),
        "ms_count":     int(avg["ms_count"]),
        "ds_count":     int(avg["ds_count"]),
        # Synthetic apps include one simple extra delete-only request used to trigger
        # a cascade-delete warning, so we exclude it from the reported count
        "callgraphs":   int(avg["callgraphs"]) - (1 if args.synthetic else 0),
        "rpcs":         int(avg["rpcs"]),
        "total_s":      float(f"{avg['total_s']:.2f}"),
        "parsing_s":    float(f"{avg['parsing_s']:.2f}"),
        "schema_s":     float(f"{avg['schema_s']:.4f}"),
        "detection_s":  float(f"{avg['detection_s']:.4f}"),
    }
    if do_get_locs:
        entry["loc"] = get_loc(app)
    ordered_results.append(entry)

ordered_results = sorted(ordered_results, key=lambda x: x["app"])

with open(OUTPUT_FILE1, "w") as out:
    yaml.dump({"weights": weights}, out, sort_keys=False)
    out.write("\n")

    out.write("apps:\n")
    for entry in ordered_results:
        yaml.dump([entry], out, sort_keys=False)
        out.write("\n")

print(f"[INFO] saved averaged results to {OUTPUT_FILE1}")

with open(OUTPUT_FILE2, "w") as out:
    yaml.dump({"weights": weights}, out, sort_keys=False)
    out.write("\n")

    out.write("apps:\n")
    for entry in ordered_results:
        yaml.dump([entry], out, sort_keys=False)
        out.write("\n")

print(f"[INFO] saved averaged results to {OUTPUT_FILE2}")

_app_display_order = [NAME_MAP.get(k, k) for k in APP_ORDER]
paper_results = sorted(ordered_results, key=lambda x: _app_display_order.index(x["app"]) if x["app"] in _app_display_order else len(_app_display_order))
col_w = max(len(e["app"]) for e in paper_results)
header = f"  {'App':<{col_w}}  {'#MS':>4}  {'#DS':>4}"
if do_get_locs:
    header += f"  {'#LoCs':>8}"
if do_get_rpcs:
    header += f"  {'#RPCs':>5}"
header += f"  {'#CGs':>10}"
sep = "  " + "-" * (len(header) - 2)
lines = ["", header, sep]
for e in paper_results:
    row = f"  {e['app']:<{col_w}}  {e['ms_count']:>4}  {e['ds_count']:>4}"
    if do_get_locs:
        loc_val = e.get("loc")
        row += f"  {loc_val if loc_val is not None else 'N/A':>8}"
    if do_get_rpcs:
        row += f"  {e['rpcs']:>5}"
    row += f"  {e['callgraphs']:>10}"
    lines.append(row)
lines.append("")
output = "\n".join(lines)

if args.synthetic:
    filepath = PAPER_DIR_BASE / "table3_synth_metrics.txt"
else:
    filepath = PAPER_DIR_BASE / "table2_real_metrics.txt"
with open(filepath, "w") as f:
    f.write(output + "\n")
print(f"[INFO] saved to {filepath}\n")
