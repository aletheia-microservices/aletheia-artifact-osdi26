#!/bin/bash
set -e

python3 collect_warnings.py summary
python3 collect_metrics.py
python3 collect_metrics.py --synthetic
python3 collect_memory.py
python3 collect_memory.py --synthetic
