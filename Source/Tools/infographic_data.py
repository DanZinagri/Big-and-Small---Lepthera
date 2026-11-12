# Collects each Lepthera xenotype's genes as they resolve in the user's game (active mods from
# ModsConfig.xml, MayRequire, our swap patches), with label, icon path, icon colour and biostats
# (ParentName inheritance resolved). Writes infographic_data.json next to the output folder.
# Usage: python -I infographic_data.py <mod folder> <out json>
import glob, json, os, re, sys
import xml.etree.ElementTree as ET

MOD = sys.argv[1]
OUT = sys.argv[2]
CFG = os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Config\ModsConfig.xml")
GAME = r"E:\SteamLibrary\steamapps\common\RimWorld"
WORKSHOP = r"E:\SteamLibrary\steamapps\workshop\content\294100"
VER = 1.7

active = [li.text.strip().lower() for li in ET.parse(CFG).getroot().find("activeMods")]
aset = set(active)

# packageId -> folder
folders = {}
for d in glob.glob(os.path.join(GAME, "Data", "*")) + glob.glob(os.path.join(GAME, "Mods", "*")) + glob.glob(os.path.join(WORKSHOP, "*")):
    about = os.path.join(d, "About", "About.xml")
    if not os.path.isfile(about):
        continue
    try:
        pid = ET.parse(about).getroot().findtext("packageId")
    except ET.ParseError:
        m = re.search(r"<packageId>\s*([^<]+?)\s*</packageId>", open(about, encoding="utf-8", errors="ignore").read())
        pid = m.group(1) if m else None
    if not pid:
        continue
    pid = pid.strip().lower()
    # local copies (Mods) win over workshop; our own source folder wins over everything
    if pid not in folders or d.startswith(os.path.join(GAME, "Mods")):
        folders[pid] = d
for core in ["core", "royalty", "ideology", "biotech", "anomaly", "odyssey"]:
    folders["ludeon.rimworld" + ("" if core == "core" else "." + core)] = os.path.join(GAME, "Data", core.capitalize())
folders["danzinagri.bigsmall.lepthera"] = MOD


def version_ok(path, root):
    rel = os.path.relpath(path, root).replace("\\", "/").split("/")
    for part in rel[:-1]:
        if re.fullmatch(r"v?\d\.\d", part):
            return float(part.lstrip("v")) <= VER, float(part.lstrip("v"))
    return True, 0.0


genedefs = {}  # name/defName -> (element, version rank, packageId)
for pid in active:
    root = folders.get(pid)
    if not root:
        continue
    for f in glob.glob(os.path.join(root, "**", "*.xml"), recursive=True):
        if "About" in f.split(os.sep) or "Languages" in f.split(os.sep):
            continue
        ok, rank = version_ok(f, root)
        if not ok:
            continue
        try:
            txt = open(f, encoding="utf-8-sig", errors="ignore").read()
        except OSError:
            continue
        if "GeneDef" not in txt:
            continue
        try:
            r = ET.fromstring(txt)
        except ET.ParseError:
            continue
        for g in r.iter():
            if not isinstance(g.tag, str) or not g.tag.endswith("GeneDef"):
                continue
            key = g.findtext("defName") or g.get("Name")
            if not key:
                continue
            if g.get("Name"):
                genedefs.setdefault("@" + g.get("Name"), (g, rank, pid))
                if rank > genedefs["@" + g.get("Name")][1]:
                    genedefs["@" + g.get("Name")] = (g, rank, pid)
            dn = g.findtext("defName")
            if dn:
                if dn not in genedefs or rank >= genedefs[dn][1]:
                    genedefs[dn] = (g, rank, pid)

FIELDS = ["label", "iconPath", "iconColor", "biostatCpx", "biostatMet", "biostatArc", "displayCategory", "skinColorOverride", "hairColorOverride", "skinColorBase"]


def resolve(dn, depth=0):
    entry = genedefs.get(dn)
    if not entry or depth > 10:
        return {}
    g = entry[0]
    out = {}
    parent = g.get("ParentName")
    if parent:
        out.update(resolve("@" + parent, depth + 1))
    for f in FIELDS:
        v = g.findtext(f)
        if v is not None:
            out[f] = v.strip()
    out["_pid"] = entry[2]
    return out


