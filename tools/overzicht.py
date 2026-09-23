#!/usr/bin/env python3
"""Maakt LOKAAL een overzicht van de testdata in mijn-data/, zonder de data zelf door te geven.

Waarom: de AI-assistent hoeft je bestanden niet te lezen om een mapping te maken. Dit
script leest ze op je eigen computer en maakt alleen een overzicht: welke tabellen en
kolommen, welk soort gegevens, hoe vaak ingevuld, en een paar voorbeeldwaarden. Namen,
adressen, telefoonnummers, e-mail, BSN en geboortedatums worden vervangen door hun vorm
(Anna -> Xxxx, 06 1234 5678 -> 99 9999 9999). Alleen dat overzicht ziet de AI.

Herkent: CSV/TSV/TXT (scheidingsteken en tekenset automatisch), Excel (.xlsx/.xlsm; .xls
alleen als xlrd er is), JSON en JSON Lines, XML, SQL-dumps, SQLite-databases, ZIP-bestanden
(wordt uitgepakt). Schermafdrukken en PDF's kan dit script niet lezen: die meldt het als
"alleen door AI te lezen". Iets anders meldt het als "niet herkend", met een advies.

Gebruik: python3 tools/overzicht.py            schrijft mijn-koppeling/overzicht.md
         python3 tools/overzicht.py <map>      een andere map
"""
import csv
import io
import json
import re
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DUMMY = "barts-dummy-data"
MAX_RIJEN = 5000          # meer rijen lezen we niet per tabel
VOORBEELDEN = 3
ALLE_CODES = 40           # code-kolommen met hooguit zoveel waarden tonen we helemaal

PRIVE = re.compile(r"(naam|name|voorn|achtern|tussenv|initial|voorlett|straat|street|adres|address|"
                   r"huisnr|huisnummer|postcode|postal|zip|woonpl|city|plaats|(?:^|[^a-z])tel|phone|mobiel|"
                   r"mail|bsn|burgerservice|ssn|geboorte|birth|dob|iban|rekening|"
                   r"(?:^|[^a-z])(?:huis)?arts|behandelaar|zorgverlener|practitioner|doctor|"
                   r"opmerk|notitie|memo|comment|note|anamnese|verslag|brief|vrije.?tekst)", re.I)
# Kolommen over een ding, niet over een persoon, ook al zit er "naam" of "name" in.
GEEN_PERSOON = re.compile(r"(device|product|middel|medic|stof|artikel|genees|hulpmiddel|display|"
                          r"omschrijving|description|diagnose|verrichting|procedure)", re.I)
PATIENT_ID = re.compile(r"^(pat|patient|patiënt|client|cliënt)(_?id|_?nr|_?nummer)?$|^patnr$", re.I)
BEELD = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".bmp", ".tif", ".tiff", ".pdf"}
DATUM = [(re.compile(r"^\d{4}-\d{2}-\d{2}([T ][\d:.]+)?"), "JJJJ-MM-DD"),
         (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "DD-MM-JJJJ"),
         (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "DD/MM/JJJJ"),
         (re.compile(r"^(19|20)\d{6}$"), "JJJJMMDD")]


def vorm(waarde) -> str:
    """Maak van een waarde alleen de vorm: letters worden X/x, cijfers 9."""
    s = str(waarde)
    return re.sub(r"[A-Z]", "X", re.sub(r"[a-z]", "x", re.sub(r"\d", "9", s)))[:40]


def soort(waarden) -> str:
    gevuld = [str(w).strip() for w in waarden if w not in (None, "") and str(w).strip()]
    if not gevuld:
        return "leeg"
    if all(re.fullmatch(r"-?\d+", w) for w in gevuld):
        return "geheel getal"
    if all(re.fullmatch(r"-?\d+([.,]\d+)?", w) for w in gevuld):
        return "getal"
    for patroon, naam in DATUM:
        if all(patroon.match(w) for w in gevuld):
            return f"datum ({naam})"
    if all(len(w) <= 12 and re.fullmatch(r"[A-Za-z0-9.\-_/]+", w) for w in gevuld):
        return "code"
    return "tekst"


