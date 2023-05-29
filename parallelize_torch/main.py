# Adapted from Ray's template
from typing import Dict

import ray
from ray.air import session

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor

import ray.train as train
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig, RunConfig

from model import BasicNeuralNetwork
from config import MainConfig

# Download training data from open datasets.
training_data = datasets.FashionMNIST(
    root="~/data",
    train=True,
    download=False,
    transform=ToTensor(),
)

# Download test data from open datasets.
test_data = datasets.FashionMNIST(
    root="~/data",
    train=False,
    download=False,
    transform=ToTensor(),
)

def train_epoch(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset) // session.get_world_size()
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        # Compute prediction error
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


def validate_epoch(dataloader, model, loss_fn):
    size = len(dataloader.dataset) // session.get_world_size()
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
    test_loss /= num_batches
    correct /= size
    print(
        f"Test Error: \n "
        f"Accuracy: {(100 * correct):>0.1f}%, "
        f"Avg loss: {test_loss:>8f} \n"
    )
    return test_loss


def train_func(config: Dict):
    batch_size = config["batch_size"]
    lr = config["lr"]
    epochs = config["epochs"]

    worker_batch_size = batch_size // session.get_world_size()

    # Create data loaders.
    train_dataloader = DataLoader(training_data, batch_size=worker_batch_size)
    test_dataloader = DataLoader(test_data, batch_size=worker_batch_size)

    train_dataloader = train.torch.prepare_data_loader(train_dataloader)
    test_dataloader = train.torch.prepare_data_loader(test_dataloader)

    # Create model.
    model = BasicNeuralNetwork()
    model = train.torch.prepare_model(model)

    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)

    for _ in range(epochs):
        train_epoch(train_dataloader, model, loss_fn, optimizer)
        loss = validate_epoch(test_dataloader, model, loss_fn)
        session.report(dict(loss=loss))


def train_fashion_mnist(num_workers=2, use_gpu=False):
    trainer = TorchTrainer(
        train_loop_per_worker=train_func,
        train_loop_config={"lr": 1e-3, "batch_size": 64, "epochs": 10},
        scaling_config=ScalingConfig(num_workers=num_workers, use_gpu=use_gpu),
    )
    result = trainer.fit()
    print(f"Last result: {result.metrics}")


if __name__ == "__main__":
    config = MainConfig()
    # parser = argparse.ArgumentParser()
    # # parser.add_argument(
    # #     "--address", required=False, type=str, help="the address to use for Ray"
    # # )
    # parser.add_argument(
    #     "--num-workers",
    #     "-n",
    #     type=int,
    #     default=2,
    #     help="Sets number of workers for training.",
    # )
    # parser.add_argument(
    #     "--use-gpu", action="store_true", default=False, help="Enables GPU training"
    # )
    # parser.add_argument(
    #     "--smoke-test",
    #     action="store_true",
    #     default=False,
    #     help="Finish quickly for testing.",
    # )

    # args, _ = parser.parse_known_args()


    # if args.smoke_test:
    #     # 2 workers + 1 for trainer.
    #     ray.init(num_cpus=3)
    #     train_fashion_mnist()
    # else:
    #     ray.init()
    #     train_fashion_mnist(num_workers=args.num_workers, use_gpu=args.use_gpu)

    if config.smoke_test:
        # 2 workers + 1 for trainer
        ray.init(config.num_cpus_smoke_test)
        train_fashion_mnist()
    else:
        ray.init()
        train_fashion_mnist(num_workers=config.num_workers, use_gpu=config.use_gpu)