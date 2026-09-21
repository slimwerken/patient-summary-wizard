#!/usr/bin/env python3
"""Zet patienten uit de eigen EPD-database om naar een HL7 Europe Patient Summary.

Per patient komt er een FHIR R4 document-bundel in output/patient-<nummer>.json,
volgens de profielen van hl7.fhir.eu.eps (zie specs/). Hoe elk EPD-veld naar
FHIR gaat staat in voorbeeld/mapping.md; dit script volgt die tabel.

Geen AI in dit script: zelfde database erin, zelfde bundels eruit. Dat maakt
het te controleren en te herhalen.

Gebruik:
    python3 voorbeeld/converter.py                  alle patienten
    python3 voorbeeld/converter.py --patient 1001   een patient
    python3 voorbeeld/converter.py --datum 2026-09-23T13:00:00+02:00
"""
import argparse
import html
import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vertaling as v  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
DATABASE = PROJECT / "data" / "epd.sqlite"
OUTPUT = PROJECT / "output" / "voorbeeld"

EPS = "http://hl7.eu/fhir/eps/StructureDefinition/"
LOINC = "http://loinc.org"
PATIENTNUMMER = "https://epd.noorderhaven.example/patientnummer"

# Vaste basis voor de id's: dezelfde rij geeft altijd dezelfde id
NAMESPACE = uuid.UUID("6f1c1a2e-4d3b-5a7c-9e8f-0a1b2c3d4e5f")

SECTIES = {
    "problemen": ("11450-4", "Problem list - Reported", "Problemen"),
    "allergieen": ("48765-2", "Allergies and adverse reactions Document", "Allergieen en intoleranties"),
    "medicatie": ("10160-0", "History of Medication use Narrative", "Medicatie"),
    "verrichtingen": ("47519-4", "History of Procedures Document", "Verrichtingen"),
    "hulpmiddelen": ("46264-8", "History of medical device use", "Medische hulpmiddelen"),
}


# ---------------------------------------------------------------- hulpjes

def vaste_id(soort: str, sleutel) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{soort}/{sleutel}"))


def url(resource_id: str) -> str:
    return f"urn:uuid:{resource_id}"


def leeg(waarde) -> bool:
    """NULL en een lege string betekenen in dit EPD allebei: niet ingevuld."""
    return waarde is None or str(waarde).strip() == ""


def fhir_datum(nl_datum):
    """DD-MM-JJJJ uit het EPD naar JJJJ-MM-DD voor FHIR. Leeg blijft None."""
    if leeg(nl_datum):
        return None
    return datetime.strptime(nl_datum.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")


def volledige_naam(voornaam, tussenvoegsel, achternaam) -> str:
    return " ".join(d for d in (voornaam, tussenvoegsel, achternaam) if not leeg(d))


def achternaam_fhir(tussenvoegsel, achternaam) -> dict:
    """Nederlandse achternaam: 'de Boer' met het voorvoegsel apart gemarkeerd."""
    familie = volledige_naam(None, tussenvoegsel, achternaam)
    extensies = []
    if not leeg(tussenvoegsel):
        extensies.append({"url": "http://hl7.org/fhir/StructureDefinition/humanname-own-prefix",
                          "valueString": tussenvoegsel})
    extensies.append({"url": "http://hl7.org/fhir/StructureDefinition/humanname-own-name",
                      "valueString": achternaam})
    return {"family": familie, "_family": {"extension": extensies}}


def codering(system: str, code: str, display: str) -> dict:
    return {"system": system, "code": code, "display": display}


def verhaal(kolommen, rijen) -> dict:
    """Leesbare tabel voor de mens die het document opent (section.text)."""
    kop = "".join(f"<th>{html.escape(k)}</th>" for k in kolommen)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(c or ''))}</td>" for c in rij) + "</tr>"
        for rij in rijen
    )
    div = f'<div xmlns="http://www.w3.org/1999/xhtml"><table><tr>{kop}</tr>{body}</table></div>'
    return {"status": "generated", "div": div}


