#!/bin/bash
# Clean build artifacts, cache files, and temporary files

echo "🧹 Cleaning Cway MCP Server..."

# Remove Python cache
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# Remove test/coverage artifacts
echo "Removing test artifacts..."
rm -rf .pytest_cache server/.pytest_cache 2>/dev/null
rm -rf server/htmlcov 2>/dev/null
rm -rf .coverage server/.coverage 2>/dev/null

# Remove build artifacts
echo "Removing build artifacts..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
rm -rf build dist 2>/dev/null

# Remove logs (optional - uncomment if you want to clean logs)
# echo "Removing logs..."
# rm -rf server/logs/*.log 2>/dev/null

echo "✅ Cleanup complete!"
