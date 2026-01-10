#!/bin/bash
# Stop all running bot instances

echo "🔍 Looking for running bot processes..."

# Find all Python bot processes
PROCESSES=$(ps aux | grep -E "python.*(bot|src\.presentation\.main|main\.py)" | grep -v grep | grep -v "$0")

if [ -z "$PROCESSES" ]; then
    echo "✅ No bot processes found running"
    exit 0
fi

echo "Found the following bot processes:"
echo "$PROCESSES" | while read line; do
    PID=$(echo "$line" | awk '{print $2}')
    CMD=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
    echo "  PID: $PID - $CMD"
done

echo ""
read -p "Kill all these processes? (yes/no): " confirm

if [ "$confirm" = "yes" ] || [ "$confirm" = "y" ]; then
    echo "$PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        if [ ! -z "$PID" ]; then
            echo "Killing PID $PID..."
            kill "$PID" 2>/dev/null
        fi
    done
    sleep 1
    
    # Verify they're stopped
    REMAINING=$(ps aux | grep -E "python.*(bot|src\.presentation\.main|main\.py)" | grep -v grep | grep -v "$0")
    if [ -z "$REMAINING" ]; then
        echo "✅ All bot processes stopped successfully"
    else
        echo "⚠️  Some processes are still running, trying force kill..."
        echo "$REMAINING" | while read line; do
            PID=$(echo "$line" | awk '{print $2}')
            kill -9 "$PID" 2>/dev/null
        done
        echo "✅ Force killed remaining processes"
    fi
else
    echo "❌ Cancelled. No processes were killed."
    exit 1
fi
