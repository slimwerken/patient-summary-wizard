# Patient Summary-wizard

Zet patientgegevens uit je eigen systeem om naar de **HL7 Europe Patient Summary**
(FHIR R4). Je AI-assistent loodst je er stap voor stap doorheen. Jij kiest en
controleert, de assistent doet het technische werk. Aan het eind heb je een gewoon
Python-script in je eigen map, goedgekeurd door de officiele HL7-validator.

Gemaakt voor de AI mini-plugathon van Nictiz op 23 september 2026.

## Starten

**Met Claude Code (aanbevolen)**
1. Download deze map (groene knop *Code* > *Download ZIP*) en pak hem uit.
2. Open de map in VS Code en open Claude Code.
3. Typ `/start`.

**Met Codex of een andere codeer-assistent**
1. Open de map in je assistent.
2. Typ: *Volg WIZARD.md*.

De assistent moet opdrachten op je eigen laptop kunnen uitvoeren. Een gewoon chatvenster
in de browser is daarom niet genoeg.

## Wat je nodig hebt

- Python 3.9 of nieuwer
- Java 17 of nieuwer, voor de keuring (de wizard installeert hem als het kan)
- Een abonnement op je AI-assistent (bij Claude is Pro genoeg)
- Testdata van je eigen systeem, of de oefen-database die hier al in zit

## Spelregels

- **Alleen testdata.** Nooit echte patientgegevens.
- Alles blijft op je eigen laptop.
- Eerst de mapping (welk veld gaat waarheen), dan pas code.
- De assistent raadt nooit een medische code. Wat hij niet weet, meldt hij.

## Wat erin zit

| Map of bestand | Wat |
|---|---|
| `WIZARD.md` | De stappen die de assistent met je doorloopt |
| `STAPPEN.md` | Dezelfde route, maar dan zelf de opdrachten intypen |
| `data/epd.sqlite` | Oefen-database van een verzonnen huisartsenpraktijk (vijf verzonnen patienten) |
| `specs/` | De specificatie van de HL7 Europe Patient Summary (versie van 11 september 2026) |
| `tools/valideer.py` | De keuring met de officiele HL7-validator |
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
