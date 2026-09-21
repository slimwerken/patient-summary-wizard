# Mapping: eigen EPD naar HL7 Europe Patient Summary

Bron: `data/epd.sqlite` (Huisartsenpraktijk Noorderhaven, alle gegevens verzonnen).
Doel: FHIR R4 document-bundel volgens `hl7.fhir.eu.eps` 1.0.0-ci-build (`specs/`).
Uitvoering: `voorbeeld/converter.py` volgt deze tabel regel voor regel.

Deze tabel is het document dat je laat controleren door iemand die de spec kent.
De code is daarna alleen nog de uitvoering ervan.

## Document

| Wat | FHIR | Waarde |
|---|---|---|
| Bundel | `Bundle.type` | `document`, met `identifier` (urn:ietf:rfc:9562) en `timestamp` |
| Soort document | `Composition.type` | LOINC 60591-5 Patient summary Document |
| Documentnummer | `Composition.identifier` | vaste UUID per patient en tijdstip (verplicht in EPS) |
| Opgesteld door | `Composition.author` | de huisarts van de patient (`patienten.arts_id`) |
| Beheerder | `Composition.custodian` | de praktijk (`praktijk`) |
| Verplichte secties | `Composition.section` | Problemen, Allergieen, Medicatie, Verrichtingen, Hulpmiddelen. Leeg = `emptyReason` unavailable (niet vastgelegd in het dossier) |

## Patient (`patienten`)

| EPD-kolom | FHIR-pad | Regel |
|---|---|---|
| `pat_id` | `Patient.identifier` | systeem `https://epd.noorderhaven.example/patientnummer`. Geen BSN in de oefening |
| `voornaam` | `Patient.name.given` | |
| `tussenvoegsel` + `achternaam` | `Patient.name.family` | "de Boer", voorvoegsel apart in extensie `humanname-own-prefix` |
| `geslacht` | `Patient.gender` | M -> male, V -> female, O -> other, leeg -> unknown |
| `geboortedatum` | `Patient.birthDate` | DD-MM-JJJJ -> JJJJ-MM-DD |
| `straat` + `huisnummer`, `postcode`, `woonplaats` | `Patient.address` | land NL |
| `telefoon` | `Patient.telecom` | alleen als ingevuld |
| `arts_id` | `Patient.generalPractitioner` | verwijzing naar de huisarts |

## Problemen (`episodes`) -> Condition

| EPD-kolom | FHIR-pad | Regel |
|---|---|---|
| `icpc` | `Condition.code.coding` | ICPC-1 (`http://hl7.org/fhir/sid/icpc-1-nl`) plus SNOMED CT uit `vertaling.py`. Geen vertaling = alleen ICPC, en de converter meldt het |
| `omschrijving` | `Condition.code.text` | |
| `actief` / `einddatum` | `Condition.clinicalStatus` | J zonder einddatum -> active, anders resolved |
| `begindatum` | `Condition.onsetDateTime` | |
| `einddatum` | `Condition.abatementDateTime` | |
| | `Condition.category` | problem-list-item |

## Allergieen (`allergieen`) -> AllergyIntolerance

| EPD-kolom | FHIR-pad | Regel |
|---|---|---|
| `stof` | `AllergyIntolerance.code` | vrije tekst -> SNOMED-stof uit `vertaling.py`, tekst blijft erbij |
| `categorie` | `AllergyIntolerance.category` | medicijn -> medication, voedsel -> food, omgeving -> environment |
| `ernst` | `AllergyIntolerance.criticality` | ernstig -> high, licht en matig -> low |
| `vastgelegd` | `AllergyIntolerance.recordedDate` | |

## Medicatie (`medicatie`) -> MedicationStatement

| EPD-kolom | FHIR-pad | Regel |
|---|---|---|
| `atc` | `medicationCodeableConcept.coding` | ATC (`http://www.whocc.no/atc`) met de officiele naam |
| `middel` | `medicationCodeableConcept.text` | |
| `gebruik` | `dosage.text` | |
| `startdatum` / `stopdatum` | `effectivePeriod` | lege stopdatum (NULL of "") = nog in gebruik |
| | `status` | stopdatum ingevuld -> completed, anders active |

## Verrichtingen (`verrichtingen`) -> Procedure

| EPD-kolom | FHIR-pad | Regel |
|---|---|---|
| `omschrijving` | `Procedure.code` | SNOMED uit `vertaling.py`, tekst blijft erbij |
| `datum` | `Procedure.performedDateTime` | |
| | `Procedure.status` | completed |

## Hulpmiddelen (`hulpmiddelen`) -> DeviceUseStatement + Device

| EPD-kolom | FHIR-pad | Regel |
|---|---|---|
| `omschrijving` | `Device.type` | SNOMED uit `vertaling.py` |
| `sinds` | `DeviceUseStatement.timingPeriod.start` | |

## Open vragen voor een inhoudsdeskundige

1. ICPC L03 (lage rugklachten) heeft nog geen vastgestelde SNOMED-vertaling. Welke?
2. Een lege sectie krijgt nu `unavailable` (niet vastgelegd in het dossier). Mag het `nilknown` zijn als de huisarts bewust "niets bekend" heeft vastgelegd?
3. EPD-ernst "matig" gaat nu naar criticality `low`. Klopt dat, of hoort daar `unable-to-assess`?
4. De validator kent de Nederlandse ICPC-codelijst niet en geeft daar een waarschuwing op. Is een SNOMED-vertaling ernaast genoeg?
