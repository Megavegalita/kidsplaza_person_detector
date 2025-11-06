#!/usr/bin/env python3
import json
from pathlib import Path

data = json.load(open('output/test_staff/threshold_comparison_full.json'))

print("="*80)
print("DETAILED THRESHOLD ANALYSIS")
print("="*80)

for result in data:
    threshold = result['threshold']
    staff_conf = result.get('staff_confidences', [])
    cust_conf = result.get('customer_confidences', [])
    
    print(f"\nThreshold {threshold:.2f}:")
    print(f"  Staff: {result['staff_count']} ({result['staff_count']/max(result['total_classifications'],1)*100:.1f}%)")
    print(f"  Customer: {result['customer_count']} ({result['customer_count']/max(result['total_classifications'],1)*100:.1f}%)")
    
    if staff_conf:
        import numpy as np
        conf_above_07 = sum(1 for c in staff_conf if c > 0.7)
        conf_above_08 = sum(1 for c in staff_conf if c > 0.8)
        print(f"  Staff confidence distribution:")
        print(f"    > 0.7: {conf_above_07}/{len(staff_conf)} ({conf_above_07/len(staff_conf)*100:.1f}%)")
        print(f"    > 0.8: {conf_above_08}/{len(staff_conf)} ({conf_above_08/len(staff_conf)*100:.1f}%)")

print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)
print("Based on results:")
print("- Threshold 0.5-0.6: Good balance (53-60% staff, confidence ~0.72-0.75)")
print("- Threshold 0.7: Higher confidence (0.78) but lower detection rate (41%)")
print("\nSuggested threshold: 0.6")
print("  - Staff confidence: 0.747 (good)")
print("  - Staff rate: 53% (reasonable)")
print("  - Processing time: reasonable")
