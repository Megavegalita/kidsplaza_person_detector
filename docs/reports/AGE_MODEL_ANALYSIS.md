# Phân Tích và Cải Thiện Age Estimation Models cho Người Châu Á

**Date**: 2025-11-02  
**Focus**: Cải thiện độ chính xác age estimation cho người châu Á

## 🔍 Models Phân Tích

### 1. **prithivMLmods/facial-age-detection** ⭐ RECOMMENDED
**Source**: Hugging Face  
**Accuracy**: 82.25% overall  
**Age Groups**: 8 classes (01-10, 11-20, 21-30, 31-40, 41-50, 51-60, 61-70, 80+)  
**Dataset**: Diverse (includes Asian faces)  
**Format**: Classification model  
**Pros**:
- High accuracy (82.25%)
- Well-structured age ranges
- Works well with Asian faces
- Available on Hugging Face

**Cons**:
- Age groups (not exact age)
- Need to map to age ranges

### 2. **LisanneH/AgeEstimation**
**Source**: Hugging Face  
**Dataset**: UTKFace (~24,000 images)  
**MAE**: 5.2 years  
**Format**: Regression model  
**Pros**:
- Exact age prediction (regression)
- Good MAE (5.2 years)
- UTKFace includes diverse faces

**Cons**:
- May not be specifically optimized for Asian faces
- Smaller dataset than AFAD

### 3. **fanclan/age-gender-model**
**Source**: Hugging Face  
**Features**: Age + Gender combined  
**Format**: ResNet50 based  
**Pros**:
- Combined age and gender
- Efficient single model

**Cons**:
- May not be Asian-optimized
- Unknown accuracy

### 4. **AFAD-trained Models**
**Dataset**: AFAD (160K+ Asian faces)  
**Best Practice**: Use models trained on AFAD for Asian faces  
**Availability**: Need to find pretrained models or train custom

### 5. **Wide ResNet for Asian Faces**
**Research**: "Joint Age Estimation and Gender Classification of Asian Faces Using Wide ResNet"  
**Performance**: Promising results for Asian faces  
**Format**: Wide ResNet architecture

## 🎯 Recommended Strategy

### Priority Order:
1. **prithivMLmods/facial-age-detection** (Best overall for Asian faces)
2. **LisanneH/AgeEstimation** (Good regression model)
3. **fanclan/age-gender-model** (If combined needed)
4. **Custom AFAD-trained model** (Best but needs training)

## 🔧 Implementation Plan

### 1. **Add prithivMLmods/facial-age-detection** ✅
- Priority 1 model for Asian faces
- 8 age groups classification
- Map to age ranges for display

### 2. **Improve Age Range Mapping**
- Better mapping from classification to ranges
- Handle 8-class model properly
- Display as age ranges (e.g., "21-30")

### 3. **Model Priority System**
- Try best models first
- Fallback gracefully
- Log which model is used

### 4. **AFAD Dataset Consideration**
- Future: Fine-tune on AFAD if needed
- Current: Use best available pretrained


