#!/usr/bin/env python3

import sys
import re
import os
import difflib

APPS = [
    "digota",
    "eshopmicroservices",
    "sockshop",
    "postnotification",
    "dsb_socialnetwork",
    "dsb_mediamicroservices",
    "trainticket",
]

ANALYSIS_KINDS = [
    "foreign-key-cascade",
    "foreign-key-concurrency",
    "foreign-key-coordination",
    "primary-key-coordination",
    "uniqueness-concurrency",
]

ANALYSIS_IDS = {
    "foreign-key-cascade":      "RI-1",
    "foreign-key-concurrency":  "RI-2",
    "foreign-key-coordination": "RI-3",
    "primary-key-coordination": "EI-1",
    "uniqueness-concurrency":   "Un-1",
}

ENTRY_MARKERS = {
    "foreign-key-cascade":       "\tmissing cascade #",
    "foreign-key-concurrency":   "\twrite #",
    "foreign-key-coordination":  "\tFOREIGN KEY READS #",
    "primary-key-coordination":  "\tPRIMARY KEY READS #",
    "uniqueness-concurrency":     "\t- affected write #",
}

BLOCK_CONTEXT = {
    "foreign-key-cascade":       "delete:",
    "foreign-key-concurrency":   "delete:",
    "foreign-key-coordination":  "entry request:",
    "primary-key-coordination":  "entry request:",
}

BLOCK_CONTEXT_2 = {
    "uniqueness-concurrency": ("entry request:", "write (origin):"),
}

ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_CYAN = "\033[36m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"

EXPECTED_DIR = "./expected"
ACTUAL_DIR = "./aletheia/output"

print(f"[INFO] collecting all warning results in: {ACTUAL_DIR}/")

def normalize_line(line, strip_numbers=False):
    # ignore any comma at the end of each line
    line = re.sub(r",\s*$", "", line)
    if strip_numbers:
        # ignore any enumeration #NUMBER_WARNINGS
        line = re.sub(r"#(\d+)", "#?", line)
    return line


def load_normalized(path, strip_numbers=False):
    with open(path) as f:
        return [normalize_line(l.rstrip("\n"), strip_numbers) for l in f]


def colored_diff(expected_path, actual_path, strip_numbers=False):
    expected_lines = load_normalized(expected_path, strip_numbers)
    actual_lines = load_normalized(actual_path, strip_numbers)

    diff = list(difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile=expected_path,
        tofile=actual_path,
        lineterm="",
    ))

    if not diff:
        print("OK!")
        return

    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            print(f"{ANSI_CYAN}{line}{ANSI_RESET}")
        elif line.startswith("-"):
            print(f"{ANSI_RED}{line}{ANSI_RESET}")
        elif line.startswith("+"):
            print(f"{ANSI_GREEN}{line}{ANSI_RESET}")
        else:
            print(line)


def _flush_block(blocks, current):
    while current and not current[-1]:
        current.pop()
    if current:
        blocks.append("\n".join(current))


def _extract_entry_blocks(lines, marker, context_marker=""):
    blocks = []
    current_context = ""
    current = []
    for line in lines:
        if context_marker and line.startswith(context_marker):
            _flush_block(blocks, current)
            current = []
            current_context = line
        elif line.startswith(marker):
            _flush_block(blocks, current)
            current = ([current_context] if current_context else []) + [line]
        elif current:
            current.append(line)
    _flush_block(blocks, current)
    return blocks


def _extract_entry_blocks_2ctx(lines, marker, primary_ctx, secondary_ctx):
    blocks = []
    p_lines = []
    s_lines = []
    in_secondary = False
    current = []

    for line in lines:
        if line.startswith(primary_ctx):
            _flush_block(blocks, current)
            current = []
            p_lines = [line]
            s_lines = []
            in_secondary = False
        elif line.startswith(secondary_ctx):
            _flush_block(blocks, current)
            current = []
            s_lines = [line]
            in_secondary = True
        elif line.startswith(marker):
            _flush_block(blocks, current)
            current = p_lines + s_lines + [line]
            in_secondary = False
        elif in_secondary and not current:
            s_lines.append(line)
        elif current:
            current.append(line)

    _flush_block(blocks, current)
    return blocks


