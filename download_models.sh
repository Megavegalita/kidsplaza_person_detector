#!/bin/bash
# Script to download OpenCV DNN age/gender models manually

set -e

MODELS_DIR="models/age_gender_opencv"

# Create directory if not exists
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

echo "📥 Downloading OpenCV DNN models..."
echo ""

# Age deploy prototxt
echo "1/4: Downloading age_deploy.prototxt..."
if [ ! -f "age_deploy.prototxt" ]; then
    curl -L -o age_deploy.prototxt \
        https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt || \
    curl -L -o age_deploy.prototxt \
        https://github.com/opencv/opencv/raw/4.x/samples/dnn/age_deploy.prototxt
    if [ -f "age_deploy.prototxt" ]; then
        echo "   ✅ Downloaded age_deploy.prototxt"
    else
        echo "   ❌ Failed to download age_deploy.prototxt"
        echo "   Please download manually from: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/age_deploy.prototxt"
    fi
else
    echo "   ✅ age_deploy.prototxt already exists"
fi

# Age model (large file ~43MB)
echo "2/4: Downloading age_net.caffemodel (~43MB)..."
if [ ! -f "age_net.caffemodel" ]; then
    curl -L -o age_net.caffemodel \
        https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel || \
    echo "   ⚠️  Direct download failed. Please download manually from:"
    echo "      https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/age_net.caffemodel"
    if [ -f "age_net.caffemodel" ]; then
        echo "   ✅ Downloaded age_net.caffemodel"
    fi
else
    echo "   ✅ age_net.caffemodel already exists"
fi

# Gender deploy prototxt
echo "3/4: Downloading gender_deploy.prototxt..."
if [ ! -f "gender_deploy.prototxt" ]; then
    curl -L -o gender_deploy.prototxt \
        https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt || \
    curl -L -o gender_deploy.prototxt \
        https://github.com/opencv/opencv/raw/4.x/samples/dnn/gender_deploy.prototxt
    if [ -f "gender_deploy.prototxt" ]; then
        echo "   ✅ Downloaded gender_deploy.prototxt"
    else
        echo "   ❌ Failed to download gender_deploy.prototxt"
        echo "   Please download manually from: https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/gender_deploy.prototxt"
    fi
else
    echo "   ✅ gender_deploy.prototxt already exists"
fi

# Gender model (~3.4MB)
echo "4/4: Downloading gender_net.caffemodel (~3.4MB)..."
if [ ! -f "gender_net.caffemodel" ]; then
    curl -L -o gender_net.caffemodel \
        https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel || \
    echo "   ⚠️  Direct download failed. Please download manually from:"
    echo "      https://github.com/opencv/opencv_extra/raw/4.x/testdata/dnn/gender_net.caffemodel"
    if [ -f "gender_net.caffemodel" ]; then
        echo "   ✅ Downloaded gender_net.caffemodel"
    fi
else
    echo "   ✅ gender_net.caffemodel already exists"
fi

echo ""
echo "📊 Summary:"
ls -lh | grep -E "\.(prototxt|caffemodel)$" || echo "No files found"

echo ""
echo "✅ Download script completed!"
echo ""
echo "⚠️  If any files failed to download, please download manually:"
echo "   1. Visit: https://github.com/opencv/opencv/tree/4.x/samples/dnn"
echo "   2. Visit: https://github.com/opencv/opencv_extra/tree/4.x/testdata/dnn"
echo "   3. Save files to: $(pwd)"


