#!/bin/bash
# Download OpenCV DNN age/gender models from Isfhan/age-gender-detection repository
# This repository has all the model files we need!

set -e

MODELS_DIR="models/age_gender_opencv"
BASE_URL="https://raw.githubusercontent.com/Isfhan/age-gender-detection/master"

# Create directory if not exists
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

echo "📥 Downloading OpenCV DNN models from Isfhan/age-gender-detection..."
echo "Repository: https://github.com/Isfhan/age-gender-detection"
echo ""

# Age deploy prototxt
echo "1/4: age_deploy.prototxt..."
if [ ! -f "age_deploy.prototxt" ] || [ $(wc -c < age_deploy.prototxt 2>/dev/null || echo 0) -lt 100 ]; then
    curl -L -o age_deploy.prototxt "${BASE_URL}/age_deploy.prototxt"
    if [ -f "age_deploy.prototxt" ] && [ $(wc -c < age_deploy.prototxt) -gt 100 ]; then
        echo "   ✅ Downloaded ($(wc -c < age_deploy.prototxt | awk '{print int($1/1024)}')KB)"
    else
        echo "   ❌ Download failed"
        exit 1
    fi
else
    echo "   ✅ Already exists"
fi

# Age model (large file)
echo "2/4: age_net.caffemodel (~25-43MB)..."
if [ ! -f "age_net.caffemodel" ] || [ $(wc -c < age_net.caffemodel 2>/dev/null || echo 0) -lt 1000000 ]; then
    curl -L -o age_net.caffemodel "${BASE_URL}/age_net.caffemodel"
    if [ -f "age_net.caffemodel" ] && [ $(wc -c < age_net.caffemodel) -gt 1000000 ]; then
        SIZE_MB=$(wc -c < age_net.caffemodel | awk '{print int($1/1024/1024)}')
        echo "   ✅ Downloaded (${SIZE_MB}MB)"
    else
        echo "   ❌ Download failed or file too small"
        exit 1
    fi
else
    echo "   ✅ Already exists"
fi

# Gender deploy prototxt
echo "3/4: gender_deploy.prototxt..."
if [ ! -f "gender_deploy.prototxt" ] || [ $(wc -c < gender_deploy.prototxt 2>/dev/null || echo 0) -lt 100 ]; then
    curl -L -o gender_deploy.prototxt "${BASE_URL}/gender_deploy.prototxt"
    if [ -f "gender_deploy.prototxt" ] && [ $(wc -c < gender_deploy.prototxt) -gt 100 ]; then
        echo "   ✅ Downloaded ($(wc -c < gender_deploy.prototxt | awk '{print int($1/1024)}')KB)"
    else
        echo "   ❌ Download failed"
        exit 1
    fi
else
    echo "   ✅ Already exists"
fi

# Gender model
echo "4/4: gender_net.caffemodel (~3.4MB)..."
if [ ! -f "gender_net.caffemodel" ] || [ $(wc -c < gender_net.caffemodel 2>/dev/null || echo 0) -lt 1000000 ]; then
    curl -L -o gender_net.caffemodel "${BASE_URL}/gender_net.caffemodel"
    if [ -f "gender_net.caffemodel" ] && [ $(wc -c < gender_net.caffemodel) -gt 1000000 ]; then
        SIZE_MB=$(wc -c < gender_net.caffemodel | awk '{print int($1/1024/1024)}')
        echo "   ✅ Downloaded (${SIZE_MB}MB)"
    else
        echo "   ❌ Download failed or file too small"
        exit 1
    fi
else
    echo "   ✅ Already exists"
fi

echo ""
echo "📊 Summary:"
ls -lh | grep -E "\.(prototxt|caffemodel)$" | awk '{printf "   %-25s %8s\n", $9, $5}'

echo ""
if [ -f "age_deploy.prototxt" ] && [ -f "age_net.caffemodel" ] && \
   [ -f "gender_deploy.prototxt" ] && [ -f "gender_net.caffemodel" ]; then
    echo "✅ All files downloaded successfully!"
    echo "✅ Models ready to use!"
else
    echo "⚠️  Some files are missing. Please check and retry."
    exit 1
fi


