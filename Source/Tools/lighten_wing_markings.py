# Makes a lightened copy of the lepthera wing art for tinting.
# The shader multiplies the mask colour into the art, so the dark-grey bands and eyespots under the
# red mask turned hair colour nearly black. This lifts only the pixels under the red mask
# (grey ~40..130 -> ~175..255, keeping the eyespot ring lighter than its centre) and leaves the
# black outlines and the rest of the wing alone. The originals are not touched.
#
# Usage: python -I lighten_wing_markings.py <Textures/Lepthera/Wings folder>
# Reads  leptherawings_<rot>.png  + leptherawings_<rot>m.png
# Writes leptherawings_light_<rot>.png + leptherawings_light_<rot>m.png (mask copied unchanged)
import os
import shutil
import sys

import numpy as np
from PIL import Image

LOW, HIGH = 40.0, 130.0        # grey range of the bands / eyespots in the source art
OUT_LOW, OUT_HIGH = 175.0, 255.0
KEEP_BELOW = 24.0              # outline-dark pixels stay as they are; 24..LOW ramps up


def lift(v):
    out = OUT_LOW + (np.clip(v, LOW, HIGH) - LOW) / (HIGH - LOW) * (OUT_HIGH - OUT_LOW)
    ramp = np.clip((v - KEEP_BELOW) / (LOW - KEEP_BELOW), 0, 1)
    return v + (out - v) * ramp


def main(folder):
    for rot in ("south", "east", "north"):
        src = os.path.join(folder, f"leptherawings_{rot}.png")
        msk = os.path.join(folder, f"leptherawings_{rot}m.png")
        tex = np.asarray(Image.open(src).convert("RGBA")).astype(float)
        mask = np.asarray(Image.open(msk).convert("RGB")).astype(float)
        red = (mask[..., 0] > 128) & (mask[..., 1] < 128) & (mask[..., 2] < 128)
        lum = tex[..., :3].mean(axis=2)
        scale = np.where(lum > 0, lift(lum) / np.maximum(lum, 1), 1.0)
        out = tex.copy()
        out[..., :3] = np.where(red[..., None], np.clip(tex[..., :3] * scale[..., None], 0, 255), tex[..., :3])
        Image.fromarray(out.astype(np.uint8), "RGBA").save(os.path.join(folder, f"leptherawings_light_{rot}.png"))
        shutil.copyfile(msk, os.path.join(folder, f"leptherawings_light_{rot}m.png"))
        print(rot, "lifted", int(red.sum()), "px")


if __name__ == "__main__":
    main(sys.argv[1])
