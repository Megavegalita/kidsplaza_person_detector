# Re-ID Improvement Plan

## Problem Analysis
- **Current Issue**: 109 unique tracks for a 3-minute video (too high)
- **Root Cause**: Re-ID embeddings are generated but NOT used for matching
- **Expected**: ~10-20 unique people in reality
- **Actual**: 109 unique track IDs assigned

## Current Situation

### What Re-ID Currently Does
1. ✅ Generates embeddings every K frames (k=20)
2. ✅ Stores embeddings in cache with track_id
3. ✅ Has cosine similarity function available
4. ❌ **NOT used in tracker matching**

### What Tracker Currently Does
1. ✅ IoU-based matching only
2. ✅ Creates new track when IoU < threshold
3. ❌ **Doesn't consider person appearance**
4. ❌ **Doesn't use Re-ID embeddings**

## Solution

### Option 1: Use Re-ID as Tie-Breaker (RECOMMENDED)
When multiple IoU matches exist or IoU is marginal, use Re-ID similarity to choose best match.

**Implementation:**
1. Add optional Re-ID cache/embedder to Tracker
2. In `_associate_detections_to_tracks()`, for marginal IoU matches, compute Re-ID similarity
3. Prefer track with higher Re-ID similarity
4. Only create new track if IoU < threshold AND no similar Re-ID exists

**Pros:** Minimal changes, effective
**Cons:** Requires Re-ID embeddings available

### Option 2: Hybrid Matching (More Complex)
Use both IoU and Re-ID in cost matrix.

**Implementation:**
```python
total_cost = alpha * iou_cost + (1-alpha) * (1 - reid_similarity)
```

**Pros:** More sophisticated
**Cons:** Requires parameter tuning

### Option 3: Re-ID for Lost Track Recovery
When IoU fails, check if Re-ID similarity exists for unmatched detection.

**Implementation:**
1. After IoU matching, for unmatched detections
2. Compute embeddings and check against all existing track embeddings
3. If similarity > threshold, reuse existing track_id
4. Otherwise, create new track

**Pros:** Most effective for reappearing people
**Cons:** Higher computation cost

## Recommended Approach: Option 1 + Option 3

### Implementation Steps

1. **Modify Tracker to accept optional Re-ID components**
   - Add `reid_embedder: Optional[ReIDEmbedder]` parameter
   - Add `reid_cache: Optional[ReIDCache]` parameter
   - Add `reid_similarity_threshold: float = 0.6` parameter

2. **Enhance cost matrix calculation**
   - If Re-ID available, compute embeddings for unmatched detections
   - Check against existing track embeddings
   - Add similarity boost to IoU cost

3. **Add Re-ID matching for unmatched detections**
   - After IoU matching fails
   - Generate detection embedding
   - Find best matching track embedding (cosine similarity)
   - If similarity > threshold, reuse track_id

### Code Changes

**File: `src/modules/tracking/tracker.py`**

```python
def __init__(
    self,
    max_age: int = 30,
    min_hits: int = 3,
    iou_threshold: float = 0.3,
    ema_alpha: float = 0.5,
    # NEW: Re-ID support
    reid_embedder: Optional[ReIDEmbedder] = None,
    reid_cache: Optional[ReIDCache] = None,
    reid_similarity_threshold: float = 0.6,
) -> None:
    # ... existing init ...
    self.reid_embedder = reid_embedder
    self.reid_cache = reid_cache
    self.reid_similarity_threshold = reid_similarity_threshold
```

**File: `src/modules/tracking/tracker.py` - update method**

```python
def update(
    self, 
    detections: List[Dict],
    frame: Optional[np.ndarray] = None,  # NEW: for Re-ID cropping
    session_id: Optional[str] = None     # NEW: for Re-ID cache
) -> List[Dict]:
    # ... existing IoU matching ...
    
    # After IoU matching, try Re-ID for unmatched detections
    if self.reid_embedder and self.reid_cache and frame is not None:
        for d_idx in unmatched_detections:
            det = detections[d_idx]
            bbox = self._convert_detection(det)
            
            # Try to match with existing track using Re-ID
            best_track_idx = self._match_with_reid(det, bbox, frame, session_id)
            if best_track_idx is not None:
                # Reuse existing track_id
                det['track_id'] = self.tracks[best_track_idx].track_id
                matched_tracks.add(best_track_idx)
                unmatched_detections.discard(d_idx)
    
    # ... rest of existing code ...
```

## Expected Improvements

| Metric | Before | After |
|--------|--------|-------|
| Unique Tracks | 109 | ~15-20 |
| Re-ID Utilization | 0% | >50% |
| Accuracy | IoU only | IoU + Re-ID |
| Performance | Good | Similar |

## Configuration Updates

Add to `process_video_file.py`:
```python
tracker = Tracker(
    max_age=tracker_max_age,
    min_hits=tracker_min_hits,
    iou_threshold=tracker_iou_threshold,
    ema_alpha=tracker_ema_alpha,
    # NEW
    reid_embedder=reid_embedder if reid_enable else None,
    reid_cache=reid_cache if reid_enable else None,
    reid_similarity_threshold=0.6
)
```

## Testing

1. Run test video with current config
2. Compare unique track count (before/after)
3. Verify same people get same track_id across reappearances
4. Check FPS impact (<5% acceptable)

## References

- Current Re-ID implementation: `src/modules/reid/`
- Tracker implementation: `src/modules/tracking/tracker.py`
- Integration: `src/scripts/process_video_file.py`


