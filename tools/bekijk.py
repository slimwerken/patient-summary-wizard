#!/usr/bin/env python3
"""Maakt van elke Patient Summary in output/ een leesbare pagina, zoals een arts hem ziet.

Het JSON-bestand is voor computers. Deze pagina laat per onderdeel zien wat erin staat,
met de codes erbij die de ontvanger gebruikt. Alles gebeurt op deze computer.

Gebruik:
    python3 tools/bekijk.py                  alle dossiers in output/, plus output/index.html
    python3 tools/bekijk.py --open           en open het overzicht in de browser
    python3 tools/bekijk.py output/patient-1001.json --open
"""
import argparse
import html
import json
import sys
import webbrowser
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

STELSELS = {
    "http://snomed.info/sct": "SNOMED",
    "http://loinc.org": "LOINC",
    "http://hl7.org/fhir/sid/icpc-1-nl": "ICPC",
    "http://hl7.org/fhir/sid/icpc-2": "ICPC-2",
    "http://www.whocc.no/atc": "ATC",
    "http://hl7.org/fhir/sid/icd-10": "ICD-10",
    "http://unitsofmeasure.org": "UCUM",
}
GESLACHT = {"female": "vrouw", "male": "man", "other": "anders", "unknown": "onbekend"}
STATUS = {"active": "actief", "resolved": "afgesloten", "inactive": "niet actief", "recurrence": "terug",
          "remission": "in remissie", "completed": "afgerond", "stopped": "gestopt", "intended": "gepland",
          "entered-in-error": "foutief ingevoerd", "unknown": "onbekend"}
LEEG = {"unavailable": "niet vastgelegd in het dossier", "nilknown": "een arts heeft vastgesteld dat er niets is",
        "notasked": "niet gevraagd", "withheld": "achtergehouden", "notstarted": "nog niet begonnen",
        "closed": "afgesloten"}
ERNST = {"high": "hoog risico", "low": "laag risico", "unable-to-assess": "niet te beoordelen"}

STIJL = """
:root{--ink:#2b2622;--zacht:#7a6e62;--lijn:#e6e0da;--vlak:#faf8f6;--accent:#ee7202;--leeg:#9a8f84}
*{box-sizing:border-box}body{margin:0;background:#f3f0ec;color:var(--ink);
font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:920px;margin:0 auto;padding:32px 16px 64px}
.kop{background:#fff;border-top:6px solid var(--accent);border-radius:10px;padding:24px 28px;margin-bottom:20px}
.kop small{color:var(--zacht);text-transform:uppercase;letter-spacing:.08em;font-size:12px}
.kop h1{margin:4px 0 6px;font-size:28px}.kop p{margin:0;color:var(--zacht)}
.feiten{display:flex;flex-wrap:wrap;gap:8px 24px;margin-top:14px;font-size:14px}
.feiten b{display:block;font-size:11px;color:var(--zacht);text-transform:uppercase;letter-spacing:.06em}
section{overflow-x:auto;background:#fff;border-radius:10px;padding:20px 28px;margin-bottom:14px}
section h2{margin:0 0 12px;font-size:19px;display:flex;justify-content:space-between;gap:12px;align-items:baseline}
section h2 span{font-size:12px;font-weight:400;color:var(--zacht)}
table{width:100%;border-collapse:collapse;font-size:15px}
th{text-align:left;font-size:12px;color:var(--zacht);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--lijn)}
td{padding:9px 8px;border-bottom:1px solid var(--lijn);vertical-align:top}
tr:last-child td{border-bottom:0}
.code{display:inline-block;background:var(--vlak);border:1px solid var(--lijn);border-radius:5px;
padding:1px 7px;margin:2px 4px 2px 0;font-size:12px;font-family:ui-monospace,Menlo,monospace;white-space:nowrap}
.code i{font-style:normal;color:var(--accent);font-weight:600;margin-right:4px}
.leeg{color:var(--leeg);font-style:italic}
.voet{color:var(--zacht);font-size:13px;margin-top:24px}
.lijst a{display:block;background:#fff;border-radius:10px;padding:16px 22px;margin-bottom:10px;
color:var(--ink);text-decoration:none;border-left:5px solid var(--accent)}
.lijst a span{color:var(--zacht);font-size:14px}
@media (max-width:600px){.kop,section{padding:16px}td,th{padding:7px 4px}}
"""


def e(tekst) -> str:
    return html.escape(str(tekst)) if tekst not in (None, "") else ""


def datum(waarde) -> str:
    """2011-05-02 of 2011-05-02T10:00:00+02:00 -> 02-05-2011"""
    if not waarde:
        return ""
    d = str(waarde)[:10].split("-")
    return "-".join(reversed(d)) if len(d) == 3 else str(waarde)


