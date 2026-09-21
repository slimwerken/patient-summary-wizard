# Specificaties

## De bron van waarheid

**HL7 Europe Patient Summary** (`hl7.fhir.eu.eps`), FHIR R4 (4.0.1).

- Online: https://build.fhir.org/ig/hl7-eu/eps/index.html
- Hier opgeslagen: `hl7.fhir.eu.eps.tgz` (versie 1.0.0-ci-build, gebouwd 11 september 2026).
  Uitpakken: `tar -xzf hl7.fhir.eu.eps.tgz` geeft een map `package/` met alle profielen
  (`StructureDefinition-*.json`) en voorbeelden (`package/example/`).

De kernprofielen:

| Profiel | Bestand in package/ |
|---|---|
| Bundle (het document) | `StructureDefinition-bundle-eu-eps.json` |
| Composition (inhoudsopgave + secties) | `StructureDefinition-composition-eu-eps.json` |
| Patient | `StructureDefinition-patient-eu-eps.json` |
| Problemen | `StructureDefinition-condition-obl-eu-eps.json` |
| Allergieen | `StructureDefinition-allergyintolerance-obl-eu-eps.json` |
| Medicatie | `StructureDefinition-medicationStatement-eu-eps.json` |
| Verrichtingen | `StructureDefinition-procedure-eu-eps.json` |
| Hulpmiddelen | `StructureDefinition-deviceUseStatement-eu-eps.json`, `StructureDefinition-device-eu-eps.json` |

## Achtergrond

- Xt-EHR logisch model Patient Summary: https://www.xt-ehr.eu/fhir/models/en/overview-patientsummary.html
- Xt-EHR deliverable D6.1 (implementatiegidsen en eisen voor EPD-systemen), meegestuurd door Nictiz.

## Let op

Dit is een CI-build: de online versie verandert. Werk tegen het opgeslagen pakket, zodat
een resultaat van vandaag over een maand nog hetzelfde is. Wil je een nieuwere versie,
download dan `https://build.fhir.org/ig/hl7-eu/eps/package.tgz`, vergelijk en pas bewust aan.
