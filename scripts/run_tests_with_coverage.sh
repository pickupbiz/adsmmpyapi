#!/bin/bash
# Script to run tests with coverage reporting

echo "Running tests with coverage..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install/upgrade coverage dependencies
pip install -q pytest-cov coverage

# Run tests with coverage
pytest \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    --cov-branch \
    -v

echo ""
echo "Coverage reports generated:"
echo "  - Terminal: Shown above"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo ""
echo "To view HTML report, open htmlcov/index.html in your browser"
