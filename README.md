# Patient Summary-wizard

Zet patientgegevens uit je eigen systeem om naar de **HL7 Europe Patient Summary**
(FHIR R4). Je AI-assistent loodst je er stap voor stap doorheen. Jij kiest en
controleert, de assistent doet het technische werk. Aan het eind heb je een gewoon
Python-script in je eigen map, goedgekeurd door de officiele HL7-validator.

Gemaakt voor de AI mini-plugathon van Nictiz op 23 september 2026.

## Starten

**Met Claude Code (aanbevolen)**
1. Download deze map (groene knop *Code* > *Download ZIP*) en pak hem uit.
2. Zet een export van je testdata in de map `mijn-data/` (zie `EXPORT.md`).
3. Open de map in VS Code en open Claude Code.
4. Typ `/start`. Daarna klik je nog vier keer; de rest doet de wizard.

**Met Codex of een andere codeer-assistent**
1. Open de map in je assistent.
2. Typ: *Volg WIZARD.md*.

De assistent moet opdrachten op je eigen laptop kunnen uitvoeren. Een gewoon chatvenster
in de browser is daarom niet genoeg.

## Vooraf, thuis (5 minuten)

Open de map en typ in de terminal: `python3 tools/valideer.py --controleer`. Dat zet de
keuring klaar en haalt de benodigde bestanden op (ongeveer 200 MB), zodat het op de dag zelf
niet op de wifi hoeft te wachten. Of vraag je assistent: *Zet de keuring klaar.*

## Wat je nodig hebt

- Python 3.9 of nieuwer
- Java 17 of nieuwer, voor de keuring (de wizard installeert hem als het kan)
- Een abonnement op je AI-assistent (bij Claude is Pro genoeg)
- Een export van je testdata in `mijn-data/` (Excel, CSV, dump, schermafdruk: alles is goed, zie `EXPORT.md`), of de oefen-database die hier al in zit

## Spelregels

- **Alleen testdata.** Nooit echte patientgegevens.
- Alles blijft op je eigen laptop. Geen testdata of twijfel? Dan leest de assistent je
  bestanden niet: een script op je eigen computer maakt een overzicht zonder namen,
  adressen en nummers, en alleen dat ziet de AI.
- Eerst de mapping (welk veld gaat waarheen), dan pas code.
- De assistent raadt nooit een medische code. Wat hij niet weet, meldt hij.

## Wat erin zit

| Map of bestand | Wat |
|---|---|
| `WIZARD.md` | De stappen die de assistent met je doorloopt |
| `EXPORT.md` | Hoe je per systeem een export van je testdata maakt |
| `STAPPEN.md` | Dezelfde route, maar dan zelf de opdrachten intypen |
| `barts-dummy-data/` | De CSV-export uit de live demo: kopieer hem naar `mijn-data/` en typ `/start` |
| `data/epd.sqlite` | Oefen-database van een verzonnen huisartsenpraktijk (vijf verzonnen patienten) |
| `specs/` | De specificatie van de HL7 Europe Patient Summary (versie van 11 september 2026) |
| `tools/valideer.py` | De keuring met de officiele HL7-validator |
| `tools/bekijk.py` | Maakt van elk dossier een leesbare pagina, zoals een arts hem ziet |
| `voorbeeld/` | Een complete, goedgekeurde koppeling voor de oefen-database |
| `mijn-koppeling/` | Hier komt jouw werk |

## Na vandaag

Komt er een nieuwe versie van de specificatie? Zet hem in `specs/` en zeg tegen je
assistent: *De spec is veranderd. Wat raakt dit in mijn mapping en code?* Je krijgt eerst
een lijstje, pas daarna aanpassingen.

---

Specificatie: [HL7 Europe Patient Summary](https://build.fhir.org/ig/hl7-eu/eps/index.html)
(HL7 Europe, CC0). Validator: [HL7 FHIR Validator](https://github.com/hapifhir/org.hl7.fhir.core).
Wizard en voorbeeld: Bart Boonstra, Slim Werken AI.
