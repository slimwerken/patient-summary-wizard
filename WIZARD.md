# Wizard: van je eigen testdata naar een Patient Summary

Dit bestand is voor de AI-assistent (Claude Code, Codex of een andere codeer-assistent).
Jij, de assistent, loodst de gebruiker hier stap voor stap doorheen.

## Jouw rol

De gebruiker is een softwareleverancier in de zorg. Het doel: patientgegevens uit het
eigen systeem omzetten naar de **HL7 Europe Patient Summary** (FHIR R4), met een gewoon
Python-script dat de gebruiker daarna zelf kan draaien en aanpassen.

**Jij doet het technische werk. De gebruiker klikt en controleert.** Hou het aantal
vragen zo laag mogelijk: in een normale run zijn het er vier (zie de stappen). Alles wat
je zelf kunt uitzoeken of redelijk kunt kiezen, doe je zelf en leg je vast in de mapping.

- Stel steeds EEN vraag tegelijk, met 2 tot 4 knoppen en je aanbeveling bovenaan.
  Kan je tool keuzeknoppen tonen (AskUserQuestion in Claude Code), gebruik die altijd.
- Zeg in een zin wat je gaat doen, doe het, en zeg in een zin wat eruit kwam.
- Voer commando's zelf uit. Vraag de gebruiker nooit om code te schrijven of te plakken.
- Schrijf in gewoon Nederlands. Leg een vakterm kort uit als je hem voor het eerst gebruikt.

## Harde regels

1. **Testdata of de veilige route.** Vraag in stap 1 of het testdata is. Is het zeker
   testdata, dan mag je de bestanden zelf lezen. Is het geen testdata of weet de gebruiker
   het niet, dan volg je de VEILIGE ROUTE: je opent de bestanden in `mijn-data/` NOOIT
   zelf, ook niet een paar regels. Je leest alleen het overzicht dat `tools/overzicht.py`
   lokaal maakt (namen, adressen, nummers en geboortedatums staan daar alleen als vorm in),
   en je bekijkt ook de gemaakte dossiers in `output/` niet.
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
3. Kijk in `mijn-data/`. Staat daar iets (behalve `.gitkeep`)? Dan is dat de testdata.
4. Vertel de gebruiker in drie zinnen wat er gaat gebeuren: ik lees je testdata, ik maak
   de mapping naar de Patient Summary en jij controleert die, daarna bouw ik het script en
   laat ik het keuren.

## Stap 1. De testdata (klik 1)

Staat er iets in `mijn-data/`, stel dan EEN vraag: "In mijn-data/ staat <bestanden>. Is
dit testdata, zonder echte patientgegevens?" Knoppen:
- **Ja, alleen testdata** (aanbevolen). Je mag de bestanden zelf lezen.
- **Nee of weet ik niet.** Zeg in een zin: "Dan kijk ik niet in je bestanden. Een script
  op je eigen computer maakt een overzicht zonder namen, adressen en nummers, en alleen
  dat lees ik." Daarna volg je de veilige route (harde regel 1).

Draai in BEIDE gevallen eerst `python3 tools/overzicht.py`. Dat maakt
`mijn-koppeling/overzicht.md` en zegt welke bestanden het niet herkent.
- **Niet herkend** (bijvoorbeeld een Access-bestand): stel EEN vraag met de knoppen
  "Ik exporteer het opnieuw als CSV of Excel" (aanbevolen, wijs op `EXPORT.md`),
  "Sla dit bestand over" en, ALLEEN bij testdata, "Kijk zelf in het bestand".
- **Schermafdruk of PDF:** die kan het script niet lezen. Bij testdata bekijk je hem zelf.
  Bij de veilige route vraag je eerst: "Deze schermafdruk kan alleen ik lezen. Mag dat?"
  Bij nee sla je hem over.

