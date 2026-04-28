#!/usr/bin/env bash
# Meta Ads Manager — quick launcher
# Usage:
#   ./start.sh          → open the visual dashboard
#   ./start.sh setup    → run the setup wizard
#   ./start.sh mcp      → run the MCP server (for Claude)

set -e
cd "$(dirname "$0")"

case "${1:-dashboard}" in
  setup)
    python setup_wizard.py
    ;;
  mcp)
    python -m meta_ads_mcp.server
    ;;
  dashboard|*)
    echo "Opening Meta Ads Manager dashboard..."
    streamlit run app.py
    ;;
esac
