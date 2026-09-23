# Patient Summary-wizard

Dit project zet testdata uit het eigen systeem van een zorgsoftwareleverancier om naar de
HL7 Europe Patient Summary (FHIR R4).

**Begint de gebruiker, of weet hij niet waar te beginnen? Volg dan `WIZARD.md`** (in Claude Code ook via `/start`; in andere assistenten typt de gebruiker: Volg WIZARD.md).

De harde regels staan in `WIZARD.md`. In het kort: alleen testdata, alles blijft op deze
computer, eerst de mapping en dan de code, nooit een code raden, geen AI in het
eindresultaat, en de officiele validator (`tools/valideer.py`) beslist over de vorm; of de inhoud klopt, controleert de gebruiker in de mapping.

- Werk van de gebruiker: `mijn-koppeling/`. Uitvoer: `output/`.
- Patroon om van te leren: `voorbeeld/` (goedgekeurde koppeling voor `data/epd.sqlite`).
- Specificatie: `specs/` (zie `specs/README.md`).