# our xenotypes
xenos = {}
for f in glob.glob(os.path.join(MOD, "Defs", "**", "*.xml"), recursive=True) + glob.glob(os.path.join(MOD, "Mods", "*", "Defs", "*.xml")):
    r = ET.parse(f).getroot()
    for x in r.findall("XenotypeDef"):
        genes = []
        for li in x.find("genes"):
            req = li.get("MayRequire")
            if req and not all(p.strip().lower() in aset for p in req.split(",")):
                continue
            genes.append([li.text.strip(), bool(req)])
        xenos[x.findtext("defName")] = {"label": x.findtext("label"), "description": x.findtext("description"),
                                       "descriptionShort": x.findtext("descriptionShort"), "genes": genes}

# Mods/* folders that load with the active mod list (loadFolders.xml, v1.7)
def _ids(v):
    return [p.strip().lower() for p in v.split(",")] if v else []
loaded = set()
for li in ET.parse(os.path.join(MOD, "loadFolders.xml")).getroot().find("v1.7"):
    any_of, all_of, none_of = _ids(li.get("IfModActive")), _ids(li.get("IfModActiveAll")), _ids(li.get("IfModNotActive"))
    if (not any_of or any(p in aset for p in any_of)) and all(p in aset for p in all_of) and not any(p in aset for p in none_of):
        loaded.add(os.path.normpath(li.text.strip()))

# copy folders: a plain top-level PatchOperationAdd onto a xenotype's genes (our copy of a gene from
# a mod that isn't loaded; the xenotype XML lists the original with MayRequire)
for f in glob.glob(os.path.join(MOD, "Mods", "*", "Patches", "*.xml")):
    if os.path.normpath(os.path.relpath(os.path.dirname(os.path.dirname(f)), MOD)) not in loaded:
        continue
    for op in ET.parse(f).getroot().findall("Operation"):
        xm = re.search(r'XenotypeDef\[defName="([^"]+)"\]/genes$', op.findtext("xpath") or "")
        if op.get("Class") == "PatchOperationAdd" and xm and xm.group(1) in xenos:
            for li in op.findall("value/li"):
                xenos[xm.group(1)]["genes"].append([li.text.strip(), False])

# swap patches: PatchOperationConditional on a GeneDef existing -> Replace li / Remove + Add
patches = glob.glob(os.path.join(MOD, "Patches", "*.xml")) + glob.glob(os.path.join(MOD, "Mods", "*", "Patches", "*.xml"))
for f in patches:
    r = ET.parse(f).getroot()
    for op in r.findall("Operation"):
        m = re.search(r'GeneDef\[defName="([^"]+)"\]', op.findtext("xpath") or "")
        if not m or m.group(1) not in genedefs:
            continue
        for sub in op.iter():
            xp = sub.findtext("xpath") or ""
            xm = re.search(r'XenotypeDef\[defName="([^"]+)"\]/genes(?:/li\[text\(\)="([^"]+)"\])?$', xp)
            if not xm or xm.group(1) not in xenos:
                continue
            cls = sub.get("Class")
            genes = xenos[xm.group(1)]["genes"]
            if cls == "PatchOperationReplace" and xm.group(2):
                new = sub.find("value/li").text.strip()
                for g in genes:
                    if g[0] == xm.group(2):
                        g[0] = new; g[1] = True
            elif cls == "PatchOperationRemove" and xm.group(2):
                xenos[xm.group(1)]["genes"] = [g for g in genes if g[0] != xm.group(2)]
            elif cls == "PatchOperationAdd" and not xm.group(2):
                for li in sub.findall("value/li"):
                    xenos[xm.group(1)]["genes"].append([li.text.strip(), True])

missing = set()
for xn, x in xenos.items():
    out = []
    for dn, optional in x["genes"]:
        d = resolve(dn)
        if not d:
            missing.add(dn)
        d["defName"] = dn
        d["optional"] = optional
        out.append(d)
    x["genes"] = out
    x["cpx"] = sum(int(float(g.get("biostatCpx", 1 if g.get("defName") else 0))) for g in out)
    x["met"] = sum(int(float(g.get("biostatMet", 0))) for g in out)
    x["arc"] = sum(int(float(g.get("biostatArc", 0))) for g in out)
json.dump({"xenotypes": xenos, "folders": {k: folders[k] for k in active if k in folders}}, open(OUT, "w"), indent=1)
print("missing genes:", sorted(missing))
for xn, x in xenos.items():
    print(xn, len(x["genes"]), "cpx", x["cpx"], "met", x["met"], "arc", x["arc"])
