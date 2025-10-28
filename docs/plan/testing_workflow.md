# Testing Workflow: Video File First, Then Live Camera

## 📋 Overview

Tài liệu mô tả quy trình testing tuân thủ DEVELOPER_CHECKLIST và đảm bảo chất lượng code trước khi deploy lên camera thật.

## 🎯 Core Principle

**KHÔNG tiến hành live camera testing cho đến khi:**
- Video file testing hoàn thành 100%
- Tất cả metrics đạt target
- Không có critical bugs
- Performance benchmarks đạt yêu cầu
- Test reports được review và approve

## 🔄 Testing Flow

```
┌─────────────────────────────────────────┐
│  Phase 1-3: Development & Implementation │
│  • Setup environment                     │
│  • Implement modules                     │
│  • Write unit tests                      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Phase 3.5: OFFLINE VIDEO FILE TESTING  │
│  • Process video files                   │
│  • Validate detection accuracy           │
│  • Test tracking consistency             │
│  • Generate annotated outputs            │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Phases 4-6: Continue on Video Files   │
│  • Demographics estimation               │
│  • Database operations                   │
│  • Full pipeline testing                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  ✅ Validation Complete                  │
│  • All tests pass                       │
│  • Performance targets met              │
│  • No critical bugs                     │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Phase 7: LIVE CAMERA INTEGRATION       │
│  • Real-time RTSP streams               │
│  • Multi-channel support                 │
│  • Production deployment                 │
└─────────────────────────────────────────┘
```

---

## 📊 Phase 3.5: Offline Video File Testing

### Objectives

1. **Validation**: Verify all modules work correctly
2. **Accuracy**: Measure detection and tracking accuracy
3. **Performance**: Benchmark inference speed and resource usage
4. **Debugging**: Find and fix issues in controlled environment
5. **Documentation**: Generate test reports and visualizations

### Test Data

**Input Video**: `input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`

**Output Directory**:
```
output/
├── videos/              # Annotated output videos
│   ├── detection_annotated.mp4
│   ├── tracking_annotated.mp4
│   └── full_pipeline_annotated.mp4
├── reports/             # Test reports
│   ├── detection_report.json
│   ├── performance_report.json
│   └── accuracy_report.json
└── visualizations/      # Charts and graphs
    ├── detection_timeline.png
    └── tracking_paths.png
```

### Implementation

#### Script: `src/scripts/process_video_file.py`

**Features**:
- Read video file from input directory
- Process through detection pipeline
- Apply tracking algorithm
- Estimate demographics
- Save to database (optional)
- Generate annotated output video
- Create performance reports

**Usage**:
```bash
# Process video file with full pipeline
python src/scripts/process_video_file.py input/video/test_video.mp4

# With specific options
python src/scripts/process_video_file.py input/video/test_video.mp4 \
    --output output/videos \
    --conf-threshold 0.5 \
    --save-db \
    --generate-reports
```

### Test Cases

#### 1. Detection Testing
- [ ] Load model successfully
- [ ] Process frames and detect persons
- [ ] Filter by confidence threshold
- [ ] Measure inference speed (target: >10 FPS)
- [ ] Validate detection accuracy (>90%)
- [ ] Test with various lighting conditions

#### 2. Tracking Testing
- [ ] Assign track IDs consistently
- [ ] Maintain tracks across frames
- [ ] Handle occlusions properly
- [ ] Re-identify persons after occlusion
- [ ] Test with multiple persons
- [ ] Validate track persistence

#### 3. Demographics Testing
- [ ] Extract face regions correctly
- [ ] Estimate age with accuracy >80%
- [ ] Estimate gender with accuracy >85%
- [ ] Handle edge cases (profile view, low resolution)
- [ ] Validate confidence scores

#### 4. Database Testing
- [ ] Insert detection data correctly
- [ ] Query historical data
- [ ] Test batch operations
- [ ] Validate data integrity
- [ ] Test Redis caching

### Metrics to Track

**Performance Metrics**:
- FPS (Frames Per Second)
- Inference time per frame
- Memory usage
- CPU/GPU utilization
- Total processing time

**Accuracy Metrics**:
- Detection accuracy (%)
- False positive rate
- False negative rate
- Tracking consistency
- Age estimation error (MAE)
- Gender estimation accuracy