def kolom_overzicht(naam: str, waarden: list) -> dict:
    gevuld = [w for w in waarden if w not in (None, "") and str(w).strip()]
    uniek = list(dict.fromkeys(str(w).strip() for w in gevuld))
    prive = bool(PRIVE.search(naam)) and not GEEN_PERSOON.search(naam)
    wat = soort(waarden)
    # Codes (ICPC, ATC, eigen codes) zijn geen persoonsgegevens: toon ze allemaal, anders
    # mist de mapping vertalingen voor codes die toevallig niet bij de voorbeelden zaten.
    # Vrije tekst met weinig verschillende waarden (zoals diagnoses) ook helemaal: die heb je
    # nodig voor de vertaling naar SNOMED. Echte vrije tekst (opmerkingen) staat onder PRIVE.
    aantal = len(uniek) if wat in ("code", "tekst") and not prive and len(uniek) <= ALLE_CODES else VOORBEELDEN
    voorbeelden = [vorm(w) if prive else str(w)[:60] for w in uniek[:aantal]]
    if wat == "code" and not prive and 1 < len(uniek) <= 10 and len(gevuld) > len(uniek):
        tel = Counter(str(w).strip() for w in gevuld)
        voorbeelden = [f"{w} ({tel[w]}x)" for w in uniek]
    return {"kolom": naam, "soort": wat, "gevuld": f"{len(gevuld)}/{len(waarden)}",
            "verschillend": len(uniek), "voorbeelden": voorbeelden, "verborgen": prive}


def tabel(naam: str, kolommen: list, rijen: list) -> dict:
    rijen = rijen[:MAX_RIJEN]
    per_kolom = [kolom_overzicht(str(k), [r[i] if i < len(r) else None for r in rijen])
                 for i, k in enumerate(kolommen)]
    t = {"tabel": naam, "rijen": len(rijen), "kolommen": per_kolom, "bron": "", "plat": ""}
    for i, k in enumerate(kolommen):
        if PATIENT_ID.match(str(k).strip()):
            ids = [r[i] for r in rijen if i < len(r) and r[i] not in (None, "")]
            if len(set(ids)) < len(ids):
                t["plat"] = (f"Let op: {len(ids)} rijen maar {len(set(ids))} verschillende `{k}`. Meerdere "
                             f"regels per patient: voeg ze samen per `{k}` tot een dossier.")
            break
    return t


# ---------------------------------------------------------------- lezers

def lees_met_codering(pad: Path) -> tuple:
    ruw = pad.read_bytes()
    for codering in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return ruw.decode(codering), codering
        except UnicodeDecodeError:
            continue
    return ruw.decode("latin-1", errors="replace"), "latin-1"


def lees_tekstbestand(pad: Path) -> str:
    return lees_met_codering(pad)[0]


def lees_csv(pad: Path) -> list:
    tekst, codering = lees_met_codering(pad)
    try:
        dialect = csv.Sniffer().sniff(tekst[:20000], delimiters=";,\t|")
    except csv.Error:
        dialect = csv.excel
    rijen = list(csv.reader(io.StringIO(tekst), dialect))
    rijen = [r for r in rijen if any(c.strip() for c in r)]
    if not rijen:
        return []
    t = tabel(pad.name, rijen[0], rijen[1:])
    scheiding = {"\t": "tab", ";": "puntkomma", ",": "komma", "|": "streep"}.get(dialect.delimiter, dialect.delimiter)
    t["bron"] = f"scheidingsteken: {scheiding}, tekenset: {codering.replace('-sig', ' (met BOM)')}"
    return [t]


def kop_zoeken(rijen: list) -> int:
    """Excel-bladen beginnen vaak met een titel. Pak de eerste rij met minstens twee
    tekstcellen en meer gevulde cellen dan de rijen erboven."""
    beste, beste_aantal = 0, 0
    for i, rij in enumerate(rijen[:15]):
        tekst = [c for c in rij if isinstance(c, str) and c.strip()]
        if len(tekst) >= 2 and len(tekst) > beste_aantal:
            beste, beste_aantal = i, len(tekst)
            if len(tekst) >= max(2, int(0.8 * len([c for c in rij if c not in (None, "")]))):
                return i
    return beste


