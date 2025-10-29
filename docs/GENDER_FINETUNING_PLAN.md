# Gender Classification Fine-tuning Plan

## Problem Analysis

### Current Issues
1. **MobileNetV2 with ImageNet weights**: Not trained for gender classification
2. **Class imbalance**: Severe M/F imbalance in predictions
3. **Low accuracy**: Visual inspection shows incorrect predictions

### Root Cause
The current `FaceGenderClassifier` uses MobileNetV2 pretrained on ImageNet (object classification), NOT on gender classification. This is why:
- Class 0 ≠ Female, Class 1 ≠ Male (mapping is arbitrary)
- ImageNet features are optimized for object recognition, not gender
- Random predictions due to non-trained classifier head

## Solution: Fine-tune on UTKFace Dataset

### Dataset
**UTKFace** (University of Tennessee and Knoxville):
- 24,000+ labeled face images
- Age and gender annotations
- Format: `[age]_[gender]_[race]_[date&time].jpg`
- Gender: 0 = Male, 1 = Female

### Model Architecture
```python
# Use MobileNetV2 backbone
model = models.mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)

# Replace classifier for gender (2 classes)
model.classifier[1] = nn.Linear(1280, 2)  # M=0, F=1

# Fine-tune for gender classification
```

## Implementation Steps

### Step 1: Download UTKFace Dataset
```bash
# Create data directory
mkdir -p data/UTKFace

# Download dataset
wget https://susanqq.github.io/UTKFace.tar.gz
tar -xzf UTKFace.tar.gz -C data/

# Dataset structure:
# data/UTKFace/
#   ├── 0_0_0_20170117174508125.jpg.chip.jpg
#   ├── 39_1_2_20170117174527397.jpg.chip.jpg
#   └── ...
```

### Step 2: Prepare Data Loader
```python
# create src/scripts/finetune_gender_classifier.py

from torch.utils.data import Dataset, DataLoader
from PIL import Image
import os
import re

class UTKFaceDataset(Dataset):
    """UTKFace dataset for gender classification."""
    
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        
        for filename in os.listdir(root_dir):
            if filename.endswith('.jpg'):
                # Parse: [age]_[gender]_[race]_[date].jpg
                parts = filename.replace('.chip.jpg', '').split('_')
                if len(parts) >= 2:
                    age = int(parts[0])
                    gender = int(parts[1])  # 0=Male, 1=Female
                    
                    # Only use age range 18-80 for clearer gender cues
                    if 18 <= age <= 80:
                        self.samples.append({
                            'path': os.path.join(root_dir, filename),
                            'gender': gender
                        })
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        image = Image.open(sample['path']).convert('RGB')
        label = sample['gender']
        
        if self.transform:
            image = self.transform(image)
        
        return image, label
```

### Step 3: Fine-tune Model
```python
# Load pretrained MobileNetV2
model = models.mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)

# Replace classifier
model.classifier[1] = nn.Linear(1280, 2)

# Setup training
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Train for 10 epochs
for epoch in range(10):
    model.train()
    for images, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    
    # Validate
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    print(f"Epoch {epoch}: Accuracy = {100 * correct / total:.2f}%")

# Save fine-tuned model
torch.save(model.state_dict(), 'models/mobilenetv2_gender_utkface.pth')
```

### Step 4: Update FaceGenderClassifier
```python
# In src/modules/demographics/face_gender_classifier.py

def _build_model(self) -> nn.Module:
    """Build MobileNetV2 model for gender classification."""
    # Load pretrained MobileNetV2 from ImageNet
    base_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    
    # Replace final classifier for 2 classes
    in_features = base_model.classifier[1].in_features
    base_model.classifier[1] = nn.Linear(in_features, 2)
    
    # Try to load fine-tuned UTKFace weights
    pretrained_path = Path(__file__).parent.parent.parent / 'models' / 'mobilenetv2_gender_utkface.pth'
    
    if pretrained_path.exists():
        base_model.load_state_dict(torch.load(str(pretrained_path), map_location=self.device))
        logger.info("✅ Loaded fine-tuned UTKFace gender weights")
    else:
        logger.warning("⚠️ Using ImageNet weights (not fine-tuned for gender)")
    
    base_model = base_model.to(self.device)
    return base_model
```

## Expected Results
- **Accuracy**: 90-95% on UTKFace test set
- **Real-world**: ~85-90% on your video test cases
- **Class balance**: Proper M/F distribution
- **Latency**: <10ms per face crop

## Next Steps
1. Download UTKFace dataset
2. Run fine-tuning script
3. Test on sample video
4. Compare with current results

## References
- [FacesVisionDemo](https://github.com/cocoa-ai/FacesVisionDemo) - CoreML gender classification
- [UTKFace Dataset](https://susanqq.github.io/UTKFace/) - Age and gender labeled dataset
- [Age and Gender Classification Paper](https://www.openu.ac.il/home/hassner/projects/cnn_agegender/) - Original research