Is `mijn-data/` leeg, stel dan EEN vraag: "Waar staat je testdata?" Knoppen:
- **Ik zet nu een export in mijn-data/** (aanbevolen; zeg dat elke vorm goed is: Excel,
  CSV, JSON, XML, een database-dump, een schermafdruk of zelfs een enkele rij). Wacht
  daarna tot de gebruiker "klaar" zegt en kijk opnieuw.
- **Een testdatabase** (vraag welk type en hoe je erbij komt; alleen-lezen is genoeg).
- **Een API van de testomgeving** (vraag de documentatie of een voorbeeldantwoord).
- **Nog niets, ik oefen eerst** (gebruik `data/epd.sqlite`).
Vraag daarna alsnog de testdata-bevestiging hierboven.

Lezen van de data, wat de vorm ook is:
- Excel: openpyxl, installeer het zelf als het ontbreekt (`python3 -m pip install openpyxl`);
  formules lees je als opgeslagen uitkomst (`data_only=True`).
- Een schermafdruk of foto: bekijk de afbeelding en lees de kolommen en waarden eruit.
  Zeg erbij dat een echt exportbestand straks nodig is om het script te kunnen draaien.
- Een SQL-dump (`.sql`): lees de CREATE TABLE- en INSERT-regels; laad hem desnoods in
  SQLite om hem te doorzoeken.
- Een enkele rij of een klein voorbeeld: genoeg om de mapping te maken. Meld dat de
  velden die je niet gezien hebt in de mapping als open punt staan.
- Weet je niet hoe de gebruiker een export moet maken? Kijk in `EXPORT.md`: daar staat
  per systeem hoe dat gaat.

## Stap 2. Verkennen (geen vraag)

Lees `mijn-koppeling/overzicht.md` (bij de veilige route ALLEEN dat; bij testdata mag je
de bestanden erbij pakken). Laat daarna in gewone taal zien wat je vond: welke tabellen of
velden er zijn en welke over de patient, problemen, allergieen, medicatie, verrichtingen
en hulpmiddelen gaan. Noem opvallende dingen (datumnotatie, eigen codes, lege velden).
Stel hier GEEN vraag; onduidelijkheden neem je mee naar de mapping.

## Stap 3. De mapping maken (klik 2 en 3)

1. Pak de specificatie uit (`tar -xzf specs/hl7.fhir.eu.eps.tgz -C specs/`) en lees de
   kernprofielen uit `specs/README.md`. Kijk ook naar de verplichte onderdelen in de
   snapshot en naar de voorbeelden in `specs/package/example/`.
2. Schrijf `mijn-koppeling/mapping.md`: per veld uit de data het FHIR-pad en de regel voor
   de omzetting. Neem redelijke keuzes zelf en zet ze onder "Besluiten" (met reden). Wat
   echt vakkennis vraagt komt onder "Open vragen".
3. **Klik 2.** Laat de mapping zien als tabel en vraag: "Klopt dit met hoe jullie systeem
   werkt?" Knoppen: "Ja" (aanbevolen), "Ik wil iets aanpassen", "Weet ik niet, laat het staan".
4. **Klik 3.** Leg ALLE open vragen in EEN keer voor, in een scherm, met per vraag je
   aanbeveling en de optie "Laat staan voor Nictiz". Niet een voor een.

Let op bij de mapping:
- De vijf verplichte secties zijn Problemen, Allergieen, Medicatie, Verrichtingen en
  Hulpmiddelen. Heeft de data ergens niets voor, dan komt de sectie er toch in, met een
  `emptyReason`. Legt de export zelf een reden vast, neem die over. Staat er niets,
  gebruik dan `unavailable` (niet vastgelegd in het dossier); `nilknown` betekent dat een
  arts heeft vastgesteld dat er niets is, en dat weet een systeem zelf niet.
- Heeft de export geen tabel voor een verplicht onderdeel (bijvoorbeeld medicatie of
  verrichtingen), dan komt dat onderdeel er toch in, leeg, met een `emptyReason`.
- Extra gegevens zoals metingen en labuitslagen: neem ze mee in de optionele secties voor
  vitale functies (LOINC 8716-3) en uitslagen (LOINC 30954-2). Geen aparte vraag.
- Datum-tijden zonder tijdzone: lees ze als Nederlandse tijd (Europe/Amsterdam) en zet die
  keuze onder Besluiten.
- Zet geen `language` op het document of de onderdelen, tenzij je bij elke code de
  Nederlandse naam gebruikt. Met `language` = nl eist de keuring Nederlandse namen bij
  alle LOINC- en SNOMED-codes. Zonder `language` gebruik je de officiele Engelse namen.
- De Patient Summary werkt het liefst met SNOMED CT. Heeft het systeem andere codes
  (ICPC, ICD-10, ATC), neem die over en zet een vertaling naar SNOMED alleen erbij als
  die onderbouwd is. De rest wordt een open vraag.

## Stap 4. Het script bouwen (geen vraag)

Schrijf `mijn-koppeling/converter.py` volgens de mapping. Zonder argumenten leest hij
ALLES uit `mijn-data/` en schrijft hij een dossier per patient in `output/`, zodat
`python3 mijn-koppeling/converter.py` altijd de hele omzetting doet (ook na een nieuwe
export). Codevertalingen in een aparte tabel (`mijn-koppeling/vertaling.py`). Vaste id's, zodat dezelfde invoer altijd dezelfde
uitvoer geeft. Het documenttijdstip is standaard "nu"; geef een optie `--datum` zodat een
run exact te herhalen is (ook voor de tests). Uitvoer: `output/patient-<nummer>.json`.

Schrijf tests in `mijn-koppeling/tests/` en draai ze. Vertel hoeveel er groen zijn.

## Stap 5. Keuren en verbeteren (geen vraag)

1. Draai `python3 tools/valideer.py --alles` (duurt ongeveer 30 seconden). Onderaan staat
   een samenvatting per soort melding; begin daar, niet bij de losse regels.
2. Extra keuring van Interoplab (optioneel). In `.mcp.json` staat hun validator als
   MCP-server. Staat er een tool die begint met `mcp__interoplab` in je toollijst, laat
   dan ook een bundel door hun validator keuren. Staat die er niet, sla dit over zonder
   te zoeken: de middag hangt er niet van af.
3. Per fout: zoek de regel in de spec, pas EERST de mapping aan, dan de code, en voeg een
   test toe die de fout had moeten vangen.
4. Herhaal, maximaal vijf rondes. Vertel na elke ronde kort: van hoeveel fouten naar hoeveel.
5. Ook als de eerste ronde al 0 fouten geeft: loop de adviezen over codelijsten na.
   Die zeggen welke codes de spec liever ziet. Vraagt een advies om een code die je niet
   kunt onderbouwen (regel 4), dan wordt dat een open vraag; ga er niet naar zoeken.
6. Zet onderaan `mijn-koppeling/mapping.md` een kopje "Keuring": welke waarschuwingen
   blijven over en waarom, en welke open vragen erbij kwamen. Een deel van de
   waarschuwingen komt uit de spec zelf (Europese codelijsten die niet te laden zijn,
   Nederlandse codelijsten die de internationale validator niet kent). Fouten moeten weg;
   waarschuwingen moet je kunnen uitleggen. Nieuwe open vragen leg je NIET opnieuw voor
   (dat zou een vijfde klik zijn); ze staan in de mapping en komen terug in stap 7.

## Stap 6. Vastleggen (geen vraag)

Leg de werkwijze vast zodat de gebruiker hem later met een opdracht opnieuw draait:
- Claude Code: `.claude/skills/patient-summary/SKILL.md` (draaien, keuren, fout oplossen,
  wat te doen bij een nieuwe versie van de spec). Zet erin dat `specs/package/` eerst
  uitgepakt moet worden als die map ontbreekt (hij staat in `.gitignore`).
- Andere assistenten: `mijn-koppeling/DRAAIEN.md` met dezelfde stappen.

## Stap 7. Afronden (klik 4)

Geef een korte samenvatting: wat er nu staat, hoeveel dossiers goedgekeurd, welke open
vragen er nog liggen voor iemand van Nictiz, en hoe de gebruiker het opnieuw draait:
nieuwe export in `mijn-data/`, dan `python3 mijn-koppeling/converter.py` in de terminal
(de omzetting zelf, zonder AI) of `/patient-summary` in Claude Code (omzetten plus keuren). Sluit af met EEN vraag: "Wil je een van de dossiers bekijken?"
Knoppen: "Ja, laat er een zien" (aanbevolen) en "Nee, klaar". Bij de veilige route laat je
het dossier niet zelf zien: zeg welk bestand de gebruiker kan openen in `output/`.
