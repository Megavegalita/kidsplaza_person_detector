#!/bin/bash
# Download and extract UTKFace dataset

echo "Downloading UTKFace dataset..."

# Create data directory
mkdir -p data

# Download dataset
cd data
if [ ! -f "UTKFace.tar.gz" ]; then
    echo "Downloading UTKFace.tar.gz (this may take a few minutes)..."
    wget https://susanqq.github.io/UTKFace.tar.gz
else
    echo "UTKFace.tar.gz already exists"
fi

# Extract
if [ ! -d "UTKFace" ]; then
    echo "Extracting UTKFace dataset..."
    tar -xzf UTKFace.tar.gz
    echo "✅ Dataset extracted to data/UTKFace/"
else
    echo "✅ Dataset already extracted"
fi

# Count images
IMG_COUNT=$(find UTKFace -name "*.jpg" | wc -l)
echo "Dataset contains $IMG_COUNT images"

cd ..

echo ""
echo "✅ UTKFace dataset ready!"
echo "   Location: data/UTKFace/"
echo "   Next step: python src/scripts/finetune_gender_classifier.py"

