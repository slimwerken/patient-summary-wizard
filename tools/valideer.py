#!/usr/bin/env python3
"""Keurt Patient Summary-bundels met de officiele HL7 FHIR-validator.

De validator is een onafhankelijke meetlat: hij leest niet onze code of onze
mapping, alleen de gepubliceerde profielen van de HL7 Europe Patient Summary
(specs/hl7.fhir.eu.eps.tgz). Wat hij goedkeurt voldoet aan de spec.

Gebruik:
    python3 tools/valideer.py                     alles in output/
    python3 tools/valideer.py output/patient-1001.json
    python3 tools/valideer.py --alles             ook waarschuwingen tonen
    python3 tools/valideer.py --offline           zonder terminologieserver

Nodig: Java 17 of nieuwer en de validator in ~/.fhir-validator/validator_cli.jar.
De eerste keer haalt hij de benodigde FHIR-pakketten op (internet nodig).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SPEC = PROJECT / "specs" / "hl7.fhir.eu.eps.tgz"
JAR = Path.home() / ".fhir-validator" / "validator_cli.jar"
REGEL = re.compile(r"^\[(-?\d+), ?(-?\d+)\] (.*?): (Error|Warning|Information|Fatal) - (.*)$")


def vind_java() -> str:
    kandidaten = []
    if os.environ.get("JAVA_HOME"):
        kandidaten.append(Path(os.environ["JAVA_HOME"]) / "bin" / "java")
    kandidaten += [Path("/opt/homebrew/opt/openjdk/bin/java"), Path("/usr/local/opt/openjdk/bin/java")]
    if shutil.which("java"):
        kandidaten.append(Path(shutil.which("java")))
    for java in kandidaten:
        if java.exists():
            probeer = subprocess.run([str(java), "-version"], capture_output=True, text=True)
            if probeer.returncode == 0:
                return str(java)
    sys.exit("Geen werkende Java gevonden. Installeer Java 17+ (bijvoorbeeld: brew install openjdk).")


def keur(bestanden, offline: bool) -> str:
    if not JAR.exists():
        sys.exit(f"Validator niet gevonden op {JAR}. Download: "
                 "https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar")
    opdracht = [vind_java(), "-jar", str(JAR), *map(str, bestanden),
                "-version", "4.0.1", "-ig", str(SPEC), "-output-style", "compact"]
    if offline:
        opdracht += ["-tx", "n/a"]
    uit = subprocess.run(opdracht, capture_output=True, text=True, cwd=PROJECT)
    return uit.stdout + uit.stderr


def lees_uitslag(tekst: str) -> dict:
    """Compacte validator-uitvoer -> {bestand: [(niveau, pad, bericht), ...]}"""
    uitslag, huidig = {}, None
    regels = tekst.splitlines()
    for i, regel in enumerate(regels):
        if regel.startswith("-----") and i + 1 < len(regels):
            huidig = regels[i + 1].rsplit(" ", 1)[0].strip()
            uitslag[huidig] = []
            continue
        m = REGEL.match(regel)
        if m and huidig:
            _, _, pad, niveau, bericht = m.groups()
            if niveau == "Fatal":
                niveau = "Error"
            if niveau != "Information":
                uitslag[huidig].append((niveau, pad, bericht))
    return uitslag


def main() -> int:
    parser = argparse.ArgumentParser(description="Keur Patient Summary-bundels")
    parser.add_argument("bestanden", nargs="*")
    parser.add_argument("--alles", action="store_true", help="toon ook de waarschuwingen")
    parser.add_argument("--offline", action="store_true", help="codes niet online controleren")
    args = parser.parse_args()

    bestanden = [Path(b) for b in args.bestanden] or sorted((PROJECT / "output").glob("*.json"))
    if not bestanden:
        sys.exit("Niets te keuren: output/ is leeg. Draai eerst de converter.")

    print(f"Keuring van {len(bestanden)} bundel(s) tegen HL7 Europe Patient Summary ...", flush=True)
    uitvoer = keur(bestanden, args.offline)
    uitslag = lees_uitslag(uitvoer)
    if not uitslag:
        print(uitvoer[-3000:])
        sys.exit("De validator gaf geen leesbare uitslag, zie hierboven.")

    totaal_fouten = 0
    for bestand, meldingen in uitslag.items():
        fouten = [m for m in meldingen if m[0] == "Error"]
        waarschuwingen = [m for m in meldingen if m[0] == "Warning"]
        totaal_fouten += len(fouten)
        teken = "✓" if not fouten else "✗"
        print(f"{teken} {Path(bestand).name}: {len(fouten)} fouten, {len(waarschuwingen)} waarschuwingen")
        for _, pad, bericht in fouten:
            print(f"    FOUT  {pad}\n          {bericht}")
        if args.alles:
            for _, pad, bericht in waarschuwingen:
                print(f"    let op {pad}\n          {bericht}")
    print("\nAlles goedgekeurd." if not totaal_fouten else f"\n{totaal_fouten} fout(en) om op te lossen.")
    alle_fouten = [m for meldingen in uitslag.values() for m in meldingen if m[0] == "Error"]
    slice_fouten = [m for m in alle_fouten if "a matching slice is required" in m[2]]
    if slice_fouten and len(slice_fouten) < len(alle_fouten):
        print("Tip: 'a matching slice is required' is meestal een gevolgfout. Los eerst de andere "
              "fouten op; past een onderdeel weer aan zijn profiel, dan verdwijnt deze vanzelf.")
    return 1 if totaal_fouten else 0


if __name__ == "__main__":
    sys.exit(main())
