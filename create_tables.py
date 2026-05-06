import re
import yaml
from pathlib import Path

PAPER_DIR_TMP = Path("paper/tmp")
PAPER_DIR_BASE = Path(__file__).parent / "paper"
GEN_SYNTHETIC_CONFIG = PAPER_DIR_BASE.parent / "generator-synthetic-apps/config/alibaba2021.yaml"


APP2_ORDER = [
    "Digota",
    "EShopMicroservices",
    "SockShop",
    "PostNotification",
    "SocialNetwork",
    "MediaMicroservices",
    "TrainTicket",
]

DETECTION_TO_DISPLAY = {
    "digota":                "Digota",
    "eshopmicroservices":    "EShopMicroservices",
    "sockshop":              "SockShop",
    "postnotification":      "PostNotification",
    "dsb_socialnetwork":     "SocialNetwork",
    "dsb_mediamicroservices": "MediaMicroservices",
    "trainticket":           "TrainTicket",
}

SYNTH_PURPOSE = {
    "App 1": "Median",
    "App 2": "p90 #DS",
    "App 3": "p90 CD",
    "App 4": "p90 FO",
    "App 5": "p90 #CG",
}


def parse_table2_metrics():
    data = {}
    for line in (PAPER_DIR_TMP / "table2_real_metrics.txt").read_text().splitlines():
        line = line.strip()
        if not line or "#MS" in line or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) >= 6:
            def parse_int(v):
                try:
                    return int(v)
                except ValueError:
                    return None
            data[parts[0]] = {
                "ms":   parse_int(parts[1]),
                "ds":   parse_int(parts[2]),
                "locs": parse_int(parts[3]),
                "rpcs": parse_int(parts[4]),
                "cgs":  parse_int(parts[5]),
            }
    return data


