# Renders the wing gene icons from the lightened wing art (south view), tinted like each gene:
# mask red = markings colour, mask green = wing colour. Output 128x128 to Textures/Lepthera/UI/Genes.
# Usage: python -I make_wing_icons.py <mod folder>
import os
import sys

import numpy as np
from PIL import Image

SCHEMES = {
    "Lepthera_Wings": ((0.62, 0.62, 0.62), (0.95, 0.94, 0.90)),        # hair colour: neutral grey stands in
    "Lepthera_Wings_Brown": ((0.52, 0.35, 0.20), (0.95, 0.94, 0.90)),
    "Lepthera_Wings_Midnight": ((0.75, 0.75, 0.80), (0.13, 0.16, 0.36)),  # hair colour: silver stands in
    "Lepthera_Wings_Lunar": ((0.88, 0.68, 0.24), (0.13, 0.16, 0.36)),
    "Lepthera_Wings_Fungal": ((0.45, 0.30, 0.30), (0.31, 0.27, 0.31)),  # Mycoth ash-brown hair, dark purple skin
}


def main(mod):
    wings = os.path.join(mod, "Textures", "Lepthera", "Wings")
    tex = np.asarray(Image.open(os.path.join(wings, "leptherawings_light_south.png")).convert("RGBA")).astype(float) / 255
    mask = np.asarray(Image.open(os.path.join(wings, "leptherawings_light_southm.png")).convert("RGB")).astype(float) / 255
    alpha_img = Image.fromarray((tex[..., 3] * 255).astype(np.uint8))
    box = alpha_img.point(lambda a: 255 if a > 40 else 0).getbbox()
    w = mask / np.maximum(mask.sum(axis=2, keepdims=True), 1e-6)
    out_dir = os.path.join(mod, "Textures", "Lepthera", "UI", "Genes")
    for name, (a, b) in SCHEMES.items():
        col = w[..., 0:1] * np.array(a) + w[..., 1:2] * np.array(b) + w[..., 2:3]
        img = tex.copy()
        img[..., :3] = tex[..., :3] * col
        im = Image.fromarray((img * 255).astype(np.uint8), "RGBA").crop(box)
        side = max(im.size)
        sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        sq.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
        sq = sq.resize((116, 116), Image.LANCZOS)
        icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        icon.alpha_composite(sq, (6, 6))
        icon.save(os.path.join(out_dir, f"{name}.png"))
        print("wrote", name)


if __name__ == "__main__":
    main(sys.argv[1])