def lees_excel(pad: Path) -> list:
    if pad.suffix.lower() == ".xls":
        try:
            import xlrd  # noqa: F401
        except ImportError:
            raise ValueError("oud Excel-formaat (.xls). Sla het op als .xlsx of CSV, of installeer xlrd")
        import xlrd
        boek = xlrd.open_workbook(pad)
        bladen = [(b.name, [b.row_values(i) for i in range(b.nrows)]) for b in boek.sheets()]
    else:
        try:
            import openpyxl
        except ImportError:
            raise ValueError("openpyxl ontbreekt. Installeer: python3 -m pip install openpyxl")
        boek = openpyxl.load_workbook(pad, read_only=True, data_only=True)
        bladen = [(b.title, [list(r) for r in b.iter_rows(values_only=True)]) for b in boek.worksheets]
    uit = []
    for naam, rijen in bladen:
        rijen = [r for r in rijen if any(c not in (None, "") for c in r)]
        if len(rijen) < 2:
            continue
        k = kop_zoeken(rijen)
        kolommen = [str(c) if c not in (None, "") else f"kolom{i + 1}" for i, c in enumerate(rijen[k])]
        uit.append(tabel(f"{pad.name} / {naam}", kolommen, rijen[k + 1:]))
    return uit


def platslaan(obj, prefix="") -> dict:
    velden = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            velden.update(platslaan(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        if obj and all(not isinstance(x, (dict, list)) for x in obj):
            velden[prefix + "[]"] = obj[0]
        else:
            for x in obj[:1]:
                velden.update(platslaan(x, prefix + "[]"))
    else:
        velden[prefix] = obj
    return velden


def records_zoeken(data):
    """Zoek de lijsten met records in een JSON-structuur: {naam: [records]}."""
    gevonden = {}

    def loop(obj, pad):
        if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj[:20]):
            gevonden[pad or "records"] = obj
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                loop(v, f"{pad}.{k}" if pad else k)

    loop(data, "")
    if not gevonden and isinstance(data, dict):
        gevonden["record"] = [data]
    return gevonden


def json_tabellen(naam: str, data) -> list:
    uit = []
    for pad, records in records_zoeken(data).items():
        vlak = [platslaan(r) for r in records[:MAX_RIJEN]]
        kolommen = list(dict.fromkeys(k for r in vlak for k in r))
        uit.append(tabel(f"{naam} / {pad}", kolommen, [[r.get(k) for k in kolommen] for r in vlak]))
    return uit


def lees_json(pad: Path) -> list:
    tekst = lees_tekstbestand(pad).strip()
    try:
        return json_tabellen(pad.name, json.loads(tekst))
    except json.JSONDecodeError:
        regels = [json.loads(r) for r in tekst.splitlines() if r.strip()]  # JSON Lines
        return json_tabellen(pad.name, regels)


def lees_xml(pad: Path) -> list:
    wortel = ET.parse(pad).getroot()
    lokaal = lambda t: t.split("}", 1)[-1]  # noqa: E731
    # herhalende elementen = records
    tellers = Counter()
    for ouder in wortel.iter():
        for tag, n in Counter(lokaal(k.tag) for k in ouder).items():
            if n > 1:
                tellers[tag] += n
    uit = []
    for tag, _ in tellers.most_common(8):
        records = [e for e in wortel.iter() if lokaal(e.tag) == tag][:MAX_RIJEN]
        vlak = []
        for e in records:
            r = {f"@{k}": v for k, v in e.attrib.items()}
            for kind in e.iter():
                if kind is not e and (kind.text or "").strip():
                    r[lokaal(kind.tag)] = kind.text.strip()
                for k, v in kind.attrib.items():
                    if kind is not e:
                        r[f"{lokaal(kind.tag)}@{k}"] = v
            if not r and (e.text or "").strip():
                r["waarde"] = e.text.strip()
            vlak.append(r)
        kolommen = list(dict.fromkeys(k for r in vlak for k in r))
        if kolommen:
            uit.append(tabel(f"{pad.name} / <{tag}>", kolommen, [[r.get(k) for k in kolommen] for r in vlak]))
    return uit


def lees_sqlite(pad: Path) -> list:
    conn = sqlite3.connect(f"file:{pad}?mode=ro", uri=True)
    uit = []
    for (naam,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        cur = conn.execute(f'SELECT * FROM "{naam}" LIMIT {MAX_RIJEN}')
        uit.append(tabel(f"{pad.name} / {naam}", [d[0] for d in cur.description], [list(r) for r in cur.fetchall()]))
    conn.close()
    return uit


def lees_sql(pad: Path) -> list:
    """SQL-dump: laad hem in een tijdelijke SQLite. Lukt dat niet (ander dialect), dan
    alleen de kolommen uit de CREATE TABLE-regels."""
    tekst = lees_tekstbestand(pad)
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "dump.sqlite"
        conn = sqlite3.connect(db)
        schoon = re.sub(r"(?im)^\s*(SET|LOCK|UNLOCK|USE|GO|/\*!).*$", "", tekst)
        schoon = re.sub(r"(?i)\b(ENGINE|AUTO_INCREMENT|DEFAULT CHARSET|CHARSET|COLLATE)\s*=\s*\w+", "", schoon)
        schoon = re.sub(r"(?i)\b(AUTO_INCREMENT|UNSIGNED|ZEROFILL)\b", "", schoon)
        schoon = schoon.replace("`", '"')
        try:
            conn.executescript(schoon)
            conn.commit()
            conn.close()
            uit = lees_sqlite(db)
            return [dict(t, tabel=t["tabel"].replace("dump.sqlite", pad.name)) for t in uit]
        except sqlite3.Error:
            conn.close()
    uit = []
    for naam, lijf in re.findall(r'(?is)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\["`]?([\w.]+)[\]"`]?\s*\((.*?)\)\s*;', tekst):
        kolommen = [re.split(r"\s+", r.strip())[0].strip('[]"`') for r in lijf.split(",")
                    if r.strip() and not re.match(r"(?i)\s*(PRIMARY|FOREIGN|UNIQUE|CONSTRAINT|KEY|INDEX|CHECK)", r)]
        uit.append(tabel(f"{pad.name} / {naam}", kolommen, []))
    if not uit:
        raise ValueError("SQL-bestand zonder herkenbare CREATE TABLE")
    return uit


LEZERS = {".csv": lees_csv, ".tsv": lees_csv, ".txt": lees_csv, ".xlsx": lees_excel, ".xlsm": lees_excel,
          ".xls": lees_excel, ".json": lees_json, ".jsonl": lees_json, ".ndjson": lees_json, ".xml": lees_xml,
          ".sql": lees_sql, ".sqlite": lees_sqlite, ".sqlite3": lees_sqlite, ".db": lees_sqlite}


def is_sqlite(pad: Path) -> bool:
    with open(pad, "rb") as f:
        return f.read(16) == b"SQLite format 3\x00"


def bekijk(pad: Path, verslag: dict, basis: Path):
    rel = str(pad.relative_to(basis))
    ext = pad.suffix.lower()
    if pad.name in (".gitkeep", ".DS_Store") or pad.name.lower().startswith(("leesmij", "readme")):
        if pad.name.lower().startswith(("leesmij", "readme")):
            verslag["toelichting"].append((rel, lees_tekstbestand(pad)[:1500]))
        return
    if ext == ".zip":
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(pad) as z:
            z.extractall(tmp)
            for kind in sorted(Path(tmp).rglob("*")):
                if kind.is_file():
                    bekijk(kind, verslag, Path(tmp))
        return
    if ext in BEELD:
        verslag["beeld"].append(rel)
        return
    lezer = LEZERS.get(ext) or (lees_sqlite if is_sqlite(pad) else None)
    if lezer is None:
        verslag["onbekend"].append((rel, f"bestandstype {ext or '(geen extensie)'} herken ik niet"))
        return
    try:
        tabellen = lezer(pad)
        if not tabellen:
            verslag["onbekend"].append((rel, "geen rijen of kolommen gevonden"))
        verslag["tabellen"].extend(tabellen)
    except Exception as fout:  # noqa: BLE001
        verslag["onbekend"].append((rel, str(fout)[:200]))


def schrijf(verslag: dict) -> str:
    r = ["# Overzicht van je testdata", "",
         "Lokaal gemaakt door `tools/overzicht.py`. Namen, adressen, telefoon, e-mail, BSN en",
         "geboortedatums zijn vervangen door hun vorm (X = letter, 9 = cijfer). De AI-assistent",
         "leest alleen dit overzicht, niet de bestanden zelf. Code-kolommen staan er helemaal in;",
         "omschrijvingen met weinig verschillende waarden ook. Opmerkingen en notities zijn verborgen.", ""]
    for t in verslag["tabellen"]:
        r += [f"## {t['tabel']}  ({t['rijen']} rijen)", "",
              *([t["bron"], ""] if t.get("bron") else []),
              *([t["plat"], ""] if t.get("plat") else []),
              "| kolom | soort | gevuld | verschillend | voorbeelden |", "|---|---|---|---|---|"]
        for k in t["kolommen"]:
            vb = ", ".join(f"`{v}`" for v in k["voorbeelden"]) + ("  (vorm, verborgen)" if k["verborgen"] and k["voorbeelden"] else "")
            r.append(f"| {k['kolom']} | {k['soort']} | {k['gevuld']} | {k['verschillend']} | {vb} |")
        r.append("")
    if verslag["toelichting"]:
        r += ["## Toelichting bij de export", "",
              "Letterlijk overgenomen uit het LEESMIJ-bestand. Staan daar namen in, haal ze daar weg.", ""]
        for naam, tekst in verslag["toelichting"]:
            r += [f"**{naam}**", "", "```", tekst.strip(), "```", ""]
    if verslag["beeld"]:
        r += ["## Alleen door AI te lezen (schermafdruk of PDF)", ""]
        r += [f"- {b}" for b in verslag["beeld"]] + [""]
    if verslag["onbekend"]:
        r += ["## Niet herkend", ""]
        r += [f"- {n}: {reden}" for n, reden in verslag["onbekend"]] + [""]
    return "\n".join(r)


def main() -> int:
    map_ = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT / "mijn-data"
    verslag = defaultdict(list)
    bestanden = sorted(p for p in map_.rglob("*") if p.is_file() and p.name not in (".gitkeep", ".DS_Store"))
    # De voorbeeldexport uit de live demo telt alleen mee als er verder niets staat.
    dummy = [p for p in bestanden if DUMMY in p.relative_to(map_).parts]
    eigen = [p for p in bestanden if DUMMY not in p.relative_to(map_).parts]
    if eigen and dummy:
        bestanden = eigen
        print(f"  Je eigen export gevonden: de map {DUMMY}/ (voorbeelddata) sla ik over.")
    for pad in bestanden:
        bekijk(pad, verslag, map_)
    tekst = schrijf(verslag)
    doel = PROJECT / "mijn-koppeling" / "overzicht.md"
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(tekst + "\n", encoding="utf-8")
    kolommen = sum(len(t["kolommen"]) for t in verslag["tabellen"])
    print(f"Overzicht gemaakt: {doel.relative_to(PROJECT)}")
    print(f"  {len(verslag['tabellen'])} tabellen, {kolommen} kolommen herkend")
    if verslag["beeld"]:
        print(f"  {len(verslag['beeld'])} schermafdruk/PDF: alleen door AI te lezen ({', '.join(verslag['beeld'])})")
    for naam, _ in verslag["toelichting"]:
        print(f"  LET OP: {naam} staat letterlijk in het overzicht. Staan daar namen in, haal ze eruit.")
    for naam, reden in verslag["onbekend"]:
        print(f"  NIET HERKEND: {naam}: {reden}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