def leeg_verhaal(tekst: str) -> dict:
    return {"status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{html.escape(tekst)}</p></div>'}


def samenvatting(*delen) -> dict:
    """Korte leesbare zin per resource (FHIR-regel dom-6: elk onderdeel leesbaar voor een mens)."""
    zin = ", ".join(str(d) for d in delen if not leeg(d))
    return {"status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{html.escape(zin)}</p></div>'}


# ---------------------------------------------------------------- lezen

def rijen(conn, sql, *args):
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


def lees_patient(conn, pat_id: int) -> dict:
    patient = rijen(conn, "SELECT * FROM patienten WHERE pat_id = ?", pat_id)
    if not patient:
        raise SystemExit(f"Patient {pat_id} staat niet in de database.")
    p = patient[0]
    arts = rijen(conn, "SELECT * FROM huisartsen WHERE arts_id = ?", p["arts_id"])[0]
    praktijk = rijen(conn, "SELECT * FROM praktijk WHERE praktijk_id = ?", arts["praktijk_id"])[0]
    return {
        "patient": p,
        "arts": arts,
        "praktijk": praktijk,
        "episodes": rijen(conn, "SELECT * FROM episodes WHERE pat_id = ? ORDER BY ep_id", pat_id),
        "medicatie": rijen(conn, "SELECT * FROM medicatie WHERE pat_id = ? ORDER BY med_id", pat_id),
        "allergieen": rijen(conn, "SELECT * FROM allergieen WHERE pat_id = ? ORDER BY allergie_id", pat_id),
        "verrichtingen": rijen(conn, "SELECT * FROM verrichtingen WHERE pat_id = ? ORDER BY verrichting_id", pat_id),
        "hulpmiddelen": rijen(conn, "SELECT * FROM hulpmiddelen WHERE pat_id = ? ORDER BY hulpmiddel_id", pat_id),
    }


# ---------------------------------------------------------------- bouwen

def maak_patient(p: dict, arts_ref: str) -> dict:
    res = {
        "resourceType": "Patient",
        "id": vaste_id("patient", p["pat_id"]),
        "meta": {"profile": [EPS + "patient-eu-eps"]},
        "text": samenvatting(volledige_naam(p["voornaam"], p["tussenvoegsel"], p["achternaam"]),
                             f"geboren {p['geboortedatum']}", f"patientnummer {p['pat_id']}"),
        "identifier": [{"system": PATIENTNUMMER, "value": str(p["pat_id"])}],
        "name": [{
            "text": volledige_naam(p["voornaam"], p["tussenvoegsel"], p["achternaam"]),
            **achternaam_fhir(p["tussenvoegsel"], p["achternaam"]),
            "given": [p["voornaam"]] if not leeg(p["voornaam"]) else [],
        }],
        "gender": v.GESLACHT.get((p["geslacht"] or "").strip(), "unknown"),
        "birthDate": fhir_datum(p["geboortedatum"]),
        "address": [{
            "use": "home",
            "line": [f"{p['straat']} {p['huisnummer']}"],
            "postalCode": p["postcode"],
            "city": p["woonplaats"],
            "country": "NL",
        }],
        "generalPractitioner": [{"reference": arts_ref}],
    }
    if not leeg(p["telefoon"]):
        res["telecom"] = [{"system": "phone", "value": p["telefoon"]}]
    if not res["name"][0]["given"]:
        del res["name"][0]["given"]
    return res


def maak_arts(a: dict) -> dict:
    naam = achternaam_fhir(a["tussenvoegsel"], a["achternaam"])
    naam["text"] = volledige_naam(a["voorletters"], a["tussenvoegsel"], a["achternaam"])
    naam["given"] = [a["voorletters"]]
    return {
        "resourceType": "Practitioner",
        "id": vaste_id("arts", a["arts_id"]),
        "text": samenvatting("Huisarts", naam["text"]),
        "name": [naam],
    }


def maak_praktijk(pr: dict) -> dict:
    return {
        "resourceType": "Organization",
        "id": vaste_id("praktijk", pr["praktijk_id"]),
        "text": samenvatting(pr["naam"], pr["plaats"]),
        "name": pr["naam"],
        "telecom": [{"system": "phone", "value": pr["telefoon"]}],
        "address": [{"line": [pr["straat"]], "postalCode": pr["postcode"],
                     "city": pr["plaats"], "country": "NL"}],
    }


def maak_probleem(e: dict, pat_ref: str, gaten: list) -> dict:
    coderingen = []
    snomed = v.ICPC_NAAR_SNOMED.get(e["icpc"])
    if snomed:
        coderingen.append(codering(v.SNOMED, *snomed))
    else:
        gaten.append(f"ICPC {e['icpc']} ({e['omschrijving']}) heeft geen SNOMED-vertaling")
    coderingen.append(codering(v.ICPC, e["icpc"], e["omschrijving"]))

    afgesloten = (e["actief"] or "").upper() == "N" or not leeg(e["einddatum"])
    res = {
        "resourceType": "Condition",
        "id": vaste_id("episode", e["ep_id"]),
        "text": samenvatting(e["omschrijving"], f"ICPC {e['icpc']}", f"sinds {e['begindatum']}",
                             f"tot {e['einddatum']}" if not leeg(e["einddatum"]) else None),
        "clinicalStatus": {"coding": [codering(
            "http://terminology.hl7.org/CodeSystem/condition-clinical",
            *(("resolved", "Resolved") if afgesloten else ("active", "Active")))]},
        "category": [{"coding": [codering(
            "http://terminology.hl7.org/CodeSystem/condition-category",
            "problem-list-item", "Problem List Item")]}],
        "code": {"coding": coderingen, "text": e["omschrijving"]},
        "subject": {"reference": pat_ref},
    }
    if fhir_datum(e["begindatum"]):
        res["onsetDateTime"] = fhir_datum(e["begindatum"])
    if fhir_datum(e["einddatum"]):
        res["abatementDateTime"] = fhir_datum(e["einddatum"])
    return res


def maak_allergie(a: dict, pat_ref: str, gaten: list) -> dict:
    code = {"text": a["stof"]}
    snomed = v.ALLERGIE_NAAR_SNOMED.get(a["stof"].strip().lower())
    if snomed:
        code["coding"] = [codering(v.SNOMED, *snomed)]
    else:
        gaten.append(f"allergie '{a['stof']}' heeft geen SNOMED-vertaling")
    res = {
        "resourceType": "AllergyIntolerance",
        "id": vaste_id("allergie", a["allergie_id"]),
        "text": samenvatting(f"Allergie voor {a['stof']}", a["ernst"]),
        "clinicalStatus": {"coding": [codering(
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "active", "Active")]},
        "verificationStatus": {"coding": [codering(
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "confirmed", "Confirmed")]},
        "type": "allergy",
        "code": code,
        "patient": {"reference": pat_ref},
    }
    categorie = v.ALLERGIE_CATEGORIE.get((a["categorie"] or "").lower())
    if categorie:
        res["category"] = [categorie]
    ernst = v.ALLERGIE_ERNST.get((a["ernst"] or "").lower())
    if ernst:
        res["criticality"] = ernst
    if fhir_datum(a["vastgelegd"]):
        res["recordedDate"] = fhir_datum(a["vastgelegd"])
    return res


def maak_medicatie(m: dict, pat_ref: str, gaten: list) -> dict:
    naam = v.ATC_NAMEN.get(m["atc"])
    if not naam:
        gaten.append(f"ATC {m['atc']} ({m['middel']}) staat niet in de namenlijst")
    periode = {"start": fhir_datum(m["startdatum"])}
    if fhir_datum(m["stopdatum"]):
        periode["end"] = fhir_datum(m["stopdatum"])
    res = {
        "resourceType": "MedicationStatement",
        "id": vaste_id("medicatie", m["med_id"]),
        "meta": {"profile": [EPS + "medicationStatement-eu-eps"]},
        "text": samenvatting(m["middel"], m["gebruik"], f"vanaf {m['startdatum']}",
                             f"tot {m['stopdatum']}" if not leeg(m["stopdatum"]) else None),
        "status": "completed" if "end" in periode else "active",
        "medicationCodeableConcept": {
            "coding": [codering(v.ATC, m["atc"], naam or m["middel"])],
            "text": m["middel"],
        },
        "subject": {"reference": pat_ref},
        "effectivePeriod": periode,
    }
    if not leeg(m["gebruik"]):
        res["dosage"] = [{"text": m["gebruik"]}]
    return res


def maak_verrichting(vr: dict, pat_ref: str, gaten: list) -> dict:
    code = {"text": vr["omschrijving"]}
    snomed = v.VERRICHTING_NAAR_SNOMED.get(vr["omschrijving"].strip().lower())
    if snomed:
        code["coding"] = [codering(v.SNOMED, *snomed)]
    else:
        gaten.append(f"verrichting '{vr['omschrijving']}' heeft geen SNOMED-vertaling")
    res = {
        "resourceType": "Procedure",
        "id": vaste_id("verrichting", vr["verrichting_id"]),
        "meta": {"profile": [EPS + "procedure-eu-eps"]},
        "text": samenvatting(vr["omschrijving"], vr["datum"]),
        "status": "completed",
        "code": code,
        "subject": {"reference": pat_ref},
    }
    if fhir_datum(vr["datum"]):
        res["performedDateTime"] = fhir_datum(vr["datum"])
    return res


def maak_hulpmiddel(h: dict, pat_ref: str, gaten: list) -> tuple:
    type_ = {"text": h["omschrijving"]}
    snomed = v.HULPMIDDEL_NAAR_SNOMED.get(h["omschrijving"].strip().lower())
    if snomed:
        type_["coding"] = [codering(v.SNOMED, *snomed)]
    else:
        gaten.append(f"hulpmiddel '{h['omschrijving']}' heeft geen SNOMED-vertaling")
    apparaat = {
        "resourceType": "Device",
        "id": vaste_id("hulpmiddel", h["hulpmiddel_id"]),
        "meta": {"profile": [EPS + "device-eu-eps"]},
        "text": samenvatting(h["omschrijving"]),
        "type": type_,
        "patient": {"reference": pat_ref},
    }
    gebruik = {
        "resourceType": "DeviceUseStatement",
        "id": vaste_id("hulpmiddelgebruik", h["hulpmiddel_id"]),
        "meta": {"profile": [EPS + "deviceUseStatement-eu-eps"]},
        "text": samenvatting(f"Gebruikt {h['omschrijving']}", f"sinds {h['sinds']}"),
        "status": "active",
        "subject": {"reference": pat_ref},
        "timingPeriod": {"start": fhir_datum(h["sinds"])},
        "device": {"reference": url(apparaat["id"]), "display": h["omschrijving"]},
    }
    return apparaat, gebruik


def sectie(sleutel: str, resources: list, tabel: dict) -> dict:
    code, display, titel = SECTIES[sleutel]
    s = {"title": titel, "code": {"coding": [codering(LOINC, code, display)]}}
    if resources:
        s["text"] = verhaal(tabel["kolommen"], tabel["rijen"])
        s["entry"] = [{"reference": url(r["id"])} for r in resources]
    else:
        # Niets vastgelegd in het EPD: zeg dat expliciet, laat de sectie niet weg
        s["text"] = leeg_verhaal("Geen gegevens bekend in het dossier.")
        s["emptyReason"] = {"coding": [codering(
            "http://terminology.hl7.org/CodeSystem/list-empty-reason", "nilknown", "Nil Known")]}
    return s


def maak_patient_summary(dossier: dict, tijdstip: str) -> tuple:
    """Geeft (bundel, gaten). Gaten zijn de dingen die de koppeling niet kon vertalen."""
    gaten = []
    p = dossier["patient"]
    arts = maak_arts(dossier["arts"])
    praktijk = maak_praktijk(dossier["praktijk"])
    patient = maak_patient(p, url(arts["id"]))
    pat_ref = url(patient["id"])

    problemen = [maak_probleem(e, pat_ref, gaten) for e in dossier["episodes"]]
    allergieen = [maak_allergie(a, pat_ref, gaten) for a in dossier["allergieen"]]
    medicatie = [maak_medicatie(m, pat_ref, gaten) for m in dossier["medicatie"]]
    verrichtingen = [maak_verrichting(vr, pat_ref, gaten) for vr in dossier["verrichtingen"]]
    hulpmiddelen = [maak_hulpmiddel(h, pat_ref, gaten) for h in dossier["hulpmiddelen"]]
    apparaten = [a for a, _ in hulpmiddelen]
    gebruik = [g for _, g in hulpmiddelen]

    secties = [
        sectie("problemen", problemen, {
            "kolommen": ["Probleem", "Sinds", "Tot", "Status"],
            "rijen": [(e["omschrijving"], e["begindatum"], e["einddatum"],
                       "afgesloten" if (e["actief"] or "").upper() == "N" else "actief")
                      for e in dossier["episodes"]]}),
        sectie("allergieen", allergieen, {
            "kolommen": ["Stof", "Soort", "Ernst"],
            "rijen": [(a["stof"], a["categorie"], a["ernst"]) for a in dossier["allergieen"]]}),
        sectie("medicatie", medicatie, {
            "kolommen": ["Middel", "Gebruik", "Start", "Stop"],
            "rijen": [(m["middel"], m["gebruik"], m["startdatum"], m["stopdatum"])
                      for m in dossier["medicatie"]]}),
        sectie("verrichtingen", verrichtingen, {
            "kolommen": ["Verrichting", "Datum"],
            "rijen": [(vr["omschrijving"], vr["datum"]) for vr in dossier["verrichtingen"]]}),
        sectie("hulpmiddelen", gebruik, {
            "kolommen": ["Hulpmiddel", "Sinds"],
            "rijen": [(h["omschrijving"], h["sinds"]) for h in dossier["hulpmiddelen"]]}),
    ]

    compositie = {
        "resourceType": "Composition",
        "id": vaste_id("compositie", f"{p['pat_id']}/{tijdstip}"),
        "meta": {"profile": [EPS + "composition-eu-eps"]},
        "text": samenvatting(f"Patient Summary van {volledige_naam(p['voornaam'], p['tussenvoegsel'], p['achternaam'])}",
                             f"opgesteld {tijdstip[:10]}"),
        "identifier": {"system": "urn:ietf:rfc:9562",
                       "value": vaste_id("compositie-nummer", f"{p['pat_id']}/{tijdstip}")},
        "status": "final",
        "type": {"coding": [codering(LOINC, "60591-5", "Patient summary Document")]},
        "subject": {"reference": pat_ref,
                    "display": volledige_naam(p["voornaam"], p["tussenvoegsel"], p["achternaam"])},
        "date": tijdstip,
        "author": [{"reference": url(arts["id"])}],
        "title": "Patient Summary",
        "confidentiality": "N",
        "custodian": {"reference": url(praktijk["id"])},
        "section": secties,
    }

    inhoud = [compositie, patient, arts, praktijk,
              *problemen, *allergieen, *medicatie, *verrichtingen, *gebruik, *apparaten]
    bundel = {
        "resourceType": "Bundle",
        "id": vaste_id("bundel", f"{p['pat_id']}/{tijdstip}"),
        "meta": {"profile": [EPS + "bundle-eu-eps"]},
        "identifier": {"system": "urn:ietf:rfc:9562",
                       "value": vaste_id("document", f"{p['pat_id']}/{tijdstip}")},
        "type": "document",
        "timestamp": tijdstip,
        "entry": [{"fullUrl": url(r["id"]), "resource": r} for r in inhoud],
    }
    return bundel, gaten


# ---------------------------------------------------------------- draaien

def nu() -> str:
    return datetime.now(ZoneInfo("Europe/Amsterdam")).replace(microsecond=0).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--patient", type=int, help="alleen deze patient")
    parser.add_argument("--datum", default=None, help="tijdstip van het document (ISO), standaard nu")
    parser.add_argument("--database", default=str(DATABASE))
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()

    tijdstip = args.datum or nu()
    conn = sqlite3.connect(args.database)
    conn.row_factory = sqlite3.Row
    if args.patient:
        nummers = [args.patient]
    else:
        nummers = [r[0] for r in conn.execute("SELECT pat_id FROM patienten ORDER BY pat_id")]

    uit = Path(args.output)
    uit.mkdir(parents=True, exist_ok=True)
    totaal_gaten = 0
    for nummer in nummers:
        dossier = lees_patient(conn, nummer)
        bundel, gaten = maak_patient_summary(dossier, tijdstip)
        bestand = uit / f"patient-{nummer}.json"
        bestand.write_text(json.dumps(bundel, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        p = dossier["patient"]
        telling = (f"{len(dossier['episodes'])} problemen, {len(dossier['allergieen'])} allergieen, "
                   f"{len(dossier['medicatie'])} medicatie, {len(dossier['verrichtingen'])} verrichtingen, "
                   f"{len(dossier['hulpmiddelen'])} hulpmiddelen")
        print(f"✓ {bestand.name}  {volledige_naam(p['voornaam'], p['tussenvoegsel'], p['achternaam'])}: {telling}")
        for gat in gaten:
            print(f"  ! {gat}")
        totaal_gaten += len(gaten)
    conn.close()
    print(f"\n{len(nummers)} Patient Summaries gemaakt in {uit}/"
          + (f", {totaal_gaten} punt(en) om na te lopen" if totaal_gaten else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