def parse_table2_memory():
    data = {}
    for line in (PAPER_DIR_TMP / "table2_real_memory.txt").read_text().splitlines():
        line = line.strip()
        if not line or "Avg." in line or line.startswith("-"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                data[parts[0]] = int(parts[1])
            except ValueError:
                pass
    return data


def parse_table2_detection():
    data = {}
    total = {}
    precision = recall = None
    for line in (PAPER_DIR_TMP / "table2_real_detection.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("-") or line.startswith("App"):
            continue
        parts = line.split()
        # parts: [label, RI-1, RI-2, RI-3, EI-1, Un-1, |, TP, FP, FN]
        if len(parts) >= 10 and parts[6] == "|":
            entry = {
                "ri1": int(parts[1]),
                "ri2": int(parts[2]),
                "ri3": int(parts[3]),
                "ei1": int(parts[4]),
                "un1": int(parts[5]),
                "tp":  int(parts[7]),
                "fp":  int(parts[8]),
                "fn":  int(parts[9]),
            }
            if parts[0] == "TOTAL":
                total = entry
            else:
                display = DETECTION_TO_DISPLAY.get(parts[0], parts[0])
                data[display] = entry
        elif line.startswith("Precision:"):
            precision = line.split(":", 1)[1].strip()
        elif line.startswith("Recall:"):
            recall = line.split(":", 1)[1].strip()
    return data, total, precision, recall


def parse_table3_metrics():
    data = {}
    p = PAPER_DIR_TMP / "table3_synth_metrics.txt"
    if not p.exists():
        print(f"[WARNING] {p} not found, skipping table3 metrics")
        return data
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or "#MS" in line or line.startswith("-"):
            continue
        m = re.match(r"(App\s+\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if m:
            data[m.group(1)] = {
                "ms":   int(m.group(2)),
                "ds":   int(m.group(3)),
                "rpcs": int(m.group(4)),
                "cgs":  int(m.group(5)),
            }
    return data


def parse_table3_memory():
    data = {}
    p = PAPER_DIR_TMP / "table3_synth_memory.txt"
    if not p.exists():
        print(f"[WARNING] {p} not found, skipping table3 memory")
        return data
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or "Avg." in line or line.startswith("-"):
            continue
        m = re.match(r"(App\s+\d+)\s+([\d.]+)", line)
        if m:
            data[m.group(1)] = float(m.group(2))
    return data


def parse_synth_config():
    with open(GEN_SYNTHETIC_CONFIG) as f:
        configs = yaml.safe_load(f)
    data = {}
    for i, app in enumerate(configs, 1):
        data[f"App {i}"] = {
            "cd": app["call_depth"],
            "fo": app["fanout"],
        }
    return data


def format_table(cols, rows, separators=None, footer_rows=None, summary=None):
    if separators is None:
        separators = set()

    widths = [len(c) for c in cols]
    for row in (rows + (footer_rows or [])):
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    def join_row(values):
        result = ""
        for i, (val, w) in enumerate(zip(values, widths)):
            result += str(val).ljust(w)
            if i < len(values) - 1:
                result += " | " if i in separators else "  "
        return result

    def make_sep():
        result = ""
        for i, w in enumerate(widths):
            result += "-" * w
            if i < len(widths) - 1:
                result += "-|-" if i in separators else "--"
        return result

    sep = make_sep()
    lines = [join_row(cols), sep]
    for row in rows:
        lines.append(join_row(row))
    if footer_rows:
        lines.append(sep)
        for row in footer_rows:
            lines.append(join_row(row))
    if summary:
        lines.append("")
        lines.extend(summary)
    return "\n".join(lines)


def build_table2():
    metrics                     = parse_table2_metrics()
    memory                      = parse_table2_memory()
    detection, total, prec, rec = parse_table2_detection()

    cols = ["Name", "#MS", "#DS", "#LoCs", "#RPCs", "#CGs", "Mem.", "RI-1", "RI-2", "RI-3", "EI-1", "Un-1", "TP", "FP", "FN"]
    # vertical bars after: #CGs (5), Mem. (6), Un-1 (11)
    separators = {5, 6, 11}

    rows = []
    for app in APP2_ORDER:
        m = metrics.get(app, {})
        d = detection.get(app, {})
        mem = memory.get(app)
        rows.append([
            app,
            m.get("ms")   if m.get("ms")   is not None else "N/A",
            m.get("ds")   if m.get("ds")   is not None else "N/A",
            m.get("locs") if m.get("locs") is not None else "N/A",
            m.get("rpcs") if m.get("rpcs") is not None else "N/A",
            m.get("cgs")  if m.get("cgs")  is not None else "N/A",
            f"{mem} MB" if mem is not None else "N/A",
            d.get("ri1",  "?"),
            d.get("ri2",  "?"),
            d.get("ri3",  "?"),
            d.get("ei1",  "?"),
            d.get("un1",  "?"),
            d.get("tp",   "?"),
            d.get("fp",   "?"),
            d.get("fn",   "?"),
        ])

    summary = []
    if total:
        summary.append(f"Total TP: {total.get('tp', '?')}")
        summary.append(f"Total FP: {total.get('fp', '?')}")
        summary.append(f"Total FN: {total.get('fn', '?')}")
    if prec:
        summary.append(f"Precision: {prec}")
    if rec:
        summary.append(f"Recall:    {rec}")

    return format_table(cols, rows, separators=separators, summary=summary or None)


def build_table3():
    metrics = parse_table3_metrics()
    memory  = parse_table3_memory()
    config  = parse_synth_config()

    cols = ["#", "Purpose", "CD", "FO", "#DS", "#MS", "#CG", "Mem"]
    # vertical bar after: # (0)
    separators = {0}
    rows = []
    for i in range(1, 6):
        app = f"App {i}"
        m   = metrics.get(app, {})
        mem = memory.get(app)
        cfg = config.get(app, {})
        mem_str = f"{mem:.2f} GB" if mem is not None else "N/A"
        rows.append([
            app,
            SYNTH_PURPOSE.get(app, "?"),
            cfg.get("cd", "?"),
            cfg.get("fo", "?"),
            m.get("ds",  "?"),
            m.get("ms",  "?"),
            m.get("cgs", "?"),
            mem_str,
        ])
    return format_table(cols, rows, separators=separators)


if __name__ == "__main__":
    table2 = build_table2()
    print("Table 2: Real-World Applications\n")
    print(table2)
    (PAPER_DIR_BASE / "table2-realistic-apps.txt").write_text(table2 + "\n")
    print(f"\n[INFO] saved table 2 in {PAPER_DIR_BASE / 'table2.txt'}")

    print()

    table3 = build_table3()
    print("Table 3: Synthetic Applications\n")
    print(table3)
    (PAPER_DIR_BASE / "table3-synthetic-apps.txt").write_text(table3 + "\n")
    print(f"\n[INFO] saved table 3 in {PAPER_DIR_BASE / 'table3-synthetic-apps.txt'}")