def compute_metrics(expected_path, actual_path, kind):
    expected_lines = load_normalized(expected_path, strip_numbers=True)
    actual_lines = load_normalized(actual_path, strip_numbers=True)
    marker = ENTRY_MARKERS[kind]

    tp = fp = fn = 0

    if kind in BLOCK_CONTEXT:
        expected_blocks = _extract_entry_blocks(expected_lines, marker, context_marker=BLOCK_CONTEXT[kind])
        actual_blocks   = _extract_entry_blocks(actual_lines,   marker, context_marker=BLOCK_CONTEXT[kind])
    elif kind in BLOCK_CONTEXT_2:
        ctx1, ctx2 = BLOCK_CONTEXT_2[kind]
        expected_blocks = _extract_entry_blocks_2ctx(expected_lines, marker, ctx1, ctx2)
        actual_blocks   = _extract_entry_blocks_2ctx(actual_lines,   marker, ctx1, ctx2)
    else:
        raise ValueError(f"no block context defined for kind: {kind}")

    matcher = difflib.SequenceMatcher(None, expected_blocks, actual_blocks)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            tp += i2 - i1
        elif tag == "delete":
            fn += i2 - i1
        elif tag == "insert":
            fp += j2 - j1
        elif tag == "replace":
            fn += i2 - i1
            fp += j2 - j1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}


def parse_num_warnings(path):
    with open(path) as f:
        for line in f:
            m = re.match(r"\[NUM_WARNINGS\s*=\s*(\d+)\]", line.strip())
            if m:
                return int(m.group(1))
    return 0


def print_warnings_table(rows, title="", col_w=0):
    col_w = col_w or max(len(name) for name, *_ in rows)
    sep = "  " + "-" * (col_w + 22)
    if title:
        print(f"\n{ANSI_BOLD}{title}{ANSI_RESET}")
        print(f"  {'Analysis':<{col_w}}  {'Expected':>9}  {'Actual':>7}")
        print(sep)
    if not title:
        print(sep)
    for name, expected_n, actual_n in rows:
        diff = actual_n - expected_n
        diff_str = f"  ({'+' if diff >= 0 else ''}{diff})" if diff != 0 else ""
        print(f"  {name:<{col_w}}  {expected_n:>9}  {actual_n:>7}{diff_str}")


def print_metrics_table(rows, title="", col_w=0):
    col_w = col_w or max(len(name) for name, *_ in rows)
    sep = "  " + "-" * (col_w + 42)
    if title:
        print(f"\n{ANSI_BOLD}{title}{ANSI_RESET}")
        print(f"  {'Analysis':<{col_w}}  {'TP':>4}  {'FP':>4}  {'FN':>4}  {'Precision':>10}  {'Recall':>8}")
        print(sep)
    if not title:
        print(sep)
    for name, m in rows:
        print(
            f"  {name:<{col_w}}  {m['tp']:>4}  {m['fp']:>4}  {m['fn']:>4}"
            f"  {m['precision']:>9.1%}  {m['recall']:>7.1%}"
        )

def collect_app_data(appname):
    dir_expected = f"{EXPECTED_DIR}/{appname}"
    dir_actual = f"{ACTUAL_DIR}/{appname}"

    kind_warnings = {}   # kind -> expected NUM_WARNINGS
    totals = {"tp": 0, "fp": 0, "fn": 0}

    for kind in ANALYSIS_KINDS:
        expected = f"{dir_expected}/expected-{kind}.txt"
        actual   = f"{dir_actual}/analysis/{kind}.txt"
        if not os.path.isfile(expected) or not os.path.isfile(actual):
            kind_warnings[kind] = 0
            continue
        kind_warnings[kind] = parse_num_warnings(actual)
        m = compute_metrics(expected, actual, kind)
        totals["tp"] += m["tp"]
        totals["fp"] += m["fp"]
        totals["fn"] += m["fn"]

    return {"warnings": kind_warnings, **totals}


