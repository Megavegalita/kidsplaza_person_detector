# Tracking Bug Analysis & Fix

## 🐛 Problem Identified

**Issue**: Track IDs jumping between different people across frames

**Root Cause**: Incorrect mapping between detections and tracks in `process_video_file.py` lines 221-225

```python
# WRONG - This is just using index, not proper bbox matching!
for i, detection in enumerate(detections):
    if i < len(tracked_objects):
        detection['track_id'] = tracked_objects[i].get('track_id', i+1)
```

## Problems

1. **Index-based mapping**: Just using `enumerate()` to map detections to tracks
2. **No bbox matching**: Not matching based on spatial proximity
3. **Wrong order**: Assumes detections and tracks are in same order (they're not!)

## Solutions

### Option 1: Use IoU to match detections to tracked_objects
Match each detection's bbox to tracked_objects' bbox using IoU

### Option 2: Return track_id from tracker.update()
Modify tracker to return detections with track_id already attached

### Option 3: Store track_id mapping from tracker
Keep track of which detection matches which track using the matching results

## Recommended Fix

**Best approach**: Modify tracker to attach track_id to each detection in its return

This way:
1. Tracker already has matching logic (IoU-based)
2. Tracker knows which detection matches which track
3. We just return detections with track_id attached

