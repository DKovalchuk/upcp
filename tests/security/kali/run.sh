#!/usr/bin/env bash
# Kali pentest agent entrypoint — TASK-0142 / SPEC-0024 Phase 4.
# Runs inside the `kali` compose service (tests/security/kali is mounted
# read-only at /kali-agent; findings go to $KALI_REPORT_DIR, default /reports).
#
# Checks (lightweight, minutes not hours):
#   1. nmap service/version scan of the app host (top 100 ports)
#   2. nikto web-server scan (bounded via -Tuning and -maxtime)
#   3. sqlmap smoke against one representative authenticated query param
#      (--batch --crawl=0 --level=1 --risk=1, hard-capped by `timeout`)
#   4. curl security-header audit of /health
#
# Outputs: /reports/kali_<ts>.json (schema upcp-security-result/v1) and
# /reports/kali_<ts>.md. Exit 0 = reports written, 2 = formatter/infra failure.
# Never prints secrets: the login token is kept in a shell variable only and
# never written to reports (format_result.py redacts as a second line of defense).

set -uo pipefail

TARGET="${KALI_TARGET:-http://app:8080}"
REPORT_DIR="${KALI_REPORT_DIR:-/reports}"
KALI_EMAIL="${KALI_EMAIL:-admin@example.com}"
KALI_PASSWORD="${KALI_PASSWORD:-TestAdmin123!}"
SQLMAP_MAX_SECONDS="${KALI_SQLMAP_MAX_SECONDS:-170}"
NIKTO_MAX_SECONDS="${KALI_NIKTO_MAX_SECONDS:-200}"

TS="$(date +%Y%m%d-%H%M%S)"
RAW="$(mktemp -d)"
START_EPOCH="$(date +%s)"

AUTHORITY="${TARGET#*://}"
HOSTPORT="${AUTHORITY%%/*}"
HOSTNAME="${HOSTPORT%%:*}"

echo "[kali] ts=${TS} target=${TARGET} host=${HOSTNAME} raw=${RAW}"

# ── 1. nmap: service/version detection, top 100 ports ─────────────────────
# -sT (TCP connect) is required: the agent runs non-root and raw sockets
# (default SYN scan / ARP probes) are not permitted — verified empirically.
timeout -k 10 150 nmap -Pn -sT -sV --top-ports 100 -oX "${RAW}/nmap.xml" \
    "${HOSTNAME}" >"${RAW}/nmap.log" 2>&1
NMAP_RC=$?
echo "[kali] nmap rc=${NMAP_RC}"

# ── 2. nikto: bounded web-server scan ─────────────────────────────────────
timeout -k 10 "${NIKTO_MAX_SECONDS}" \
    nikto -h "${TARGET}" -nointeractive -Tuning "${NIKTO_TUNING:-123b}" \
    -maxtime "$((NIKTO_MAX_SECONDS - 20))" \
    -output "${RAW}/nikto.txt" >"${RAW}/nikto.log" 2>&1
NIKTO_RC=$?
echo "[kali] nikto rc=${NIKTO_RC}"

# ── 3. sqlmap smoke against a representative param ────────────────────────
# Bearer token fetched from the live stack (15 min TTL) — kept in-memory only.
TOKEN="$(curl -s -m 10 -X POST "${TARGET}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${KALI_EMAIL}\",\"password\":\"${KALI_PASSWORD}\"}" \
    | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("access_token", ""))
except Exception:
    print("")' 2>/dev/null)"
AUTH_USED="no"
SQLMAP_ARGS=(
    -u "${TARGET}/api/v1/search?q=upcp&limit=5"
    --batch --crawl=0 --level=1 --risk=1 --threads=1
    --timeout=10 --retries=1 --output-dir="${RAW}/smap"
)
if [ -n "${TOKEN}" ]; then
    AUTH_USED="yes"
    SQLMAP_ARGS+=(-H "Authorization: Bearer ${TOKEN}")
fi
timeout -k 5 "${SQLMAP_MAX_SECONDS}" \
    sqlmap "${SQLMAP_ARGS[@]}" >"${RAW}/sqlmap.log" 2>&1
SQLMAP_RC=$?
echo "[kali] sqlmap rc=${SQLMAP_RC} auth=${AUTH_USED}"

# ── 4. curl security-header audit ─────────────────────────────────────────
curl -s -m 10 -D "${RAW}/headers.txt" -o /dev/null "${TARGET}/health"
HEADERS_RC=$?
echo "[kali] headers rc=${HEADERS_RC}"

# ── format: shared result schema + markdown report ────────────────────────
DURATION="$(( $(date +%s) - START_EPOCH ))"
python3 /kali-agent/format_result.py \
    --target "${TARGET}" --ts "${TS}" --raw "${RAW}" \
    --out "${REPORT_DIR}/kali_${TS}.json" \
    --md "${REPORT_DIR}/kali_${TS}.md" \
    --nmap-rc "${NMAP_RC}" --nikto-rc "${NIKTO_RC}" \
    --sqlmap-rc "${SQLMAP_RC}" --headers-rc "${HEADERS_RC}" \
    --sqlmap-max "${SQLMAP_MAX_SECONDS}" --nikto-max "${NIKTO_MAX_SECONDS}" \
    --auth-used "${AUTH_USED}" --duration "${DURATION}"
FORMAT_RC=$?

if [ "${FORMAT_RC}" -eq 0 ]; then
    echo "[kali] reports: ${REPORT_DIR}/kali_${TS}.{json,md} (duration=${DURATION}s)"
else
    echo "[kali] format_result.py failed rc=${FORMAT_RC}" >&2
    exit 2
fi
exit 0
