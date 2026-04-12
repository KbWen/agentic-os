#!/bin/bash

# AgentCortex Skill Synchronization Script
# Purpose: Sync skill metadata from .agents/skills/ to .agent/skills/
# This ensures cross-platform compatibility (handling Windows symlink issues)
# while keeping metadata in sync.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$REPO_ROOT/.agents/skills"
DEST_DIR="$REPO_ROOT/.agent/skills"

echo "🔄 Synchronizing AI Skills metadata..."

if [ ! -d "$SRC_DIR" ]; then
    echo "❌ Error: Source directory $SRC_DIR not found."
    exit 1
fi

mkdir -p "$DEST_DIR"

# Loop through each skill in .agents/skills
for skill_path in "$SRC_DIR"/*; do
    if [ -d "$skill_path" ]; then
        skill_name=$(basename "$skill_path")
        meta_file="$skill_path/agents/openai.yaml"
        
        # Check if the specific metadata file exists
        if [ -f "$meta_file" ]; then
            echo "  - Syncing metadata for: $skill_name"
            cp "$meta_file" "$DEST_DIR/$skill_name"
        else
            # Fallback: if agents/openai.yaml doesn't exist, check for other potential meta files or skip
            # Some skills might just have SKILL.md, but the .agent/skills/ usually tracks the identity YAML
            if [ -f "$skill_path/SKILL.md" ] && [ ! -f "$DEST_DIR/$skill_name" ]; then
                 echo "  - ⚠️ No identity YAML found for $skill_name, skipping."
            fi
        fi
    fi
done

echo "✅ Skill synchronization complete."
