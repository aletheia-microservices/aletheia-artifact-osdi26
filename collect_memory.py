import re
import argparse
import sys
import time
from datetime import date
from pathlib import Path
from collections import defaultdict

PAPER_DIR_BASE = Path("paper/tmp")
PAPER_DIR_BASE.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_BASE = Path("results")
OUTPUT_DIR_BASE.mkdir(exist_ok=True)
VERSIONS_DIR = OUTPUT_DIR_BASE / "versions"
VERSIONS_DIR.mkdir(exist_ok=True)


PATTERN_MAC = re.compile(r"(\d+)\s+maximum resident set size")
PATTERN_LINUX = re.compile(r"Maximum resident set size \(kbytes\):\s*(\d+)")

parser = argparse.ArgumentParser()
parser.add_argument("--synthetic", action="store_true", help="enable synthetic mode")
parser.add_argument("--date", type=str, default=str(date.today()), help="date in YYYY-MM-DD format (default: today)")
args = parser.parse_args()

INPUT_DIR = Path(f"aletheia/eval/memory/{args.date}")
if args.synthetic:
    INPUT_DIR = INPUT_DIR / "synthetic"
else:
    INPUT_DIR = INPUT_DIR / "realistic"

print(f"[INFO] collecting all memory results in: {INPUT_DIR}/")

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

def extract_app_name(filename: str) -> str:
    return filename.split(".", 1)[0]

def extract_peak(path: Path):
    for line in path.read_text(errors="ignore").splitlines():
        m = PATTERN_MAC.search(line)
        if m:
            return int(m.group(1))  # bytes

        m = PATTERN_LINUX.search(line)
        if m:
            return int(m.group(1)) * 1024  # convert kbytes to bytes

    return None

def save(averaged, max_app_len):
    lines = []

    unit = "GB" if args.synthetic else "MB"
    header = f"\n{'App'.ljust(max_app_len)}   Avg. Peak Memory ({unit})"
    sep = "-" * (max_app_len + 26)
    lines.append(header)
    lines.append(sep)

    for app, avg in sorted(averaged, key=lambda x: APP_ORDER.index(x[0]) if x[0] in APP_ORDER else len(APP_ORDER)):
        final_app_name = NAME_MAP.get(app, app)
        if args.synthetic:
            lines.append(f"{final_app_name.ljust(max_app_len)}   {avg:.2f}")
        else:
            lines.append(f"{final_app_name.ljust(max_app_len)}   {int(avg)}")

    table_str = "\n".join(lines)

    unix_ts = int(time.time())

    filename_base = "memory-synthetic" if args.synthetic else "memory-realistic"

    with open(OUTPUT_DIR_BASE / f"{filename_base}.txt", "w") as f:
        f.write(table_str + "\n")

    with open(VERSIONS_DIR / f"{filename_base}-{unix_ts}.txt", "w") as f:
        f.write(table_str + "\n")

    if args.synthetic:
        paper_filepath = PAPER_DIR_BASE / "table3_synth_memory.txt"
    else:
        paper_filepath = PAPER_DIR_BASE / "table2_real_memory.txt"
    with open(paper_filepath, "w") as f:
        f.write(table_str + "\n")

    print(f"[INFO] saved to {paper_filepath}\n")

def main():
    if not INPUT_DIR.exists():
        if args.synthetic:
            print(f"[WARNING] synthetic results not available at {INPUT_DIR}, skipping...\n")
            sys.exit(0)
        print(f"[ERROR] directory not found: {INPUT_DIR}")
        sys.exit(1)

    # group values by app
    groups = defaultdict(list)

    for file in sorted(INPUT_DIR.iterdir()):
        if not file.is_file():
            continue

        peak = extract_peak(file)
        if peak is None:
            continue

        app = extract_app_name(file.name)
        if args.synthetic:
            groups[app].append(peak / 1024**3)  # GB
        else:
            groups[app].append(peak / 1024**2)  # MB

    averaged = [(app, sum(vals)/len(vals)) for app, vals in groups.items()]
    if not averaged:
        print(f"[WARNING] no memory results found in {INPUT_DIR}, skipping...\n")
        sys.exit(0)
    max_app_len = max(len(app) for app, _ in averaged)
    save(averaged, max_app_len)

if __name__ == "__main__":
    main()