def codes(concept) -> str:
    if not concept:
        return ""
    stukken = []
    for c in concept.get("coding", []):
        naam = STELSELS.get(c.get("system", ""), c.get("system", "").rsplit("/", 1)[-1] or "code")
        titel = e(c.get("display", ""))
        stukken.append(f'<span class="code" title="{titel}"><i>{e(naam)}</i>{e(c.get("code", ""))}</span>')
    return "".join(stukken)


def naam_van(concept) -> str:
    if not concept:
        return ""
    if concept.get("text"):
        return concept["text"]
    for c in concept.get("coding", []):
        if c.get("display"):
            return c["display"]
    return ""


def wie(r: dict) -> str:
    """Naam van een arts (lijst met namen) of een organisatie (tekst)."""
    naam = r.get("name")
    if isinstance(naam, list) and naam:
        n = naam[0]
        return n.get("text") or " ".join([*n.get("given", []), n.get("family", "")]).strip()
    return naam or ""


def status(concept) -> str:
    code = next((c.get("code") for c in (concept or {}).get("coding", [])), "")
    return STATUS.get(code, code)


def periode(start, eind) -> str:
    if start and eind:
        return f"{datum(start)} tot {datum(eind)}"
    return f"sinds {datum(start)}" if start else (f"tot {datum(eind)}" if eind else "")


def regel(r: dict, bron: dict) -> tuple:
    """Een onderdeel -> (wat, codes, details). Onbekende soorten krijgen hun eigen tekst."""
    soort = r.get("resourceType")
    if soort == "Condition":
        return (naam_van(r.get("code")), codes(r.get("code")),
                ", ".join(x for x in (status(r.get("clinicalStatus")),
                                      periode(r.get("onsetDateTime"), r.get("abatementDateTime"))) if x))
    if soort == "AllergyIntolerance":
        wat = ", ".join(x for x in (ERNST.get(r.get("criticality"), ""), status(r.get("clinicalStatus")),
                                    f"vastgelegd {datum(r['recordedDate'])}" if r.get("recordedDate") else "") if x)
        return naam_van(r.get("code")), codes(r.get("code")), wat
    if soort in ("MedicationStatement", "MedicationRequest"):
        middel = r.get("medicationCodeableConcept")
        if not middel and r.get("medicationReference"):
            middel = bron.get(r["medicationReference"].get("reference"), {}).get("code")
        dosering = "; ".join(d.get("text", "") for d in r.get("dosage", r.get("dosageInstruction", [])) if d.get("text"))
        p = r.get("effectivePeriod", {})
        return (naam_van(middel), codes(middel),
                ", ".join(x for x in (dosering, periode(p.get("start") or r.get("effectiveDateTime"), p.get("end"))) if x))
    if soort == "Procedure":
        wanneer = r.get("performedDateTime") or r.get("performedPeriod", {}).get("start")
        return naam_van(r.get("code")), codes(r.get("code")), datum(wanneer)
    if soort == "DeviceUseStatement":
        apparaat = bron.get(r.get("device", {}).get("reference"), {})
        p = r.get("timingPeriod", {})
        return (naam_van(apparaat.get("type")), codes(apparaat.get("type")),
                periode(p.get("start") or r.get("timingDateTime"), p.get("end")))
    if soort == "Observation":
        def meting(x):
            v = x.get("valueQuantity")
            return f"{v.get('value', '')} {v.get('unit') or v.get('code', '')}".strip() if v else \
                (naam_van(x.get("valueCodeableConcept")) or x.get("valueString", ""))
        delen = [f"{naam_van(c.get('code'))} {meting(c)}".strip() for c in r.get("component", []) if meting(c)]
        waarde = meting(r) or "; ".join(delen)
        wanneer = r.get("effectiveDateTime") or r.get("effectivePeriod", {}).get("start")
        return naam_van(r.get("code")), codes(r.get("code")), ", ".join(x for x in (waarde, datum(wanneer)) if x)
    if soort == "Immunization":
        return naam_van(r.get("vaccineCode")), codes(r.get("vaccineCode")), datum(r.get("occurrenceDateTime"))
    return soort or "onderdeel", codes(r.get("code")), ""


