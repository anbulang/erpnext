#!/bin/bash
# Batch render all Mermaid diagrams to SVG
# Usage: bash render-all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Rendering ERPNext Architecture Diagrams ==="
echo ""

# Puppeteer config for headless rendering as root
PCONFIG="puppeteer-config.json"

# Check if config exists
if [ ! -f "$PCONFIG" ]; then
    echo "Error: $PCONFIG not found"
    exit 1
fi

# Function to render a diagram
render_diagram() {
    local INPUT="$1"
    local OUTPUT="$2"
    local THEME="${3:-default}"
    local BG="${4:-white}"

    if [ ! -f "$INPUT" ]; then
        echo "  ⚠️  $INPUT not found, skipping"
        return
    fi

    echo "  📄 Rendering: $INPUT → $OUTPUT"

    npx -y @mermaid-js/mermaid-cli \
        -i "$INPUT" \
        -o "$OUTPUT" \
        -t "$THEME" \
        -b "$BG" \
        -p "$PCONFIG" \
        -s 2 \
        2>&1 | grep -v "Generating single mermaid chart" || true

    if [ -f "$OUTPUT" ]; then
        SIZE=$(wc -c < "$OUTPUT")
        echo "  ✓ Generated: $OUTPUT ($SIZE bytes)"
    else
        echo "  ❌ Failed to generate: $OUTPUT"
    fi
}

# Architecture diagrams
echo "🏗️  Architecture Diagrams"
echo "───────────────────────────"
render_diagram "overall-architecture.mmd" "../architecture/overall-architecture.svg"
render_diagram "tech-stack.mmd" "../architecture/tech-stack.svg"
render_diagram "controller-inheritance.mmd" "../architecture/controller-inheritance.svg"
echo ""

# Workflow diagrams
echo "🔄 Workflow Diagrams"
echo "───────────────────────────"
render_diagram "pos-workflow.mmd" "../workflows/pos-workflow.svg"
render_diagram "wholesale-flow.mmd" "../workflows/wholesale-flow.svg"
echo ""

# Data model diagrams
echo "📊 Data Model Diagrams"
echo "───────────────────────────"
render_diagram "data-relationships.mmd" "../data-model/data-relationships.svg"
echo ""

# Also generate PNG versions (optional, for better compatibility)
echo "🖼️  Generating PNG versions (optional)..."
echo "───────────────────────────"
for mmd in *.mmd; do
    [ -f "$mmd" ] || continue
    base=$(basename "$mmd" .mmd)

    # Determine output directory
    case "$base" in
        overall-architecture|tech-stack|controller-inheritance)
            outdir="../architecture"
            ;;
        pos-workflow|wholesale-flow)
            outdir="../workflows"
            ;;
        data-relationships)
            outdir="../data-model"
            ;;
        *)
            outdir=".."
            ;;
    esac

    png_output="$outdir/${base}.png"

    if [ -f "$mmd" ]; then
        echo "  📸 $mmd → $png_output"
        npx -y @mermaid-js/mermaid-cli \
            -i "$mmd" \
            -o "$png_output" \
            -t default \
            -b white \
            -p "$PCONFIG" \
            -s 3 \
            2>&1 | grep -v "Generating single mermaid chart" || true

        if [ -f "$png_output" ]; then
            echo "  ✓ PNG: $(wc -c < "$png_output") bytes"
        fi
    fi
done

echo ""
echo "=== Rendering Complete ==="
echo ""
echo "Generated files:"
find .. -name "*.svg" -o -name "*.png" | grep -v "_src" | sort
echo ""
echo "To view: open the SVG files in a browser or use 'eog' on Linux"