def print_summary():
    ids = [ANALYSIS_IDS[k] for k in ANALYSIS_KINDS]
    col_w = max(len(a) for a in APPS)
    id_w  = 5

    header = f"  {'App':<{col_w}}  " + "  ".join(f"{i:>{id_w}}" for i in ids) + "  |   TP   FP   FN"
    sep    = "  " + "-" * (len(header) - 2)

    lines = ["", header, sep]

    total_tp = total_fp = total_fn = 0
    kind_totals = {k: 0 for k in ANALYSIS_KINDS}

    for appname in APPS:
        data = collect_app_data(appname)
        tp, fp, fn = data["tp"], data["fp"], data["fn"]
        kind_cols = "  ".join(f"{data['warnings'][k]:>{id_w}}" for k in ANALYSIS_KINDS)
        lines.append(f"  {appname:<{col_w}}  {kind_cols}  |  {tp:>4} {fp:>4} {fn:>4}")
        total_tp += tp
        total_fp += fp
        total_fn += fn
        for k in ANALYSIS_KINDS:
            kind_totals[k] += data["warnings"][k]

    total_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    total_recall    = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    kind_cols = "  ".join(f"{kind_totals[k]:>{id_w}}" for k in ANALYSIS_KINDS)
    lines.append(sep)
    lines.append(f"  {'TOTAL':<{col_w}}  {kind_cols}  |  {total_tp:>4} {total_fp:>4} {total_fn:>4}")
    lines.append("")

    output = "\n".join(lines)
    output += "\n"
    output += f"Precision: {total_precision:.1%}\n"
    output += f"Recall:    {total_recall:.1%}"
    filepath = "paper/tmp/table2_real_detection.txt"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(output + "\n")
    print(f"[INFO] saved to {filepath}\n")


def metrics_for_app(appname):
    dir_expected = f"./expected/{appname}"
    dir_actual = f"./aletheia/output/{appname}"

    metrics_rows = []
    warnings_rows = []
    totals = {"tp": 0, "fp": 0, "fn": 0}
    total_expected_n = total_actual_n = 0

    for kind in ANALYSIS_KINDS:
        expected = f"{dir_expected}/expected-{kind}.txt"
        actual = f"{dir_actual}/analysis/{kind}.txt"

        if not os.path.isfile(expected):
            print(f"  warning: missing expected file: {expected}")
            continue
        if not os.path.isfile(actual):
            print(f"  warning: missing actual file: {actual}")
            continue

        label = f"({ANALYSIS_IDS[kind]}) {kind}"
        m = compute_metrics(expected, actual, kind)
        metrics_rows.append((label, m))
        totals["tp"] += m["tp"]
        totals["fp"] += m["fp"]
        totals["fn"] += m["fn"]

        expected_n = parse_num_warnings(expected)
        actual_n = parse_num_warnings(actual)
        warnings_rows.append((label, expected_n, actual_n))
        total_expected_n += expected_n
        total_actual_n += actual_n

    tp, fp, fn = totals["tp"], totals["fp"], totals["fn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    total_row = {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}

    col_w = max(len(name) for name, *_ in warnings_rows)
    print_warnings_table(warnings_rows, title=f"Warnings for: {appname}", col_w=col_w)
    print_warnings_table([("TOTAL", total_expected_n, total_actual_n)], col_w=col_w)
    print()
    print_metrics_table(metrics_rows, title=f"Metrics for: {appname}", col_w=col_w)
    print_metrics_table([("TOTAL", total_row)], col_w=col_w)
    print()


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "summary":
        print_summary()
        return

    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <appname> [schema|analysis|metrics]")
        print(f"       {sys.argv[0]} summary")
        print("available apps:")
        for app in APPS:
            print(f"  - {app}")
        sys.exit(1)

    appname = sys.argv[1]
    type_ = sys.argv[2]
    dir_expected = f"./expected/{appname}"
    dir_actual = f"./aletheia/output/{appname}"

    if type_ == "metrics":
        metrics_for_app(appname)
        return

    if type_ == "analysis":
        print()
        print("Select analysis kind:")
        i = 1
        for kind, id in ANALYSIS_IDS.items():
            print(f"  {i}) {id}: {kind}")
            i += 1
        print()

        choice = input("Enter a number [1-5]: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(ANALYSIS_KINDS)):
            print("Invalid choice.")
            sys.exit(1)
        kind = ANALYSIS_KINDS[int(choice) - 1]
    else:
        kind = ""

    if type_ == "schema":
        expected = f"{dir_expected}/expected-schema.json"
        actual = f"{dir_actual}/schema.json"
    else:
        expected = f"{dir_expected}/expected-{kind}.txt"
        actual = f"{dir_actual}/analysis/{kind}.txt"

    if not os.path.isfile(expected):
        print(f"error: expected file not found: {expected}")
        sys.exit(1)
    if not os.path.isfile(actual):
        print(f"error: actual file not found: {actual}")
        sys.exit(1)

    strip_numbers = type_ != "schema"
    colored_diff(expected, actual, strip_numbers=strip_numbers)


if __name__ == "__main__":
    main()
