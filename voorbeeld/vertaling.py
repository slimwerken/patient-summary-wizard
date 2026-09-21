"""Vertaaltabellen van de eigen EPD-codes naar internationale codes.

Dit is het deel van de koppeling waar je het meest moet opletten. Een AI kan
een SNOMED-code verzinnen die er echt uitziet. Daarom geldt hier: elke code is
gecontroleerd tegen de terminologieserver (tx.fhir.org), en een code die niet
in deze tabel staat wordt NIET geraden. De converter meldt hem dan als gat.
"""

SNOMED = "http://snomed.info/sct"
ICPC = "http://hl7.org/fhir/sid/icpc-1-nl"
ATC = "http://www.whocc.no/atc"

# ICPC-1 (probleemlijst huisarts) naar SNOMED CT
ICPC_NAAR_SNOMED = {
    "T90": ("44054006", "Diabetes mellitus type 2"),
    "K86": ("38341003", "Hypertensive disorder, systemic arterial (disorder)"),
    "R96": ("195967001", "Asthma"),
    "K78": ("49436004", "Atrial fibrillation"),
    "K77": ("84114007", "Heart failure"),
    "T93": ("13644009", "Hypercholesterolemia"),
    # L03 (lage rugklachten) staat er bewust niet in: die vertaling is nog
    # niet door een inhoudsdeskundige vastgesteld.
}

# Allergieen staan in het EPD als vrije tekst
ALLERGIE_NAAR_SNOMED = {
    "penicilline": ("764146007", "Penicillin"),
    "huisstofmijt": ("260147004", "House dust mite"),
    "pinda": ("762952008", "Peanut"),
}

ALLERGIE_CATEGORIE = {
    "medicijn": "medication",
    "voedsel": "food",
    "omgeving": "environment",
}

# ernst in het EPD -> criticality in FHIR (het risico op een zware reactie)
ALLERGIE_ERNST = {
    "licht": "low",
    "matig": "low",
    "ernstig": "high",
}

VERRICHTING_NAAR_SNOMED = {
    "staaroperatie": ("110473004", "Cataract surgery"),
    "blindedarmoperatie": ("80146002", "Excision of appendix"),
    "plaatsing pacemaker": ("307280005", "Implantation of cardiac pacemaker"),
}

HULPMIDDEL_NAAR_SNOMED = {
    "pacemaker": ("14106009", "Cardiac pacemaker"),
}

# De officiele (Engelse) ATC-namen, voor de display naast de code
ATC_NAMEN = {
    "A10BA02": "metformin",
    "C09AA03": "lisinopril",
    "R03AC02": "salbutamol",
    "B01AF02": "apixaban",
    "C07AB02": "metoprolol",
    "C10AA01": "simvastatin",
    "N02BE01": "paracetamol",
}

GESLACHT = {
    "M": "male",
    "V": "female",
    "O": "other",
}