### Test Reports

#### Detection Report (`detection_report.json`)
```json
{
  "total_frames": 3000,
  "total_persons_detected": 1523,
  "average_detections_per_frame": 0.508,
  "detection_accuracy": 92.5,
  "processing_time_seconds": 245.6,
  "average_fps": 12.2,
  "memory_usage_mb": 1234,
  "gpu_utilization_percent": 85.3
}
```

#### Tracking Report (`tracking_report.json`)
```json
{
  "total_tracks": 342,
  "average_track_length_frames": 4.4,
  "longest_track_frames": 87,
  "tracking_consistency": 94.2,
  "occlusions_handled": 23,
  "re_identifications": 8
}
```

#### Demographics Report (`demographics_report.json`)
```json
{
  "total_with_age": 1523,
  "total_with_gender": 1523,
  "age_mae": 5.2,
  "gender_accuracy": 87.3,
  "age_distribution": {
    "0-17": 234,
    "18-35": 678,
    "36-55": 523,
    "56+": 88
  },
  "gender_distribution": {
    "male": 823,
    "female": 700
  }
}
```

---

## ✅ Pre-Live Camera Checklist

### Code Quality
- [ ] All unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Code formatted with Black
- [ ] No linter errors
- [ ] Type checking passes

### Video File Testing
- [ ] Video file processing script implemented
- [ ] All test cases pass on video files
- [ ] Performance metrics meet targets
- [ ] Accuracy metrics meet targets
- [ ] Annotated videos generated and reviewed
- [ ] Test reports generated

### Module Validation
- [ ] Detection module validated on video
- [ ] Tracking module validated on video
- [ ] Demographics module validated on video
- [ ] Database operations tested on video data
- [ ] Error handling tested

### Documentation
- [ ] Test reports documented
- [ ] Performance benchmarks documented
- [ ] Known issues documented
- [ ] Rollback plan prepared

### Risk Mitigation
- [ ] Backups created
- [ ] Monitoring setup
- [ ] Error recovery tested
- [ ] Resource limits defined

---

## 🚀 Proceeding to Live Camera

### Prerequisites

1. **Video File Testing**: 100% complete
2. **Metrics**: All targets met
3. **Reports**: Review and approval
4. **No Critical Bugs**: All issues resolved
5. **Code Review**: Peer review completed

### Steps

1. **Preparation**:
   - Backup current state
   - Setup monitoring
   - Prepare rollback plan

2. **Single Channel Test**:
   - Test with 1 camera channel first
   - Validate against video results
   - Monitor performance

3. **Multi-Channel Test**:
   - Test with all 4 channels
   - Measure resource usage
   - Check for stability

4. **Production Deployment**:
   - Deploy with monitoring
   - Monitor for issues
   - Collect feedback

---

## 📝 Test Data Requirements

### Video Files Needed

1. **Primary Test Video**: 
   - `Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
   - Contains real footage from camera

2. **Additional Test Scenarios**:
   - Multiple persons
   - Varying lighting conditions
   - Different camera angles
   - Occlusions and interactions
   - Various demographics

### Sample Clips

Create short clips (30-60 seconds) for specific tests:
- `test_multiple_persons.mp4` - Multiple people detection
- `test_occlusion.mp4` - Tracking through occlusion
- `test_demographics.mp4` - Various age/gender groups
- `test_low_light.mp4` - Low light conditions

---

## 🎯 Success Criteria

### Phase 3.5 Success (Video File Testing)
- ✅ Detection accuracy > 90%
- ✅ Tracking consistency > 90%
- ✅ Demographics accuracy > 80%
- ✅ Processing speed > 10 FPS
- ✅ No crashes or errors
- ✅ All test reports generated

### Phase 7 Success (Live Camera)
- ✅ Real-time processing achieved
- ✅ All 4 channels working
- ✅ Performance matches video testing
- ✅ Stability over extended periods
- ✅ Production-ready deployment

---

## 📚 Related Documents

- [Development Plan](development_plan.md) - Full development plan
- [Developer Checklist](../DEVELOPER_CHECKLIST.md) - Quality standards
- [Best Practices](../standards/python_production_best_practices.md) - Coding standards

---

**Remember**: Quality over speed. Complete video file testing thoroughly before live integration. 🚀

