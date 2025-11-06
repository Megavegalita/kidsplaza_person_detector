#!/usr/bin/env python3
"""
Log analyzer for Channel 4 staff detection test.
Analyzes voting behavior, classification accuracy, and filtering stats.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

def analyze_log(log_file: Path) -> Dict:
    """Analyze log file for staff detection metrics."""
    
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)
    
    print(f"📄 Analyzing log: {log_file}")
    print("=" * 60)
    
    stats = {
        "total_frames": 0,
        "staff_classifications": [],
        "voting_events": [],
        "fixed_classifications": [],
        "filtering_stats": [],
        "reid_skipped": 0,
        "counter_events": [],
        "errors": [],
    }
    
    with open(log_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            # Track frames
            if "Processed" in line and "frames" in line:
                match = re.search(r"Processed (\d+) frames", line)
                if match:
                    stats["total_frames"] = max(stats["total_frames"], int(match.group(1)))
            
            # Staff classification events
            if "Staff classification" in line:
                stats["staff_classifications"].append((line_num, line.strip()))
            
            # Voting events
            if "fixed as" in line.lower() or "voting" in line.lower():
                if "track" in line.lower():
                    stats["voting_events"].append((line_num, line.strip()))
            
            # Fixed classifications
            if "fixed=" in line or "fixed as" in line.lower():
                stats["fixed_classifications"].append((line_num, line.strip()))
            
            # Filtering stats
            if "Staff filtering:" in line:
                stats["filtering_stats"].append((line_num, line.strip()))
            
            # Counter events
            if "Counter event:" in line:
                stats["counter_events"].append((line_num, line.strip()))
            
            # Errors
            if "ERROR" in line or "error" in line.lower():
                if "staff" in line.lower() or "classification" in line.lower():
                    stats["errors"].append((line_num, line.strip()))
    
    return stats

def print_analysis(stats: Dict) -> None:
    """Print analysis results."""
    
    print("\n📊 ANALYSIS RESULTS")
    print("=" * 60)
    
    # Basic stats
    print(f"\n📈 Basic Statistics:")
    print(f"  Total frames processed: {stats['total_frames']}")
    print(f"  Staff classification events: {len(stats['staff_classifications'])}")
    print(f"  Voting events: {len(stats['voting_events'])}")
    print(f"  Fixed classifications: {len(stats['fixed_classifications'])}")
    print(f"  Filtering stats entries: {len(stats['filtering_stats'])}")
    print(f"  Counter events: {len(stats['counter_events'])}")
    print(f"  Errors: {len(stats['errors'])}")
    
    # Voting analysis
    if stats["voting_events"]:
        print(f"\n🗳️  Voting Analysis:")
        staff_fixed = sum(1 for _, line in stats["voting_events"] if "staff" in line.lower() and "fixed" in line.lower())
        customer_fixed = sum(1 for _, line in stats["voting_events"] if "customer" in line.lower() and "fixed" in line.lower())
        still_voting = sum(1 for _, line in stats["voting_events"] if "voting" in line.lower())
        
        print(f"  Fixed as STAFF: {staff_fixed}")
        print(f"  Fixed as CUSTOMER: {customer_fixed}")
        print(f"  Still voting: {still_voting}")
        
        if staff_fixed + customer_fixed > 0:
            print(f"\n  Sample fixed classifications:")
            for i, (line_num, line) in enumerate(stats["fixed_classifications"][:5], 1):
                print(f"    {i}. Line {line_num}: {line[:80]}...")
    
    # Filtering analysis
    if stats["filtering_stats"]:
        print(f"\n🔍 Filtering Analysis:")
        total_staff = 0
        total_customer = 0
        
        for _, line in stats["filtering_stats"]:
            match = re.search(r"(\d+) staff.*(\d+) customer", line)
            if match:
                total_staff += int(match.group(1))
                total_customer += int(match.group(2))
        
        print(f"  Total staff filtered: {total_staff}")
        print(f"  Total customers processed: {total_customer}")
        print(f"\n  Sample filtering stats:")
        for i, (line_num, line) in enumerate(stats["filtering_stats"][:5], 1):
            print(f"    {i}. Line {line_num}: {line}")
    
    # Counter events analysis
    if stats["counter_events"]:
        print(f"\n🔢 Counter Events Analysis:")
        enter_events = sum(1 for _, line in stats["counter_events"] if "enter" in line.lower())
        exit_events = sum(1 for _, line in stats["counter_events"] if "exit" in line.lower())
        
        print(f"  Enter events: {enter_events}")
        print(f"  Exit events: {exit_events}")
        print(f"\n  Sample counter events:")
        for i, (line_num, line) in enumerate(stats["counter_events"][:5], 1):
            print(f"    {i}. Line {line_num}: {line[:80]}...")
    
    # Errors
    if stats["errors"]:
        print(f"\n⚠️  Errors Found:")
        for i, (line_num, line) in enumerate(stats["errors"][:10], 1):
            print(f"    {i}. Line {line_num}: {line[:100]}...")
    else:
        print(f"\n✅ No errors found!")
    
    print("\n" + "=" * 60)

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_staff_log.py <log_file>")
        print("\nExample:")
        print("  python analyze_staff_log.py logs/channel_4_staff_test_20250101_120000.log")
        sys.exit(1)
    
    log_file = Path(sys.argv[1])
    
    if not log_file.exists():
        # Try to find latest log file
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = sorted(
                log_dir.glob("channel_4_staff_test_*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if log_files:
                log_file = log_files[0]
                print(f"📁 Using latest log file: {log_file}")
            else:
                print(f"❌ No log files found in {log_dir}")
                sys.exit(1)
        else:
            print(f"❌ Log file not found: {log_file}")
            sys.exit(1)
    
    stats = analyze_log(log_file)
    print_analysis(stats)
    
    # Save summary
    summary_file = log_file.parent / f"{log_file.stem}_analysis.txt"
    with open(summary_file, "w") as f:
        f.write(f"Staff Detection Log Analysis\n")
        f.write(f"Log file: {log_file}\n")
        f.write(f"Analyzed: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total frames: {stats['total_frames']}\n")
        f.write(f"Staff classifications: {len(stats['staff_classifications'])}\n")
        f.write(f"Voting events: {len(stats['voting_events'])}\n")
        f.write(f"Fixed classifications: {len(stats['fixed_classifications'])}\n")
        f.write(f"Counter events: {len(stats['counter_events'])}\n")
        f.write(f"Errors: {len(stats['errors'])}\n")
    
    print(f"\n💾 Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()

