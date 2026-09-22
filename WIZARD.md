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
   validatie-tool die de gebruiker zelf heeft ingesteld. Losse CODES opzoeken bij de
   terminologieserver (tx.fhir.org, die gebruikt de keuring ook) mag wel: daar gaat
   nooit patientinformatie heen, alleen de code.
3. **Eerst de mapping, dan de code.** De mapping is de tabel "welk veld gaat waarheen".
   Die laat je de gebruiker controleren voordat je code schrijft.
4. **Nooit een code raden.** Een SNOMED-, LOINC- of andere code die je niet kunt
   onderbouwen, komt er niet in. Meld hem als open punt.
5. **Geen AI in het resultaat.** Het script is gewoon Python (alleen de standaardbibliotheek
   waar het kan): zelfde invoer, zelfde uitvoer. Dat maakt het controleerbaar.
6. **De keuring beslist over de vorm, een mens over de inhoud.** Eigen tests zijn goed,
   maar over de vorm telt het oordeel van de officiele validator (`tools/valideer.py`).
   De validator ziet niet of een code de juiste betekenis heeft. Dat controleert de
   gebruiker in de mapping. Zeg dat erbij als je "goedgekeurd" meldt.

## Het voorbeeld

In `voorbeeld/` staat een complete, goedgekeurde koppeling voor de oefen-database
`data/epd.sqlite`: `mapping.md`, `converter.py`, `vertaling.py` en tests. Gebruik die als
patroon voor structuur en werkwijze. Maar bouw voor de gegevens van de gebruiker; neem
nooit blind velden of codes over.

Het werk van de gebruiker komt in `mijn-koppeling/`. De uitvoer in `output/`.

---

## Stap 0. Klaarzetten (zonder vragen)

1. Draai `python3 tools/valideer.py --controleer`. Dat controleert Python en Java, haalt
   de validator op als hij ontbreekt en doet een proefkeuring (de eerste keer 1 tot 2
   minuten, internet nodig). Gebruik NIET `java -version` als controle: op macOS bestaat
   een nep-`java` die faalt terwijl de keuring gewoon werkt.
2. Meldt hij dat Java ontbreekt: installeer het als dat kan (macOS: `brew install openjdk`)
   en draai de controle opnieuw. Lukt het niet, zeg dat kort en ga door: de keuring kan later.
3. Vertel de gebruiker in drie zinnen wat er gaat gebeuren: we lezen je testdata, we maken
   samen de mapping naar de Patient Summary, en jij krijgt een script dat de omzetting doet.

## Stap 1. Waar staat je testdata?

Vraag (keuzes):
- **Een exportbestand** (CSV, Excel, JSON of XML). Vraag het bestand in `mijn-data/` te zetten.
  Excel inlezen gaat met openpyxl: installeer het zelf als het ontbreekt
  (`python3 -m pip install openpyxl`). Excel-formules: lees de opgeslagen uitkomst
  (`data_only=True`).
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
4. Leg de open vragen GEBUNDELD voor: maximaal vier per keer, en bij elke vraag de optie
   "Laat staan voor Nictiz". Niet een voor een; de gebruiker weet de meeste niet.

Let op bij de mapping:
- De vijf verplichte secties zijn Problemen, Allergieen, Medicatie, Verrichtingen en
  Hulpmiddelen. Heeft de data ergens niets voor, dan komt de sectie er toch in, met een
  `emptyReason`. Legt de export zelf een reden vast, neem die over. Staat er niets,
  gebruik dan `unavailable` (niet vastgelegd in het dossier); `nilknown` betekent dat een
  arts heeft vastgesteld dat er niets is, en dat weet een systeem zelf niet.
- Heeft de export geen tabel voor een verplicht onderdeel (bijvoorbeeld medicatie of
  verrichtingen), dan komt dat onderdeel er toch in, leeg, met een `emptyReason`.
- Extra gegevens zoals metingen en labuitslagen: vraag of ze mee moeten. Ze horen in de
  optionele secties voor vitale functies (LOINC 8716-3) en uitslagen (LOINC 30954-2).
- Datum-tijden zonder tijdzone: lees ze als Nederlandse tijd (Europe/Amsterdam) en zet die
  keuze in de mapping.
- Zet geen `language` op het document of de onderdelen, tenzij je bij elke code de
  Nederlandse naam gebruikt. Met `language` = nl eist de keuring Nederlandse namen bij
  alle LOINC- en SNOMED-codes. Zonder `language` gebruik je de officiele Engelse namen.
- De Patient Summary werkt het liefst met SNOMED CT. Heeft het systeem andere codes
  (ICPC, ICD-10, ATC), neem die over en zet een vertaling naar SNOMED alleen erbij als
  die onderbouwd is. De rest wordt een open vraag.

## Stap 4. Het script bouwen

Schrijf `mijn-koppeling/converter.py` volgens de mapping. Codevertalingen in een aparte
tabel (`mijn-koppeling/vertaling.py`). Vaste id's, zodat dezelfde invoer altijd dezelfde
uitvoer geeft. Het documenttijdstip is standaard "nu"; geef een optie `--datum` zodat een
run exact te herhalen is (ook voor de tests). Uitvoer: `output/patient-<nummer>.json`.

Schrijf tests in `mijn-koppeling/tests/` en draai ze. Vertel hoeveel er groen zijn.

## Stap 5. Keuren en verbeteren

1. Draai `python3 tools/valideer.py --alles` (duurt ongeveer 30 seconden). Onderaan staat
   een samenvatting per soort melding; begin daar, niet bij de losse regels.
2. Extra keuring van Interoplab (optioneel). In `.mcp.json` staat hun validator als
   MCP-server. Claude Code vraagt de eerste keer of je hem wilt gebruiken; daarna logt de
   gebruiker in met een Microsoft-account via `/mcp` (kies interoplab, dan Authenticate).
   Stuur er alleen testdata naartoe. Lukt inloggen niet of ligt de server eruit, ga dan
   gewoon door met `tools/valideer.py`: de middag hangt er niet van af.
3. Per fout: zoek de regel in de spec, pas EERST de mapping aan, dan de code, en voeg een
   test toe die de fout had moeten vangen.
4. Herhaal, maximaal vijf rondes. Vertel na elke ronde kort: van hoeveel fouten naar hoeveel.
5. Ook als de eerste ronde al 0 fouten geeft: loop de adviezen over codelijsten na
   (zichtbaar met `--alles`). Die zeggen welke codes de spec liever ziet.
6. Aan het eind: welke waarschuwingen blijven over en waarom. Een deel komt uit de spec
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
