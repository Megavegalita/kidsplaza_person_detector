#!/usr/bin/env python3
"""
Fine-tune MobileNetV2 for gender classification on UTKFace dataset.

This script downloads UTKFace dataset, trains a gender classifier,
and saves the fine-tuned model weights.
"""

import argparse
import logging
from pathlib import Path
from typing import Tuple, TypedDict, List

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import models, transforms
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class _Sample(TypedDict):
    path: str
    gender: int


class UTKFaceDataset(Dataset):
    """UTKFace dataset for gender classification."""

    def __init__(self, root_dir: Path, transform=None):
        """
        Initialize UTKFace dataset.

        Args:
            root_dir: Root directory of UTKFace dataset
            transform: Image transforms to apply
        """
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples: List[_Sample] = []

        # Parse UTKFace files: [age]_[gender]_[race]_[date&time].jpg
        for filename in sorted(self.root_dir.glob("*.jpg")):
            parts = filename.stem.split("_")

            if len(parts) >= 2:
                try:
                    age = int(parts[0])
                    gender = int(parts[1])  # 0=Male, 1=Female

                    # Filter age range 18-80 for clearer gender cues
                    if 18 <= age <= 80:
                        self.samples.append({"path": str(filename), "gender": int(gender)})
                except ValueError:
                    continue

    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        Get a sample from the dataset.

        Args:
            idx: Sample index

        Returns:
            Tuple of (image, label)
        """
        sample = self.samples[idx]
        image = Image.open(sample["path"]).convert("RGB")
        label: int = int(sample["gender"])  # already int by construction

        if self.transform:
            image = self.transform(image)
        else:
            # Basic to-tensor if no transform provided
            image = transforms.ToTensor()(image)

        return image, label


def create_data_loaders(
    root_dir: Path, batch_size: int = 32, train_split: float = 0.8, num_workers: int = 4
) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation data loaders.

    Args:
        root_dir: Root directory of UTKFace dataset
        batch_size: Batch size
        train_split: Train/val split ratio
        num_workers: Number of data loader workers

    Returns:
        Tuple of (train_loader, val_loader)
    """
    # Data augmentation for training
    train_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Validation will reuse same normalization pipeline after split

    # Create datasets
    train_dataset = UTKFaceDataset(root_dir, transform=train_transform)
    # Separate validation dataset not required; using split from train_dataset

    # Split dataset
    train_size = int(train_split * len(train_dataset))
    val_size = len(train_dataset) - train_size
    train_subset, val_subset = random_split(
        train_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42),
    )

    logger.info(f"Dataset split: Train={len(train_subset)}, Val={len(val_subset)}")

    # Create data loaders
    train_loader = DataLoader(
        train_subset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    return train_loader, val_loader


def build_model(device: str = "cpu") -> nn.Module:
    """
    Build MobileNetV2 model for gender classification.

    Args:
        device: Device for model (cpu, cuda, mps)

    Returns:
        Model ready for training
    """
    # Load pretrained MobileNetV2
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

    # Replace classifier for 2 classes (Male=0, Female=1)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 2)

    # Move to device
    model = model.to(device)

    logger.info(f"Model built and moved to {device}")

    return model


def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: str,
) -> float:
    """
    Train for one epoch.

    Args:
        model: Model to train
        train_loader: Training data loader
        optimizer: Optimizer
        criterion: Loss function
        device: Device to use

    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for images, labels in tqdm(train_loader, desc="Training"):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches


def validate(
    model: nn.Module, val_loader: DataLoader, criterion: nn.Module, device: str
) -> Tuple[float, float]:
    """
    Validate model.

    Args:
        model: Model to validate
        val_loader: Validation data loader
        criterion: Loss function
        device: Device to use

    Returns:
        Tuple of (average_loss, accuracy)
    """
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="Validating"):
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    avg_loss = total_loss / len(val_loader)
    accuracy = 100 * correct / total

    return avg_loss, accuracy


def main():
    """Main training loop."""
    parser = argparse.ArgumentParser(description="Fine-tune gender classifier")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/UTKFace",
        help="Directory containing UTKFace dataset",
    )
    parser.add_argument(
        "--epochs", type=int, default=10, help="Number of training epochs"
    )
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument(
        "--output",
        type=str,
        default="models/mobilenetv2_gender_utkface.pth",
        help="Output path for saved model",
    )
    parser.add_argument(
        "--device", type=str, default="auto", help="Device to use (cpu, cuda, mps)"
    )

    args = parser.parse_args()

    # Determine device
    if args.device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
    else:
        device = args.device

    logger.info(f"Using device: {device}")

    # Check data directory
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        logger.info("Please download UTKFace dataset first:")
        logger.info("  wget https://susanqq.github.io/UTKFace.tar.gz")
        logger.info(f"  tar -xzf UTKFace.tar.gz -C {data_dir.parent}")
        return

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create data loaders
    logger.info("Creating data loaders...")
    train_loader, val_loader = create_data_loaders(data_dir, batch_size=args.batch_size)

    # Build model
    logger.info("Building model...")
    model = build_model(device)

    # Setup training
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    # Training loop
    logger.info(f"Starting training for {args.epochs} epochs...")
    best_accuracy = 0.0

    for epoch in range(args.epochs):
        logger.info(f"\nEpoch {epoch+1}/{args.epochs}")

        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        logger.info(f"Train loss: {train_loss:.4f}")

        # Validate
        val_loss, accuracy = validate(model, val_loader, criterion, device)
        logger.info(f"Val loss: {val_loss:.4f}, Val accuracy: {accuracy:.2f}%")

        # Save best model
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save(model.state_dict(), output_path)
            logger.info(f"Saved best model (accuracy: {accuracy:.2f}%)")

    logger.info(f"\nTraining complete! Best accuracy: {best_accuracy:.2f}%")
    logger.info(f"Model saved to: {output_path}")


if __name__ == "__main__":
    main()
