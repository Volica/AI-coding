from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
MODEL_DIR = PROJECT_DIR / "models"
MODEL_PATH = MODEL_DIR / "mnist_cnn.pt"
RANDOM_SEED = 42
MNIST_MEAN = (0.1307,)
MNIST_STD = (0.3081,)


def get_torchvision() -> tuple[Any, Any]:
    try:
        from torchvision import datasets, transforms
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("Missing dependency: torchvision. Run `pip install -r requirements.txt` first.") from exc
    return datasets, transforms


class MNISTCNN(nn.Module):
    """A compact LeNet-style CNN for 28x28 grayscale digit images."""

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.25),
            nn.Linear(128 * 7 * 7, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(128, 10),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


def set_seed(seed: int = RANDOM_SEED) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_transforms(use_augmentation: bool) -> Any:
    _, transforms = get_torchvision()
    steps: list[object] = []
    if use_augmentation:
        steps.append(transforms.RandomAffine(degrees=10, translate=(0.08, 0.08), scale=(0.95, 1.05)))
    steps.extend(
        [
            transforms.ToTensor(),
            transforms.Normalize(MNIST_MEAN, MNIST_STD),
        ]
    )
    return transforms.Compose(steps)


def split_indices(total_size: int, val_ratio: float, max_train_samples: int | None) -> tuple[list[int], list[int]]:
    generator = torch.Generator().manual_seed(RANDOM_SEED)
    indices = torch.randperm(total_size, generator=generator).tolist()
    if max_train_samples is not None:
        indices = indices[: max(2, min(max_train_samples, total_size))]
    val_size = max(1, int(len(indices) * val_ratio))
    val_size = min(val_size, len(indices) - 1)
    return indices[val_size:], indices[:val_size]


def create_dataloaders(
    batch_size: int,
    val_ratio: float,
    download: bool,
    max_train_samples: int | None,
    num_workers: int,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    datasets, _ = get_torchvision()
    train_aug = datasets.MNIST(
        root=DATA_DIR,
        train=True,
        transform=build_transforms(use_augmentation=True),
        download=download,
    )
    train_eval = datasets.MNIST(
        root=DATA_DIR,
        train=True,
        transform=build_transforms(use_augmentation=False),
        download=download,
    )
    test_dataset = datasets.MNIST(
        root=DATA_DIR,
        train=False,
        transform=build_transforms(use_augmentation=False),
        download=download,
    )

    train_indices, val_indices = split_indices(len(train_aug), val_ratio, max_train_samples)
    train_loader = DataLoader(
        Subset(train_aug, train_indices),
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        Subset(train_eval, val_indices),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    return train_loader, val_loader, test_loader


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        batch_size = labels.size(0)
        running_loss += loss.item() * batch_size
        correct += (logits.argmax(dim=1) == labels).sum().item()
        total += batch_size
    return running_loss / total, correct / total


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> tuple[float, float, list[list[int]]]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    confusion = torch.zeros(10, 10, dtype=torch.int64)
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        logits = model(images)
        loss = criterion(logits, labels)
        predictions = logits.argmax(dim=1)

        batch_size = labels.size(0)
        running_loss += loss.item() * batch_size
        correct += (predictions == labels).sum().item()
        total += batch_size
        for true_label, predicted_label in zip(labels.cpu(), predictions.cpu(), strict=True):
            confusion[int(true_label), int(predicted_label)] += 1
    return running_loss / total, correct / total, confusion.tolist()


def write_history(history: list[dict[str, float]], output_dir: Path) -> None:
    if not history:
        return
    with (output_dir / "training_history.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)


def train(args: argparse.Namespace) -> None:
    set_seed(args.seed)
    OUTPUT_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)

    device = get_device()
    train_loader, val_loader, test_loader = create_dataloaders(
        batch_size=args.batch_size,
        val_ratio=args.val_ratio,
        download=not args.no_download,
        max_train_samples=args.max_train_samples,
        num_workers=args.num_workers,
    )

    model = MNISTCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

    best_val_accuracy = 0.0
    history: list[dict[str, float]] = []
    for epoch in range(1, args.epochs + 1):
        train_loss, train_accuracy = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_accuracy, _ = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        row = {
            "epoch": float(epoch),
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
            "learning_rate": scheduler.get_last_lr()[0],
        }
        history.append(row)
        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"train loss {train_loss:.4f}, acc {train_accuracy:.4f} | "
            f"val loss {val_loss:.4f}, acc {val_accuracy:.4f}"
        )
        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(model.state_dict(), MODEL_PATH)

    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    test_loss, test_accuracy, confusion = evaluate(model, test_loader, criterion, device)
    write_history(history, OUTPUT_DIR)

    summary = {
        "model": "MNISTCNN",
        "device": str(device),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "best_val_accuracy": round(best_val_accuracy, 6),
        "test_loss": round(test_loss, 6),
        "test_accuracy": round(test_accuracy, 6),
        "confusion_matrix": confusion,
        "model_path": str(MODEL_PATH),
    }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nBest validation accuracy: {best_val_accuracy:.4f}")
    print(f"Test accuracy: {test_accuracy:.4f}")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metrics to: {OUTPUT_DIR / 'metrics.json'}")


def load_model(model_path: Path, device: torch.device) -> MNISTCNN:
    model = MNISTCNN().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model


@torch.no_grad()
def predict_image(image_path: Path, model_path: Path) -> None:
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}. Train the model first.")
    from PIL import Image

    _, transforms = get_torchvision()
    device = get_device()
    model = load_model(model_path, device)
    transform = transforms.Compose(
        [
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((28, 28)),
            transforms.ToTensor(),
            transforms.Normalize(MNIST_MEAN, MNIST_STD),
        ]
    )
    image = Image.open(image_path)
    tensor = transform(image).unsqueeze(0).to(device)
    logits = model(tensor)
    probabilities = torch.softmax(logits, dim=1).squeeze(0).cpu()
    prediction = int(probabilities.argmax().item())
    confidence = float(probabilities[prediction].item())
    print(f"Prediction: {prediction}")
    print(f"Confidence: {confidence:.4f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and use a CNN model for MNIST digit recognition.")
    parser.add_argument("--run", action="store_true", help="Train and evaluate the MNIST model.")
    parser.add_argument("--predict", type=Path, help="Predict one local digit image with a trained model.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=128, help="Training batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Adam weight decay.")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio from the training set.")
    parser.add_argument("--max-train-samples", type=int, help="Limit samples for a quick smoke test.")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers. Use 0 on Windows if unsure.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed.")
    parser.add_argument("--model-path", type=Path, default=MODEL_PATH, help="Path to a trained model file.")
    parser.add_argument("--no-download", action="store_true", help="Disable MNIST download and use existing data only.")
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    if cli_args.run:
        train(cli_args)
    elif cli_args.predict:
        predict_image(cli_args.predict, cli_args.model_path)
    else:
        print("Use `python mnist_model.py --run` to train, or `python mnist_model.py --predict path/to/image.png`.")
