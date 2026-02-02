#!/usr/bin/env bash
set -euo pipefail

TASKS_FILE="${1:-tasks.json}"
HOST="${HOST:-127.0.0.1}"
MAX_RETRY="${MAX_RETRY:-1}"
LOG_ROOT="${LOG_ROOT:-/nas/logs}"

if [[ ! -f "$TASKS_FILE" ]]; then
  echo "Tasks file not found: $TASKS_FILE" >&2
  exit 1
fi

lab-gpu server start --role master --host "$HOST" >/tmp/labgpu_master.log 2>&1 &

lab-gpu submit-batch --file "$TASKS_FILE"

declare -A retries

while true; do
  lab-gpu server tick >/tmp/labgpu_tick.log 2>&1 || true
  STATUS_JSON=$(lab-gpu status --json)

  PENDING=$(echo "$STATUS_JSON" | python -c "import sys, json; print(json.load(sys.stdin)['pending'])")
  RUNNING=$(echo "$STATUS_JSON" | python -c "import sys, json; print(len(json.load(sys.stdin)['running']))")

  FAILED_IDS=$(echo "$STATUS_JSON" | python -c "import sys, json; print(' '.join(str(x['id']) for x in json.load(sys.stdin)['recent'] if x['status']=='failed'))")

  for tid in $FAILED_IDS; do
    retries[$tid]=${retries[$tid]:-0}
    if [[ "${retries[$tid]}" -lt "$MAX_RETRY" ]]; then
      retries[$tid]=$((retries[$tid] + 1))
      echo "Retry task $tid (attempt ${retries[$tid]})"
      lab-gpu server preempt --task-id "$tid" >/dev/null 2>&1 || true
      lab-gpu server tick >/dev/null 2>&1 || true
    else
      echo "Task $tid reached max retry."
    fi
  done

  if [[ "$PENDING" -eq 0 && "$RUNNING" -eq 0 ]]; then
    echo "All tasks finished."
    break
  fi
  sleep 3
done

echo "Log root: $LOG_ROOT (e.g. ${LOG_ROOT}/<task_id>.log)"