def pagina(pad: Path) -> tuple:
    bundel = json.loads(pad.read_text(encoding="utf-8"))
    bron = {x.get("fullUrl"): x.get("resource", {}) for x in bundel.get("entry", [])}
    for r in list(bron.values()):
        if r.get("resourceType") and r.get("id"):
            bron.setdefault(f"{r['resourceType']}/{r['id']}", r)
    doc = next((r for r in bron.values() if r.get("resourceType") == "Composition"), {})
    pat = bron.get(doc.get("subject", {}).get("reference"), {}) or \
        next((r for r in bron.values() if r.get("resourceType") == "Patient"), {})

    naam = pat.get("name", [{}])[0]
    volledig = naam.get("text") or " ".join([*naam.get("given", []), naam.get("family", "")]).strip() or "Onbekend"
    nummers = ", ".join(i.get("value", "") for i in pat.get("identifier", []))
    auteurs = ", ".join(wie(bron.get(a.get("reference"), {})) for a in doc.get("author", []))
    beheerder = wie(bron.get(doc.get("custodian", {}).get("reference"), {}))

    feiten = [("Geboren", datum(pat.get("birthDate"))), ("Geslacht", GESLACHT.get(pat.get("gender"), pat.get("gender"))),
              ("Nummer", nummers), ("Opgesteld", datum(doc.get("date"))), ("Door", auteurs), ("Praktijk", beheerder)]
    delen = [f"""<div class="kop"><small>Patient Summary</small><h1>{e(volledig)}</h1>
<p>Dit is wat een arts ziet die dit dossier ontvangt.</p>
<div class="feiten">{"".join(f"<div><b>{k}</b>{e(v)}</div>" for k, v in feiten if v)}</div></div>"""]

    for s in doc.get("section", []):
        rijen = [regel(bron.get(x.get("reference"), {}), bron) for x in s.get("entry", [])]
        kopcode = codes(s.get("code"))
        if rijen:
            inhoud = "<table><tr><th>Wat</th><th>Codes</th><th>Details</th></tr>" + "".join(
                f"<tr><td>{e(wat)}</td><td>{c}</td><td>{e(d)}</td></tr>" for wat, c, d in rijen) + "</table>"
        else:
            code = next((c.get("code") for c in (s.get("emptyReason") or {}).get("coding", [])), "")
            reden = LEEG.get(code) or naam_van(s.get("emptyReason")) or "geen gegevens"
            inhoud = f'<p class="leeg">Leeg. Reden: {e(reden)}.</p>'
        delen.append(f'<section><h2>{e(s.get("title", ""))}<span>{kopcode}</span></h2>{inhoud}</section>')

    delen.append(f'<p class="voet">Gemaakt uit {e(pad.name)} door tools/bekijk.py. '
                 "De codes zijn wat de computer van de ontvanger leest; de tekst is voor mensen.</p>")
    tekst = (f'<!doctype html><html lang="nl"><head><meta charset="utf-8">'
             f'<meta name="viewport" content="width=device-width,initial-scale=1">'
             f"<title>Patient Summary {e(volledig)}</title><style>{STIJL}</style></head>"
             f"<body><main>{''.join(delen)}</main></body></html>")
    uit = pad.with_suffix(".html")
    uit.write_text(tekst, encoding="utf-8")
    return uit, volledig, datum(pat.get("birthDate"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Maak leesbare pagina's van de Patient Summaries")
    parser.add_argument("bestanden", nargs="*")
    parser.add_argument("--open", action="store_true", help="open het resultaat in de browser")
    args = parser.parse_args()

    bestanden = [Path(b) for b in args.bestanden] or sorted((PROJECT / "output").glob("*.json"))
    if not bestanden:
        sys.exit("Niets te bekijken: output/ is leeg. Draai eerst de converter.")
    gemaakt, mislukt = [], 0
    for pad in bestanden:
        try:
            gemaakt.append(pagina(pad))
        except (ValueError, KeyError, IndexError, AttributeError, TypeError) as fout:
            mislukt += 1
            print(f"  Overgeslagen: {pad.name} ({type(fout).__name__})")

    doel = gemaakt[0][0] if len(bestanden) == 1 and gemaakt else None
    if len(bestanden) > 1 and gemaakt:
        doel = gemaakt[0][0].parent / "index.html"
        items = "".join(f'<a href="{e(p.name)}"><b>{e(n)}</b><br><span>geboren {e(g)}, {e(p.stem)}</span></a>'
                        for p, n, g in gemaakt)
        doel.write_text(f'<!doctype html><html lang="nl"><head><meta charset="utf-8">'
                        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                        f"<title>Patient Summaries</title><style>{STIJL}</style></head><body><main>"
                        f'<div class="kop"><small>Overzicht</small><h1>{len(gemaakt)} Patient Summaries</h1>'
                        f"<p>Klik op een dossier om het te bekijken zoals de ontvanger het ziet.</p></div>"
                        f'<div class="lijst">{items}</div></main></body></html>', encoding="utf-8")
    # Alleen bestandsnamen en aantallen in de terminal: geen gegevens (veilige route).
    print(f"{len(gemaakt)} pagina('s) gemaakt in {gemaakt[0][0].parent.name}/" if gemaakt else "Geen pagina's gemaakt.")
    if doel:
        print(f"Open: {doel.relative_to(PROJECT) if doel.is_relative_to(PROJECT) else doel}")
        if args.open:
            webbrowser.open(doel.resolve().as_uri())
    return 1 if mislukt else 0


if __name__ == "__main__":
    sys.exit(main())
