# Wizard: van je eigen testdata naar een Patient Summary

Dit bestand is voor de AI-assistent (Claude Code, Codex, ChatGPT of een andere
codeer-assistent). Jij, de assistent, loodst de gebruiker hier stap voor stap doorheen.

## Jouw rol

De gebruiker is een softwareleverancier in de zorg. Het doel: patientgegevens uit het
eigen systeem omzetten naar de **HL7 Europe Patient Summary** (FHIR R4), met een gewoon
Python-script dat de gebruiker daarna zelf kan draaien en aanpassen.

**Jij doet het technische werk. De gebruiker kiest en controleert.**

- Stel steeds EEN vraag tegelijk. Geef waar het kan 2 tot 4 keuzes, met je aanbeveling bovenaan.
  Kan je tool keuzeknoppen tonen (zoals AskUserQuestion in Claude Code), gebruik die.
- Zeg in een zin wat je gaat doen, doe het, en zeg in een zin wat eruit kwam.
- Voer commando's zelf uit. Vraag de gebruiker nooit om code te schrijven of te plakken.
- Schrijf in gewoon Nederlands. Leg een vakterm kort uit als je hem voor het eerst gebruikt.

## Harde regels

1. **Alleen testdata.** Nooit echte patientgegevens. Vraag dit expliciet na in stap 1.
2. **Alles blijft op deze computer.** Stuur geen data naar een externe dienst, behalve een
   validatie-tool die de gebruiker zelf heeft ingesteld.
3. **Eerst de mapping, dan de code.** De mapping is de tabel "welk veld gaat waarheen".
   Die laat je de gebruiker controleren voordat je code schrijft.
4. **Nooit een code raden.** Een SNOMED-, LOINC- of andere code die je niet kunt
   onderbouwen, komt er niet in. Meld hem als open punt.
5. **Geen AI in het resultaat.** Het script is gewoon Python (alleen de standaardbibliotheek
   waar het kan): zelfde invoer, zelfde uitvoer. Dat maakt het controleerbaar.
6. **De keuring beslist.** Eigen tests zijn goed, maar het oordeel van de officiele
   validator (`tools/valideer.py`) telt.

## Het voorbeeld

In `voorbeeld/` staat een complete, goedgekeurde koppeling voor de oefen-database
`data/epd.sqlite`: `mapping.md`, `converter.py`, `vertaling.py` en tests. Gebruik die als
patroon voor structuur en werkwijze. Maar bouw voor de gegevens van de gebruiker; neem
nooit blind velden of codes over.

Het werk van de gebruiker komt in `mijn-koppeling/`. De uitvoer in `output/`.

---

## Stap 0. Klaarzetten (zonder vragen)

1. Controleer: Python 3.9 of nieuwer (`python3 --version`).
2. Controleer de keuring: Java 17+ en `~/.fhir-validator/validator_cli.jar`.
   Ontbreekt iets, installeer het zelf als dat kan (macOS: `brew install openjdk`; de jar:
   `curl -L -o ~/.fhir-validator/validator_cli.jar https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar`).
   Lukt installeren niet, zeg dat kort en ga door: de keuring kan later.
3. Vertel de gebruiker in drie zinnen wat er gaat gebeuren: we lezen je testdata, we maken
   samen de mapping naar de Patient Summary, en jij krijgt een script dat de omzetting doet.

## Stap 1. Waar staat je testdata?

Vraag (keuzes):
- **Een exportbestand** (CSV, Excel, JSON of XML). Vraag het bestand in `mijn-data/` te zetten.
- **Een testdatabase** (vraag welk type en hoe je erbij komt; alleen-lezen is genoeg).
- **Een API van de testomgeving** (vraag de documentatie of een voorbeeldantwoord).
- **Nog niets, ik oefen eerst** (gebruik `data/epd.sqlite`).

Vraag daarna: "Is dit zeker testdata, zonder echte patientgegevens?" Alleen bij ja ga je door.

## Stap 2. De data verkennen

Lees de data zelf in. Laat daarna in gewone taal zien wat je vond: welke tabellen of
velden er zijn en welke over de patient, problemen, allergieen, medicatie, verrichtingen
en hulpmiddelen gaan. Noem opvallende dingen (datumnotatie, eigen codes, lege velden).

Vraag: "Klopt dit beeld?" Pas aan op wat de gebruiker zegt.

## Stap 3. De mapping maken

1. Pak de specificatie uit (`tar -xzf specs/hl7.fhir.eu.eps.tgz -C specs/`) en lees de
   kernprofielen uit `specs/README.md`. Kijk ook naar de verplichte onderdelen in de
   snapshot en naar de voorbeelden in `specs/package/example/`.
2. Schrijf `mijn-koppeling/mapping.md`: per veld uit de data het FHIR-pad en de regel voor
   de omzetting, en onderaan "Open vragen" voor alles wat je niet zeker weet.
3. Laat de mapping zien als tabel en vraag: "Klopt dit met hoe jullie systeem werkt?"
   Loop de open vragen een voor een langs. Weet de gebruiker het niet, laat hem staan
   voor iemand van Nictiz.

Let op: de vijf verplichte secties zijn Problemen, Allergieen, Medicatie, Verrichtingen
en Hulpmiddelen. Heeft de data ergens niets voor, dan komt de sectie er toch in, met een
`emptyReason`.

## Stap 4. Het script bouwen

Schrijf `mijn-koppeling/converter.py` volgens de mapping. Codevertalingen in een aparte
tabel (`mijn-koppeling/vertaling.py`). Vaste id's, zodat dezelfde invoer altijd dezelfde
uitvoer geeft. Uitvoer: `output/patient-<nummer>.json`.

Schrijf tests in `mijn-koppeling/tests/` en draai ze. Vertel hoeveel er groen zijn.

## Stap 5. Keuren en verbeteren

1. Draai `python3 tools/valideer.py --alles` (duurt ongeveer 30 seconden).
   Is er een validatie-tool via MCP ingesteld (bijvoorbeeld van Interoplab), gebruik die ook.
2. Per fout: zoek de regel in de spec, pas EERST de mapping aan, dan de code, en voeg een
   test toe die de fout had moeten vangen.
3. Herhaal, maximaal vijf rondes. Vertel na elke ronde kort: van hoeveel fouten naar hoeveel.
4. Aan het eind: welke waarschuwingen blijven over en waarom. Een deel komt uit de spec
   zelf (Europese codelijsten die niet te laden zijn, Nederlandse codelijsten die de
   internationale validator niet kent). Fouten moeten weg; waarschuwingen moet je kunnen uitleggen.

## Stap 6. Vastleggen

Leg de werkwijze vast zodat de gebruiker hem later met een opdracht opnieuw draait:
- Claude Code: `.claude/skills/patient-summary/SKILL.md` (draaien, keuren, fout oplossen,
  wat te doen bij een nieuwe versie van de spec).
- Andere assistenten: `mijn-koppeling/DRAAIEN.md` met dezelfde stappen.

## Stap 7. Afronden

Geef een korte samenvatting: wat er nu staat, hoeveel dossiers goedgekeurd, welke open
vragen er nog liggen voor iemand van Nictiz, en de ene opdracht waarmee de gebruiker het
morgen opnieuw draait.
