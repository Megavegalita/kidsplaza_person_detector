#!/bin/bash
# Auto-monitor ArcFace benchmark with periodic updates

cd "$(dirname "$0")/.." || exit

TOTAL_CONFIGS=8
CHECK_INTERVAL=30  # Check every 30 seconds
MAX_ITERATIONS=60  # Max 30 minutes

iteration=0

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║          AUTO-MONITORING ARCFACE BENCHMARK                                  ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Monitoring benchmark progress..."
echo "🔄 Checking every ${CHECK_INTERVAL} seconds"
echo "⏱️  Will check for up to $((MAX_ITERATIONS * CHECK_INTERVAL / 60)) minutes"
echo ""

while [ $iteration -lt $MAX_ITERATIONS ]; do
    # Count completed configs
    completed=$(find output/arcface_benchmark -name "report_*.json" 2>/dev/null | wc -l | tr -d ' ')
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⏰ Check #$((iteration + 1)) - $(date '+%H:%M:%S')"
    echo ""
    echo "✅ Progress: ${completed}/${TOTAL_CONFIGS} configs completed"
    echo ""
    
    # Show completed configs with results
    echo "📊 COMPLETED CONFIGS:"
    for dir in output/arcface_benchmark/*/; do
        if [ -d "$dir" ]; then
            config_name=$(basename "$dir")
            report_file=$(find "$dir" -name "report_*.json" 2>/dev/null | head -1)
            if [ -n "$report_file" ]; then
                tracks=$(grep -o '"unique_tracks_total":[0-9]*' "$report_file" 2>/dev/null | head -1 | cut -d: -f2)
                echo "   ✅ $config_name: $tracks tracks"
            fi
        fi
    done 2>/dev/null
    
    # Show current activity
    echo ""
    echo "📝 CURRENT STATUS:"
    tail -2 logs/arcface_benchmark.log 2>/dev/null | grep -E "(Running|completed)" | sed 's/INFO:__main__://' | sed 's/^/   /' || echo "   (Initializing...)"
    
    # Check if done
    if [ "$completed" -eq "$TOTAL_CONFIGS" ]; then
        echo ""
        echo "🎉 BENCHMARK COMPLETED!"
        echo ""
        echo "📊 FINAL RESULTS:"
        bash scripts/monitor_arcface_benchmark.sh
        
        # Check for summary report
        if [ -f output/arcface_benchmark/benchmark_summary.json ]; then
            echo ""
            echo "📄 Summary report: output/arcface_benchmark/benchmark_summary.json"
            python3 << 'EOF'
import json
from pathlib import Path

report_path = Path("output/arcface_benchmark/benchmark_summary.json")
if report_path.exists():
    with open(report_path) as f:
        data = json.load(f)
    
    best = data['best_config']
    print("\n🏆 BEST CONFIGURATION:")
    print(f"   Name: {best['name']}")
    print(f"   Unique Tracks: {best['unique_tracks']}")
    print(f"\n   Parameters:")
    params = best['parameters']
    print(f"     - similarity_threshold: {params['reid_similarity_threshold']}")
    print(f"     - tracker_max_age: {params['tracker_max_age']}")
    print(f"     - reid_every_k: {params['reid_every_k']}")
    
    comp = best['comparison']
    print(f"\n   Comparison:")
    print(f"     - Body Re-ID baseline: {comp['body_baseline']} tracks")
    print(f"     - Difference: {comp['diff_vs_body']} tracks")
    if comp['better_than_body']:
        print(f"     ✅ ArcFace better than Body Re-ID!")
    else:
        print(f"     ⚠️  ArcFace worse than Body Re-ID")
EOF
        fi
        
        exit 0
    fi
    
    # Check if process is still running
    if ! ps aux | grep -v grep | grep -q "benchmark_arcface_configs.py"; then
        echo ""
        echo "⚠️  WARNING: Benchmark process not found!"
        echo "   It may have crashed or completed. Checking logs..."
        tail -10 logs/arcface_benchmark.log | tail -5 | sed 's/^/   /'
        
        # Check if it actually completed
        completed=$(find output/arcface_benchmark -name "report_*.json" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$completed" -eq "$TOTAL_CONFIGS" ]; then
            echo ""
            echo "✅ Actually completed! All configs done."
            exit 0
        else
            echo ""
            echo "❌ Benchmark stopped before completion."
            echo "   Completed: ${completed}/${TOTAL_CONFIGS}"
            exit 1
        fi
    fi
    
    # Calculate remaining time
    remaining=$((TOTAL_CONFIGS - completed))
    if [ "$remaining" -gt 0 ]; then
        est_minutes=$((remaining * 2))
        echo ""
        echo "⏱️  Estimated: ~${est_minutes} minutes remaining"
    fi
    
    echo ""
    echo "💤 Sleeping ${CHECK_INTERVAL} seconds..."
    echo ""
    
    sleep $CHECK_INTERVAL
    iteration=$((iteration + 1))
done

echo ""
echo "⏰ Time limit reached (${MAX_ITERATIONS} checks)"
echo "📊 Final status:"
bash scripts/monitor_arcface_benchmark.sh
exit 1


