# Building EfficientNet

# Paper: https://arxiv.org/abs/1905.11946
# Implementation: https://www.youtube.com/watch?v=fR_0o25kigM
# MBConv(Inverted Residual Block) paper: https://arxiv.org/abs/1801.04381v4

import torch
import torch.nn as nn
from math import ceil

# Table 1 from the paper
# EfficientNet-B0 baseline network
# expand_ratio is the number that comes after the MBConv i.e. MBConv1, MBConv6
# repeats are the # of layers
# stride is from MBConv paper

base_model = [
    # expand_ratio, channels, repeats, stride, kernel_size
    [1, 16, 1, 1, 3],    # stage 2
    [6, 24, 2, 2, 3],    # stage 3
    [6, 40, 2, 2, 5],    # stage 4
    [6, 80, 3, 2, 5],    # stage 5
    [6, 112, 3, 1, 5],   # stage 6
    [6, 192, 4, 2, 5],   # stage 7
    [6, 320, 1, 1, 3]   # stage 8
]

phi_values = {
    # tuple of: (phi_value, resolution, drop_rate
    "b0": (0, 224, 0.2), # alpha, beta, gamma, depth = alpha ** phi
    "b1": ( 0.5, 240, 0.2),
    "b2": (1, 260, 0.3),
    "b3": (2, 300, 0.3),
    "b4": (3, 380, 0.4),
    "b5": (4, 456, 0.4),
    "b6": (5, 528, 0.5),
    "b7": (6, 600, 0.5)
}

class CNNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride, padding, groups=1):
        super(CNNBlock, self).__init__()
        self.cnn = nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            groups=groups,
            bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.silu = nn.SiLU() # SiLU = Sigmoid Linear Units

    def forward(self, x):
        return self.silu(self.bn(self.cnn(x)))


# compute attention scores for each of the channels
class SqueezeExcitation(nn.Module):
    def __init__(self, in_channels, reduced_dim):
        super(SqueezeExcitation, self).__init__()
        self.se = nn.Sequential(
            nn.AdaptiveAvgPool2d(1), # C * H * W -> C * 1 * 1
            nn.Conv2d(in_channels, reduced_dim, kernel_size=1),
            nn.SiLU(),
            nn.Conv2d(reduced_dim, in_channels, kernel_size=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return x * self.se(x) # input * attention value


class InvertedResidualBlock(nn.Module):
    def __init__(
            self,
            in_channels,
            out_channels,
            kernel_size,
            stride,
            padding,
            expand_ratio,
            reduction=4,    # squeeze excitation
            survival_prob=0.8,   # for stochastic depth
    ):
        super(InvertedResidualBlock, self).__init__()
        self.survival_prob = 0.8
        self.use_residual = in_channels == out_channels and stride == 1
        hidden_dim = in_channels * expand_ratio
        self.expand = in_channels != hidden_dim
        reduced_dim = int(in_channels / reduction)

        if self.expand:
            self.expand_conv = CNNBlock(
                in_channels, hidden_dim, kernel_size=3, stride=1, padding=1
            )

        self.conv = nn.Sequential(
            CNNBlock(
                hidden_dim, hidden_dim, kernel_size, stride, padding, groups=hidden_dim
            ),
            SqueezeExcitation(hidden_dim, reduced_dim),
            nn.Conv2d(hidden_dim, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
        )


class EfficientNet(nn.Module):
    pass