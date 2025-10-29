# Face-Based Gender Classification Test Videos

## Generated Videos for Review

### Config A - Strict
**Parameters:**
- `--gender-min-confidence 0.6`
- `--gender-voting-window 15`

**File:** `output/gender_face_configs/Config_A_Strict/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4` (51MB)

**Characteristics:**
- Highest confidence threshold (0.6)
- Large voting window (15)
- Most conservative filtering

---

### Config B - Balanced
**Parameters:**
- `--gender-min-confidence 0.4`
- `--gender-voting-window 10`

**File:** `output/gender_face_configs/Config_B_Balanced/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4` (115MB)

**Characteristics:**
- Medium confidence threshold (0.4)
- Medium voting window (10)
- Balanced between accuracy and coverage

---

### Config C - Permissive
**Parameters:**
- `--gender-min-confidence 0.3`
- `--gender-voting-window 7`

**File:** `output/gender_face_configs/Config_C_Permissive/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4` (109MB)

**Characteristics:**
- Lower confidence threshold (0.3)
- Smaller voting window (7)
- More permissive, higher coverage

---

## How to Review

1. **Watch each video** to visually inspect gender classification accuracy
2. **Check overlay stats** (Male/Female counts on screen)
3. **Observe bounding box labels** (format: `ID<track> - person: <conf> | Male/Female(<conf>)`)
4. **Note visual accuracy** - do the gender labels match what you see?

## Recommendation

Based on your review, choose the config with:
- **Best visual accuracy** (labels match reality)
- **Good coverage** (not too many "Unknown")
- **Stable predictions** (gender doesn't flip frequently)

## Implementation

Once you choose the best config, we'll update the default parameters in `src/scripts/process_video_file.py`.


