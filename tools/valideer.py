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
    python3 tools/valideer.py --controleer        alles klaarzetten en een proefkeuring

Nodig: Java 17 of nieuwer en de validator in ~/.fhir-validator/validator_cli.jar.
De eerste keuring haalt de FHIR-pakketten op (internet nodig). Doe daarom vooraf
een keer --controleer, dan gaat het op de dag zelf snel.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SPEC = PROJECT / "specs" / "hl7.fhir.eu.eps.tgz"
JAR = Path.home() / ".fhir-validator" / "validator_cli.jar"
JAR_URL = "https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar"
REGEL = re.compile(r"^\[(-?\d+), ?(-?\d+)\] (.*?): (Error|Warning|Information|Fatal) - (.*)$")


def vind_java(verplicht: bool = True):
    """Zoekt een werkende Java. Let op: op macOS bestaat /usr/bin/java ook zonder
    Java; dat ding faalt. Daarom proberen we elke kandidaat echt te starten."""
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
    if verplicht:
        sys.exit("Geen werkende Java gevonden. Installeer Java 17+ (macOS: brew install openjdk).")
    return None


def keur(bestanden, offline: bool) -> str:
    if not JAR.exists():
        sys.exit(f"Validator niet gevonden op {JAR}. Draai: python3 tools/valideer.py --controleer")
    opdracht = [vind_java(), "-jar", str(JAR), *map(str, bestanden),
                "-version", "4.0.1", "-ig", str(SPEC), "-output-style", "compact"]
    if offline:
        opdracht += ["-tx", "n/a"]
    uit = subprocess.run(opdracht, capture_output=True, text=True, cwd=PROJECT)
    return uit.stdout + uit.stderr


def controleer() -> int:
    """Zet alles klaar wat de keuring nodig heeft en doet een proefkeuring."""
    goed = True
    print(f"✓ Python {sys.version.split()[0]}")
    java = vind_java(verplicht=False)
    if java:
        print(f"✓ Java gevonden: {java}")
    else:
        goed = False
        print("✗ Geen werkende Java. Installeer Java 17+ (macOS: brew install openjdk) en draai dit opnieuw.")
    if JAR.exists():
        print(f"✓ Validator staat klaar: {JAR}")
    else:
        print("… Validator downloaden (ongeveer 200 MB)")
        uit = subprocess.run(["curl", "-sL", "--create-dirs", "-o", str(JAR), JAR_URL])
        if uit.returncode == 0 and JAR.exists() and JAR.stat().st_size > 1_000_000:
            print(f"✓ Validator gedownload: {JAR}")
        else:
            goed = False
            print(f"✗ Download mislukt. Download hem met de hand van {JAR_URL} naar {JAR}")
    print(f"{'✓' if SPEC.exists() else '✗'} Specificatie: {SPEC.relative_to(PROJECT)}")
    goed = goed and SPEC.exists()
    if not goed:
        return 1
    print("… Proefkeuring met het officiele voorbeeld (de eerste keer 1 tot 2 minuten)", flush=True)
    with tarfile.open(SPEC) as tgz, tempfile.TemporaryDirectory() as tmp:
        naam = "package/example/Bundle-EPSExampleBundle01NoProblemsMedicationAllergies.json"
        tgz.extract(naam, tmp)
        uitslag = lees_uitslag(keur([Path(tmp) / naam], offline=False))
    fouten = sum(1 for m in uitslag.values() for x in m if x[0] == "Error")
    if uitslag and not fouten:
        print("✓ Proefkeuring gelukt. De keuring is klaar voor gebruik.")
        return 0
    print("✗ De proefkeuring gaf geen schone uitslag. Controleer de internetverbinding en probeer opnieuw.")
    return 1


def lees_uitslag(tekst: str) -> dict:
    """Compacte validator-uitvoer -> {bestand: [(niveau, pad, bericht), ...]}

    Van de meldingen van het niveau Information bewaren we alleen de adviezen over
    codelijsten ("recommended to come from this value set"): die vertellen dat een
    andere codelijst de voorkeur heeft, en dat is nuttig om te weten."""
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
            elif "recommended to come from this value set" in bericht:
                uitslag[huidig].append(("Advies", pad, bericht))
    return uitslag


def main() -> int:
    parser = argparse.ArgumentParser(description="Keur Patient Summary-bundels")
    parser.add_argument("bestanden", nargs="*")
    parser.add_argument("--alles", action="store_true", help="toon ook de waarschuwingen")
    parser.add_argument("--offline", action="store_true", help="codes niet online controleren")
    parser.add_argument("--controleer", action="store_true", help="alles klaarzetten en een proefkeuring doen")
    args = parser.parse_args()
    if args.controleer:
        return controleer()

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
    soorten = {}
    for bestand, meldingen in uitslag.items():
        for niveau, _, bericht in meldingen:
            sleutel = (niveau, re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27}", "<id>", bericht)[:180])
            soorten[sleutel] = soorten.get(sleutel, 0) + 1
        fouten = [m for m in meldingen if m[0] == "Error"]
        waarschuwingen = [m for m in meldingen if m[0] == "Warning"]
        adviezen = [m for m in meldingen if m[0] == "Advies"]
        totaal_fouten += len(fouten)
        teken = "✓" if not fouten else "✗"
        print(f"{teken} {Path(bestand).name}: {len(fouten)} fouten, {len(waarschuwingen)} waarschuwingen, "
              f"{len(adviezen)} adviezen over codelijsten")
        for _, pad, bericht in fouten:
            print(f"    FOUT  {pad}\n          {bericht}")
        if args.alles:
            for _, pad, bericht in waarschuwingen:
                print(f"    let op {pad}\n          {bericht}")
            for _, pad, bericht in adviezen:
                print(f"    advies {pad}\n          {bericht}")
    print("\nAlles goedgekeurd op de vorm. Of de inhoud klopt, beoordeelt een mens via de mapping."
          if not totaal_fouten else f"\n{totaal_fouten} fout(en) om op te lossen.")
    if soorten:
        namen = {"Error": "fout", "Warning": "let op", "Advies": "advies"}
        print("\nPer soort melding (meest voorkomend eerst):")
        for (niveau, bericht), aantal in sorted(soorten.items(), key=lambda x: (x[0][0] != "Error", -x[1]))[:12]:
            print(f"  {aantal:>4}x {namen.get(niveau, niveau)}: {bericht}")
        if len(soorten) > 12:
            print(f"  ... en nog {len(soorten) - 12} andere soorten (zie --alles)")
    alle_fouten = [m for meldingen in uitslag.values() for m in meldingen if m[0] == "Error"]
    slice_fouten = [m for m in alle_fouten if "a matching slice is required" in m[2]]
    if slice_fouten and len(slice_fouten) < len(alle_fouten):
        print("Tip: 'a matching slice is required' is meestal een gevolgfout. Los eerst de andere "
              "fouten op; past een onderdeel weer aan zijn profiel, dan verdwijnt deze vanzelf.")
    return 1 if totaal_fouten else 0


if __name__ == "__main__":
    sys.exit(main())
