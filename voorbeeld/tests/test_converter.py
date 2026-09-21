"""Tests voor de koppeling EPD -> Patient Summary.

Draaien: python3 -m unittest discover voorbeeld/tests -v

Deze tests controleren ONZE regels (datums, geslacht, secties, verwijzingen).
Of het resultaat aan de Europese profielen voldoet, beoordeelt de validator
(tools/valideer.py). Allebei nodig: de tests komen uit dezelfde lezing van de
spec als de code, de validator niet.
"""
import json
import sqlite3
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "voorbeeld"))

import converter  # noqa: E402

TIJDSTIP = "2026-09-23T13:00:00+02:00"
VERPLICHTE_SECTIES = {"11450-4", "48765-2", "10160-0", "47519-4", "46264-8"}


def bundel_voor(pat_id):
    conn = sqlite3.connect(PROJECT / "data" / "epd.sqlite")
    conn.row_factory = sqlite3.Row
    try:
        return converter.maak_patient_summary(converter.lees_patient(conn, pat_id), TIJDSTIP)
    finally:
        conn.close()


def resources(bundel, soort):
    return [e["resource"] for e in bundel["entry"] if e["resource"]["resourceType"] == soort]


def secties(bundel):
    return {s["code"]["coding"][0]["code"]: s for s in bundel["entry"][0]["resource"]["section"]}


class TestHulpjes(unittest.TestCase):
    def test_datum_van_nederlands_naar_fhir(self):
        self.assertEqual(converter.fhir_datum("14-03-1952"), "1952-03-14")

    def test_lege_datum_blijft_leeg(self):
        self.assertIsNone(converter.fhir_datum(None))
        self.assertIsNone(converter.fhir_datum(""))
        self.assertIsNone(converter.fhir_datum("   "))

    def test_ids_zijn_vast(self):
        self.assertEqual(converter.vaste_id("patient", 1001), converter.vaste_id("patient", 1001))
        self.assertNotEqual(converter.vaste_id("patient", 1001), converter.vaste_id("patient", 1002))


class TestBundelVorm(unittest.TestCase):
    def test_elke_patient_geeft_een_documentbundel(self):
        for pat_id in (1001, 1002, 1003, 1004, 1005):
            bundel, _ = bundel_voor(pat_id)
            self.assertEqual(bundel["type"], "document")
            self.assertEqual(bundel["entry"][0]["resource"]["resourceType"], "Composition")
            self.assertEqual(len(resources(bundel, "Patient")), 1)
            self.assertIn("identifier", bundel)
            self.assertIn("identifier", bundel["entry"][0]["resource"])

    def test_vijf_verplichte_secties_altijd_aanwezig(self):
        for pat_id in (1001, 1005):
            bundel, _ = bundel_voor(pat_id)
            self.assertTrue(VERPLICHTE_SECTIES.issubset(secties(bundel).keys()))

    def test_lege_sectie_zegt_waarom_hij_leeg_is(self):
        bundel, _ = bundel_voor(1005)
        for code, sectie in secties(bundel).items():
            self.assertNotIn("entry", sectie)
            self.assertEqual(sectie["emptyReason"]["coding"][0]["code"], "nilknown")

    def test_alle_verwijzingen_bestaan_in_de_bundel(self):
        for pat_id in (1001, 1004):
            bundel, _ = bundel_voor(pat_id)
            adressen = {e["fullUrl"] for e in bundel["entry"]}
            tekst = json.dumps(bundel)
            for ref in {deel.split('"')[0] for deel in tekst.split('"reference": "')[1:]}:
                self.assertIn(ref, adressen, f"verwijzing {ref} wijst nergens naar")

    def test_zelfde_invoer_geeft_zelfde_uitvoer(self):
        self.assertEqual(bundel_voor(1004)[0], bundel_voor(1004)[0])

    def test_elke_resource_heeft_een_leesbare_samenvatting(self):
        bundel, _ = bundel_voor(1004)
        for entry in bundel["entry"]:
            self.assertIn("text", entry["resource"], entry["resource"]["resourceType"])


class TestMapping(unittest.TestCase):
    def test_patient(self):
        bundel, _ = bundel_voor(1001)
        p = resources(bundel, "Patient")[0]
        self.assertEqual(p["gender"], "female")
        self.assertEqual(p["birthDate"], "1952-03-14")
        self.assertEqual(p["name"][0]["family"], "de Boer")
        self.assertEqual(p["identifier"][0]["value"], "1001")

    def test_leeg_geslacht_wordt_unknown(self):
        bundel, _ = bundel_voor(1005)
        self.assertEqual(resources(bundel, "Patient")[0]["gender"], "unknown")

    def test_afgesloten_episode_is_resolved_met_einddatum(self):
        bundel, _ = bundel_voor(1001)
        rug = [c for c in resources(bundel, "Condition") if c["code"]["text"].startswith("Lage rug")][0]
        self.assertEqual(rug["clinicalStatus"]["coding"][0]["code"], "resolved")
        self.assertEqual(rug["abatementDateTime"], "2019-03-20")

    def test_icpc_zonder_vertaling_wordt_gemeld_niet_geraden(self):
        bundel, gaten = bundel_voor(1001)
        rug = [c for c in resources(bundel, "Condition") if c["code"]["text"].startswith("Lage rug")][0]
        systemen = {c["system"] for c in rug["code"]["coding"]}
        self.assertNotIn("http://snomed.info/sct", systemen)
        self.assertTrue(any("L03" in g for g in gaten))

    def test_icpc_met_vertaling_krijgt_snomed_en_icpc(self):
        bundel, _ = bundel_voor(1001)
        dm = [c for c in resources(bundel, "Condition") if c["code"]["text"].startswith("Diabetes")][0]
        codes = {(c["system"], c["code"]) for c in dm["code"]["coding"]}
        self.assertIn(("http://snomed.info/sct", "44054006"), codes)
        self.assertIn(("http://hl7.org/fhir/sid/icpc-1-nl", "T90"), codes)

    def test_lege_stopdatum_betekent_nog_in_gebruik(self):
        bundel, _ = bundel_voor(1001)
        lisinopril = [m for m in resources(bundel, "MedicationStatement")
                      if m["medicationCodeableConcept"]["coding"][0]["code"] == "C09AA03"][0]
        self.assertEqual(lisinopril["status"], "active")
        self.assertNotIn("end", lisinopril["effectivePeriod"])

    def test_gestopte_medicatie_is_completed(self):
        bundel, _ = bundel_voor(1004)
        paracetamol = [m for m in resources(bundel, "MedicationStatement")
                       if m["medicationCodeableConcept"]["coding"][0]["code"] == "N02BE01"][0]
        self.assertEqual(paracetamol["status"], "completed")
        self.assertEqual(paracetamol["effectivePeriod"]["end"], "2022-03-15")

    def test_ernstige_allergie_is_high(self):
        bundel, _ = bundel_voor(1003)
        pinda = resources(bundel, "AllergyIntolerance")[0]
        self.assertEqual(pinda["criticality"], "high")
        self.assertEqual(pinda["category"], ["food"])

    def test_hulpmiddel_geeft_apparaat_en_gebruik(self):
        bundel, _ = bundel_voor(1004)
        self.assertEqual(len(resources(bundel, "Device")), 1)
        self.assertEqual(len(resources(bundel, "DeviceUseStatement")), 1)


if __name__ == "__main__":
    unittest.main()
