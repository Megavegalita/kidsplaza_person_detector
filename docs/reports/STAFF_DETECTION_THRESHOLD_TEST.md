# Staff Detection Threshold Testing Report

## Test Summary

**Video:** `Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`  
**Duration:** 60 seconds (first 60s)  
**Total Person Detections:** 117  
**Frames Processed:** 25 frames (every 60 frames)

## Results Comparison

| Threshold | Staff Count | Customer Count | Staff % | Avg Staff Conf | Avg Cust Conf | Processing Time |
|-----------|-------------|---------------|---------|----------------|---------------|-----------------|
| 0.30      | 73          | 44            | 62.4%   | 0.712 ± 0.113   | 0.523 ± 0.277  | 14.00s         |
| 0.40      | 72          | 45            | 61.5%   | 0.717 ± 0.103   | 0.496 ± 0.302  | 6.52s          |
| 0.50      | 70          | 47            | 59.8%   | 0.724 ± 0.095   | 0.427 ± 0.345  | 6.44s          |
| 0.60      | 62          | 55            | 53.0%   | 0.747 ± 0.075   | 0.316 ± 0.362  | 5.83s          |
| 0.70      | 48          | 69            | 41.0%   | 0.778 ± 0.052   | 0.148 ± 0.307  | 5.76s          |

## Staff Confidence Distribution

- **Threshold 0.3-0.5:** ~65-69% of staff detections have confidence > 0.7
- **Threshold 0.6:** 77.4% of staff detections have confidence > 0.7
- **Threshold 0.7:** 100% of staff detections have confidence > 0.7 (but only 41% detection rate)

## Analysis

### Threshold 0.3-0.4
- **Pros:** Higher detection rate (61-62% staff)
- **Cons:** Lower confidence (0.71-0.72), may include false positives
- **Use case:** If you want to catch all possible staff members

### Threshold 0.5
- **Pros:** Balanced detection rate (59.8%), decent confidence (0.724)
- **Cons:** Still relatively high staff rate, may have some false positives
- **Use case:** General purpose, moderate filtering

### Threshold 0.6 ⭐ **RECOMMENDED**
- **Pros:** 
  - Good balance: 53% staff rate (more realistic)
  - Higher confidence: 0.747 ± 0.075 (more reliable)
  - 77.4% of detections have confidence > 0.7
  - Faster processing: 5.83s
- **Cons:** Slightly lower detection rate than 0.5
- **Use case:** **Production use - balanced accuracy and reliability**

### Threshold 0.7
- **Pros:** Highest confidence (0.778), very consistent (std: 0.052)
- **Cons:** Lower detection rate (41%), may miss some staff members
- **Use case:** When accuracy is critical and false positives must be minimized

## Recommendation

**✅ Recommended Threshold: 0.6**

**Rationale:**
1. **Balanced Detection Rate:** 53% staff rate is more realistic than 60%+
2. **Good Confidence:** Average 0.747 with reasonable consistency (std: 0.075)
3. **Reliable Detections:** 77.4% of staff detections have confidence > 0.7
4. **Performance:** Faster processing time (5.83s vs 6.44s+ for lower thresholds)

## Configuration

For production use, set in camera config:

```json
{
  "features": {
    "staff_detection": {
      "enabled": true,
      "model_path": "models/kidsplaza/best.pt",
      "conf_threshold": 0.6
    }
  }
}
```

## Next Steps

1. ✅ Test with threshold 0.6 in production
2. Monitor staff detection rate over time
3. Adjust threshold if needed based on:
   - Too many false positives → increase to 0.65-0.7
   - Missing too many staff → decrease to 0.5-0.55
4. Consider per-channel thresholds if different cameras have different staff ratios

## Notes

- Staff rate of 53-62% may seem high, but could be accurate if:
  - This is a busy retail location with many staff present
  - Staff uniforms are easily distinguishable
  - The model is working correctly
- Visual verification recommended to confirm accuracy
- Threshold can be fine-tuned per channel if needed

