"""Slice the fur mask sheet into the Lepthera fluffy body textures.

Sheet layout (768x1536, 256px cells): rows Male, Female, Thin, Fat, Hulk, Child;
columns south, east, north. Same layout as Desktop/lepthera_masks/base_sheet.png
and the Affinity document Lepthera_FurMasks.af.

Paint only the fur, in red, on its own layer over the base art. Exported mask colours:
red = fur (B&S colorA, hair colour), green = chitin (colorB, skin colour). Every pixel inside
the body outline (taken from OAB's art) that isn't painted red becomes green; pixels outside the
outline are then filled from their nearest neighbour so the soft edge never samples black.
To export from Affinity, hide the base art layer and export the page as PNG.

Writes Textures/Lepthera/FluffyBody/FluffMask_<BodyType>_<rot>.png. The gene points its
texturePaths at OAB's own BP_Fuzzy_Body art and its maskPaths here, per body type, so no OAB art
is copied. Explicit mask paths load <maskPath>_<rot> (no "m" suffix). Baby reuses Child's mask.

Usage: python slice_fur_masks.py <mask_sheet.png>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

OAB = r"E:/SteamLibrary/steamapps/workshop/content/294100/2896673577/Textures/Things/Pawn/Humanlike/Bodies/BP_Fuzzy_Body"
ART = {"Male": "Fuzzy_Body_Male", "Female": "Fuzzy_Body_Female", "Thin": "Fuzzy_Body_Thin",
       "Fat": "Fuzzy_Body_Fat", "Hulk": "Fuzzy_Body_Hulk", "Child": "Fuzzy_BodyChild"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Textures", "Lepthera", "FluffyBody")
ROWS = ["Male", "Female", "Thin", "Fat", "Hulk", "Child"]
COLS = ["south", "east", "north"]


def clean(cell, art):
    rgb = cell[..., :3].astype(int)
    red = (cell[..., 3] >= 128) & (rgb[..., 0] > 128) & (rgb[..., 1] < 128)
    inside = art[..., 3] > 0
    green = inside & ~red
    lab = np.zeros(cell.shape[:2], np.uint8)
    lab[red], lab[green] = 1, 2
    # grow labels outward until the whole cell is covered
    for _ in range(256):
        if (lab > 0).all():
            break
        img = Image.fromarray(lab)
        grown = np.array(img.filter(ImageFilter.MaxFilter(3)))
        lab = np.where(lab == 0, grown, lab)
        if not lab.any():
            break
    out = np.zeros(cell.shape[:2] + (3,), np.uint8)
    out[lab == 1] = (255, 0, 0)
    out[lab == 2] = (0, 255, 0)
    return Image.fromarray(out, "RGB")


def main(sheet_path):
    sheet = np.array(Image.open(sheet_path).convert("RGBA"))
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for r, body in enumerate(ROWS):
        for c, rot in enumerate(COLS):
            art = np.array(Image.open(f"{OAB}/{ART[body]}_{rot}.png").convert("RGBA"))
            mask = clean(sheet[r * 256:(r + 1) * 256, c * 256:(c + 1) * 256], art)
            mask.save(os.path.join(OUT, f"FluffMask_{body}_{rot}.png"))
            n += 1
    print(f"wrote {n} masks to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main(sys.argv[1])
