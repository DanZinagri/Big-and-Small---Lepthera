# Finds every gene icon texture listed in infographic_data.json and copies it (as PNG) into
# <out>/icons/<iconPath with / -> _>.png. Mod textures are searched in the mod that defines the
# gene, then every active mod; vanilla ones come out of the 1.7 Assets.zip files via 7z and
# _reference/RimWorld-1.7-textures/unsplit_dds.py.
# Usage: python -I infographic_icons.py <data.json> <out folder>
import glob, json, os, shutil, subprocess, sys

DATA, OUT = sys.argv[1], sys.argv[2]
GAME = r"E:\SteamLibrary\steamapps\common\RimWorld"
UNSPLIT = r"C:\Users\DanZinagri\Documents\Claude\_reference\RimWorld-1.7-textures\unsplit_dds.py"
SEVENZ = "7z"
d = json.load(open(DATA))
folders = d["folders"]
os.makedirs(os.path.join(OUT, "icons"), exist_ok=True)

aptitude = {}
paths = {}
for x in d["xenotypes"].values():
    for g in x["genes"]:
        ip = g.get("iconPath")
        dn = g["defName"]
        if not ip and dn.startswith("Aptitude"):
            kind, skill = dn[len("Aptitude"):].split("_", 1)
            ip = f"UI/Icons/Genes/Skills/{skill}/{kind}"
            g["iconPath"] = ip
            g["label"] = {"Poor": "poor ", "Strong": "great ", "Terrible": "awful "}[kind] + skill.lower()
            g.setdefault("biostatMet", {"Poor": "1", "Strong": "-1", "Terrible": "2"}[kind])
            g.setdefault("biostatCpx", "1")
        if ip:
            paths.setdefault(ip, g.get("_pid"))

found = {}
order = ["danzinagri.bigsmall.lepthera"]
for ip, pid in paths.items():
    tries = ([pid] if pid else []) + order
    for p in tries:
        root = folders.get(p) or (r"C:\Users\DanZinagri\Documents\RimWorldProjects\Big and Small - Lepthera" if p == "danzinagri.bigsmall.lepthera" else None)
        if not root:
            continue
        hits = glob.glob(os.path.join(root, "**", "Textures", *ip.split("/")) + ".png", recursive=True)
        if hits:
            found[ip] = sorted(hits)[-1]
            break
missing = [ip for ip in paths if ip not in found]

# vanilla: Assets.zip of the game and each DLC (one listing per zip, indexed by texture path)
zips = [os.path.join(GAME, "Assets.zip")] + glob.glob(os.path.join(GAME, "Data", "*", "Assets.zip"))
tmp = os.path.join(OUT, "_vanilla")
os.makedirs(tmp, exist_ok=True)
index = {}
for z in zips:
    listing = subprocess.run([SEVENZ, "l", "-ba", z], capture_output=True, text=True).stdout
    for l in listing.splitlines():
        n = l.split()[-1] if l.split() else ""
        if n.endswith(".dds.split") and "-premul" not in n:
            rel = n.replace("\\", "/")
            rel = rel[len("Resources/"):] if rel.startswith("Resources/") else rel
            if not rel.startswith("Textures/"):
                continue
            key = rel[len("Textures/"):].split(".")[0]
            index.setdefault(key.lower(), (z, n))
for ip in list(missing):
    hit = index.get(ip.lower())
    if not hit:
        continue
    z, n = hit
    subprocess.run([SEVENZ, "e", "-y", f"-o{tmp}", z, n], capture_output=True)
    src = os.path.join(tmp, os.path.basename(n.replace("\\", "/")))
    dst = os.path.join(tmp, ip.replace("/", "_") + ".png")
    subprocess.run([sys.executable, "-I", UNSPLIT, src, dst], check=True)
    found[ip] = dst
    missing.remove(ip)

# leftovers: likely mods first, then every active mod
likely = ["vera.bug", "redmattis.bigsmall.core", "redmattis.betterprerequisites", "sarg.alphagenes", "redmattis.bigsmall"]
for ip in list(missing):
    for p in likely + [k for k in folders if k not in likely]:
        root = folders.get(p)
        if not root or root.startswith(os.path.join(GAME, "Data")):
            continue
        hits = glob.glob(os.path.join(root, "**", "Textures", *ip.split("/")) + ".png", recursive=True)
        if hits:
            found[ip] = sorted(hits)[-1]
            missing.remove(ip)
            break

for ip, src in found.items():
    shutil.copy(src, os.path.join(OUT, "icons", ip.replace("/", "_") + ".png"))
d["icons"] = {ip: ip.replace("/", "_") + ".png" for ip in found}
json.dump(d, open(DATA, "w"), indent=1)
print("found", len(found), "missing", missing)
