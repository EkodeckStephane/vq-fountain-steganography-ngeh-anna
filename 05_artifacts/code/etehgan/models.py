import torch
import torch.nn as nn
import torch.nn.functional as F


class SpatialAttention(nn.Module):
    """CBAM-style spatial attention used by the checkpoint decoder."""

    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False)

    def forward(self, x):
        avg_map = torch.mean(x, dim=1, keepdim=True)
        max_map, _ = torch.max(x, dim=1, keepdim=True)
        attention = torch.sigmoid(self.conv(torch.cat([avg_map, max_map], dim=1)))
        return x * attention


def conv_block(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
        nn.ReLU(inplace=True),
        nn.BatchNorm2d(out_channels),
    )


class DenseEncoder512(nn.Module):
    """Dense payload encoder matching the ETEHGAN.pt `en` state_dict."""

    def __init__(self):
        super().__init__()
        self.conv1 = conv_block(3, 32)
        self.conv2 = conv_block(34, 32)
        self.conv3 = conv_block(66, 32)
        self.final_conv = nn.Conv2d(98, 3, kernel_size=3, padding=1)

    def forward(self, cover, payload):
        x1 = self.conv1(cover)
        x2 = self.conv2(torch.cat([x1, payload], dim=1))
        x3 = self.conv3(torch.cat([x1, x2, payload], dim=1))
        stego = self.final_conv(torch.cat([x1, x2, x3, payload], dim=1))
        return torch.tanh(stego)


class ResidualDenseEncoder512(DenseEncoder512):
    """Residual encoder for V2 training with explicit image-fidelity control."""

    def __init__(self, residual_strength=0.1):
        super().__init__()
        self.residual_strength = residual_strength

    def forward(self, cover, payload):
        x1 = self.conv1(cover)
        x2 = self.conv2(torch.cat([x1, payload], dim=1))
        x3 = self.conv3(torch.cat([x1, x2, payload], dim=1))
        residual = torch.tanh(self.final_conv(torch.cat([x1, x2, x3, payload], dim=1)))
        return (cover + self.residual_strength * residual).clamp(-1.0, 1.0)


class DenseDecoder512(nn.Module):
    """Dense payload decoder matching the ETEHGAN.pt `de` state_dict."""

    def __init__(self):
        super().__init__()
        self.layer1 = conv_block(3, 32)
        self.layer2 = conv_block(32, 32)
        self.layer3 = conv_block(64, 32)
        self.attention = SpatialAttention()
        self.final_layer = nn.Conv2d(96, 2, kernel_size=3, padding=1)

    def forward(self, stego):
        x1 = self.layer1(stego)
        x2 = self.layer2(x1)
        x3 = self.layer3(torch.cat([x1, x2], dim=1))
        features = torch.cat([x1, x2, x3], dim=1)
        features = self.attention(features)
        return self.final_layer(features)


class ResidualStegoDiscriminator(nn.Module):
    """Small residual-domain cover/stego discriminator for adversarial training."""

    def __init__(self, base_channels=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(12, base_channels, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.GroupNorm(4, base_channels),
            nn.Conv2d(base_channels, base_channels * 2, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.GroupNorm(8, base_channels * 2),
            nn.Conv2d(base_channels * 2, base_channels * 4, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.GroupNorm(8, base_channels * 4),
            nn.Conv2d(base_channels * 4, base_channels * 4, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(base_channels * 4, 1),
        )

    def forward(self, image):
        horizontal = F.pad(image[:, :, :, 1:] - image[:, :, :, :-1], (0, 1, 0, 0))
        vertical = F.pad(image[:, :, 1:, :] - image[:, :, :-1, :], (0, 0, 0, 1))
        local_mean = F.avg_pool2d(image, kernel_size=3, stride=1, padding=1)
        high_pass = image - local_mean
        features = torch.cat([image, horizontal, vertical, high_pass], dim=1)
        return self.net(features)
