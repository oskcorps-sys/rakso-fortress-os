#!/bin/bash
# setup-sdd.sh - Initialize SDD+ project structure
#
# Usage:
#   bash setup-sdd.sh [project-name]
#
# Creates: complete SDD+ project with all directories and files

set -e

PROJECT_NAME="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Setting up SDD+ project: $PROJECT_NAME"

# Create main directories
mkdir -p "$PROJECT_NAME/sdd/artifacts"
mkdir -p "$PROJECT_NAME/sdd/logs"
mkdir -p "$PROJECT_NAME/sdd/schemas"
mkdir -p "$PROJECT_NAME/sdd/validators"
mkdir -p "$PROJECT_NAME/sdd/tools"
mkdir -p "$PROJECT_NAME/sdd/skills"
mkdir -p "$PROJECT_NAME/sdd/behavior"
mkdir -p "$PROJECT_NAME/sdd/state-machine"
mkdir -p "$PROJECT_NAME/tests"

echo "✓ Directory structure created"

# Copy Python files (scaffolding from this script's directory)
# In actual use, these would come from the outputs or be part of a template

# Create __init__.py files if they don't exist
touch "$PROJECT_NAME/sdd/__init__.py"
touch "$PROJECT_NAME/sdd/tools/__init__.py"
touch "$PROJECT_NAME/sdd/validators/__init__.py"
touch "$PROJECT_NAME/sdd/skills/__init__.py"
touch "$PROJECT_NAME/tests/__init__.py"

# Create .gitkeep for empty directories
touch "$PROJECT_NAME/sdd/logs/.gitkeep"

echo "✓ Python packages initialized"

# Initialize git (if not already git)
if [ ! -d "$PROJECT_NAME/.git" ]; then
    cd "$PROJECT_NAME"
    git init
    echo "✓ Git repository initialized"
else
    cd "$PROJECT_NAME"
fi

# Create initial commit
git add .
git commit -m "PHASE 0: SDD+ scaffold - bootstrap project structure" || true

echo "✓ Git initialized"
echo ""
echo "📋 Next steps:"
echo "   1. cd $PROJECT_NAME"
echo "   2. uv sync (or: pip install -e .)"
echo "   3. pytest tests/ -v --cov"
echo "   4. Read AGENTS.md (implementer role) and CLAUDE.md (auditor role)"
echo "   5. Confirm DECISION-0007 (repo location) in DECISIONS.md"
echo ""
echo "🎯 Ready for Phase 1!"
