#!/bin/bash

set -e

runs=5
mode=default
target=both

apps_realistic=(
    digota
    sockshop
    eshopmicroservices
    postnotification
    dsb_socialnetwork
    dsb_mediamicroservices
    trainticket
)

apps_synthetic=(
    synthetic_app1
    synthetic_app2
    synthetic_app3
    synthetic_app4
    synthetic_app5
)

DATE=$(date +%F)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER_DIR="$SCRIPT_DIR/aletheia"
METRICS_DIR="$SCRIPT_DIR/aletheia/eval/memory/$DATE"

mkdir -p "$METRICS_DIR"
mkdir -p "$METRICS_DIR/realistic"
mkdir -p "$METRICS_DIR/synthetic"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS uses BSD time with -l
    TIME_CMD="/usr/bin/time -l"
else
    # Linux uses GNU time with -v
    TIME_CMD="time -v"
fi

for arg in "$@"; do
    case "$arg" in
        --help)
            echo "Usage: ./run.sh [MODE] [TARGET]"
            echo ""
            echo "MODE (default: runs --init then --eval):"
            echo "  --init       download dependencies and import all applications (recommended before running the experiments)"
            echo "  --eval       run the experiments (requires --init to have been run at least once)"
            echo "  --debug      run without flags for debugging (single run)"
            echo ""
            echo "TARGET (default: both):"
            echo "  --realistic  run only realistic applications"
            echo "  --synthetic  run only synthetic applications"
            echo ""
            echo "Examples:"
            echo "  ./run.sh                       # init + eval for all apps"
            echo "  ./run.sh --eval --realistic    # eval only realistic apps"
            echo "  ./run.sh --init --synthetic    # init only synthetic apps"
            exit 0
            ;;
        --eval)
            mode="--eval"
            ;;
        --debug)
            mode=""
            runs=1
            ;;
        --init)
            mode="--init"
            runs=1
            ;;
        --realistic)
            target="realistic"
            ;;
        --synthetic)
            target="synthetic"
            ;;
        *)
            echo "[ERROR] unknown argument: $arg"
            exit 1
            ;;
    esac
done

# default: run --init then --eval
if [[ "$mode" == "default" ]]; then
    run_modes=("--init" "--eval")
else
    run_modes=("$mode")
fi

cd $ALETHEIA_BASE
#GOGC=100

if [[ "$target" == "both" || "$target" == "realistic" ]]; then
    for m in "${run_modes[@]}"; do
        [[ "$m" == "--init" ]] && local_runs=1 || local_runs=$runs
        for app in "${apps_realistic[@]}"; do
            echo "=== Running $app ($local_runs times) $m ==="

            for i in $(seq 1 $local_runs); do
                echo "=== Run $i/$local_runs"
                timestamp=$(date +%s)
                output_file="$METRICS_DIR/realistic/${app}.${timestamp}.txt"
                go_tags="-tags=eval,realistic"
                if [[ "$m" == "--eval" ]]; then
                    $TIME_CMD go -C $ANALYZER_DIR run $go_tags main.go $m "$app" 2> "$output_file"
                else
                    go -C $ANALYZER_DIR run $go_tags main.go $m "$app"
                fi
            done

            echo
        done
    done
fi

if [[ "$target" == "both" || "$target" == "synthetic" ]]; then
    for m in "${run_modes[@]}"; do
        [[ "$m" == "--init" ]] && local_runs=1 || local_runs=$runs
        for app in "${apps_synthetic[@]}"; do
            echo "=== Running $app ($local_runs times) $m ==="

            go_tags=""
            case "$app" in
                synthetic_app1|synthetic_app2|synthetic_app3)
                    go_tags="-tags=eval,synthetic_small"
                    ;;
                synthetic_app4)
                    go_tags="-tags=eval,synthetic_medium"
                    ;;
                synthetic_app5)
                    go_tags="-tags=eval,synthetic_large"
                    ;;
            esac

            for i in $(seq 1 $local_runs); do
                echo "=== Run $i/$local_runs"
                timestamp=$(date +%s)
                output_file="$METRICS_DIR/synthetic/${app}.${timestamp}.txt"

                if [[ "$m" == "--eval" ]]; then
                   $TIME_CMD go -C $ANALYZER_DIR run $go_tags main.go $m --synthetic "$app" 2> "$output_file"
                else
                    go -C $ANALYZER_DIR run $go_tags main.go $m --synthetic "$app"
                fi
            done

            echo
        done
    done
fi
