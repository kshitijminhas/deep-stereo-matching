import argparse
import os
import time

import numpy as np
import torch
from torch import nn, optim
from torch.utils.data import DataLoader

from data import StereoDataset
from model import Model
from utils import loss_function, pixel_accuracy

half_range = 100

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, default='data/training')
parser.add_argument("--preprocess", type=str, default='preprocess/debug_15')
parser.add_argument("--checkpoint", type=str, default='checkpoint.pkl')
parser.add_argument("--batch_size", type=int, default=128)
parser.add_argument("--pixel_dist", type=int, default=2)
args = parser.parse_args()

batch_size = args.batch_size
checkpoint = args.checkpoint
pixel_dist = args.pixel_dist

torch.manual_seed(42)
np.random.seed(42)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

model = Model(3, half_range*2+1).to(device)
model.load_state_dict(torch.load(checkpoint))
test_dataset = StereoDataset(
    util_root=args.preprocess,
    data_root=args.data,
    filename='tr_160_18_100.bin',
    start_sample=40000 * 128,
    num_samples=50000,
)

test_data = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
class_weights = torch.Tensor([1, 4, 10, 4, 1]).to(device)
targets = np.tile(half_range + 1, (batch_size, 1))
target_batch = torch.tensor(targets, dtype=torch.int32)


print("%d test samples" % len(test_dataset))

model.eval()
losses = np.array([])
accuracies = np.array([])
for batch in test_data:
    left_img = batch['left'].to(device)
    right_img = batch['right'].to(device)
    target = target_batch.to(device)

    _, _, pred = model(left_img, right_img)
    loss = loss_function(pred, target, class_weights)
    acc = pixel_accuracy(pred, target, pixel=pixel_dist)
    losses = np.append(losses, loss.item())
    accuracies = np.append(accuracies, acc)

avg_loss = np.mean(losses)
avg_acc = np.mean(accuracies)
print("Accuracy: %f, Loss: %f" % (avg_acc, avg_loss))
