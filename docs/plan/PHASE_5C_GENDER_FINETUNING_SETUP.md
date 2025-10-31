# Phase 5C: Fine-tune Gender Classifier on UTKFace

## Overview
Fine-tune MobileNetV2 for face-based gender classification using UTKFace dataset to achieve 90-95% accuracy.

## Requirements

### Functional Requirements
1. Download and prepare UTKFace dataset (24,000+ images)
2. Create data loader with proper transformations
3. Fine-tune MobileNetV2 for 10 epochs
4. Save model weights for production use
5. Update `FaceGenderClassifier` to use fine-tuned weights
6. Validate accuracy on test videos

### Non-Functional Requirements
- **Accuracy**: ≥90% on UTKFace test set
- **Real-world**: ≥85% on video samples
- **Training time**: <30 minutes (10 epochs)
- **Model size**: <20MB (fits in existing infrastructure)
- **Class balance**: M:F ratio close to 1:1 in predictions

### Technical Constraints
- Use PyTorch and torchvision
- Compatible with existing `FaceGenderClassifier`
- Maintains <10ms inference latency
- No breaking changes to existing API

## User Stories

### US1: High-Accuracy Gender Classification
**As a**: System user  
**I want**: Gender predictions with ≥90% accuracy  
**So that**: Demographic analytics are reliable

**Acceptance Criteria**:
- Fine-tuned model achieves ≥90% accuracy on UTKFace validation set
- Real video test shows ≥85% accuracy
- Class distribution is balanced (not severely skewed M/F)
- Inference latency remains <10ms

### US2: Easy Model Updates
**As a**: Developer  
**I want**: To fine-tune and update model weights easily  
**So that**: We can improve accuracy over time

**Acceptance Criteria**:
- Fine-tuning script is self-contained
- Can be run with single command
- Model weights saved to standard location
- Script includes progress monitoring

## Technical Approach

### Data Preparation
```python
# UTKFace Dataset Structure
# [age]_[gender]_[race]_[date&time].jpg
# gender: 0=Male, 1=Female
# Filter: Age 18-80 for clear gender cues
```

### Model Architecture
```python
# MobileNetV2 backbone
model = models.mobilenet_v2(weights=ImageNet)

# Gender classifier head (2 classes)
model.classifier[1] = nn.Linear(1280, 2)

# Train strategy
- Freeze early layers
- Fine-tune last 3 layers
- Optimizer: Adam (lr=0.001)
- Loss: CrossEntropy
```

### Training Configuration
- **Epochs**: 10
- **Batch size**: 32
- **Optimizer**: Adam (lr=0.001)
- **Loss**: CrossEntropyLoss
- **Train/Val split**: 80/20
- **Data augmentation**: Random flip, rotation, color jitter

### Validation Metrics
- Accuracy per class (M/F)
- Overall accuracy
- Class balance ratio
- Inference latency

## Implementation Plan

### Phase 1: Data Setup
- Download UTKFace dataset
- Create data directory structure
- Implement `UTKFaceDataset` class
- Add data augmentation transforms

### Phase 2: Training Script
- Create `src/scripts/finetune_gender_classifier.py`
- Implement training loop
- Add progress logging
- Save checkpoint weights

### Phase 3: Model Integration
- Update `FaceGenderClassifier` to load fine-tuned weights
- Add fallback to ImageNet weights if not found
- Test on sample videos

### Phase 4: Validation
- Run validation on test set
- Measure real-world accuracy on videos
- Compare with baseline (current model)

## Files to Create

1. `src/scripts/finetune_gender_classifier.py` - Training script
2. `tests/unit/test_gender_finetuning.py` - Unit tests
3. `models/mobilenetv2_gender_utkface.pth` - Trained weights
4. `docs/GENDER_FINETUNING_RESULTS.md` - Results report

## Acceptance Criteria

- [ ] Model achieves ≥90% accuracy on UTKFace validation set
- [ ] Real video tests show ≥85% accuracy
- [ ] No severe class imbalance (M/F ratio 0.5-2.0)
- [ ] Inference latency <10ms maintained
- [ ] Model weights integrated into production pipeline
- [ ] Documentation complete

## References
- [UTKFace Dataset](https://susanqq.github.io/UTKFace/)
- [FacesVisionDemo](https://github.com/cocoa-ai/FacesVisionDemo)
- [Age and Gender Classification Paper](https://www.openu.ac.il/home/hassner/projects/cnn_agegender/)

