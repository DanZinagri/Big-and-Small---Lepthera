# Renders one 128px gene tile per gene (vanilla endogene background + icon tinted like the game
# does: iconColor, else skin/hair colour override, else white) into <out>/tiles/<defName>.png.
# Usage: python -I infographic_tiles.py <data.json> <out folder>
import json, os, re, sys
from PIL import Image

DATA, OUT = sys.argv[1], sys.argv[2]
BG = r"C:\Users\DanZinagri\Documents\Claude\_reference\RimWorld-1.7-textures\DependencyGenes\GeneBackground_Endogene.png"
d = json.load(open(DATA))
os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
bg = Image.open(BG).convert("RGBA").resize((128, 128), Image.LANCZOS)


def colour(s):
    if not s:
        return None
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", s)][:3]
    if len(nums) < 3:
        return None
    if max(nums) > 1:
        nums = [n / 255 for n in nums]
    return nums


missing = []
for x in d["xenotypes"].values():
    for g in x["genes"]:
        tile = bg.copy()
        icon = d.get("icons", {}).get(g.get("iconPath"))
        if icon:
            im = Image.open(os.path.join(OUT, "icons", icon)).convert("RGBA")
            im.thumbnail((128, 128), Image.LANCZOS)
            c = colour(g.get("iconColor")) or colour(g.get("skinColorOverride")) or colour(g.get("hairColorOverride")) or colour(g.get("skinColorBase"))
            if c:
                r, gg, b, a = im.split()
                r = r.point(lambda v, k=c[0]: int(v * k)); gg = gg.point(lambda v, k=c[1]: int(v * k)); b = b.point(lambda v, k=c[2]: int(v * k))
                im = Image.merge("RGBA", (r, gg, b, a))
            tile.alpha_composite(im, ((128 - im.width) // 2, (128 - im.height) // 2))
        else:
            missing.append(g["defName"])
        tile.save(os.path.join(OUT, "tiles", g["defName"] + ".png"))
print("tiles done; no icon:", sorted(set(missing)))
