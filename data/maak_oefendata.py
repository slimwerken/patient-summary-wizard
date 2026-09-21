#!/usr/bin/env python3
"""Bouwt de oefen-database van een verzonnen huisartsenpraktijk (data/epd.sqlite).

Alles hierin is verzonnen: praktijk, huisartsen, patienten, adressen. Geen BSN,
geen echte identificatie. De structuur is bewust NIET FHIR-achtig: Nederlandse
kolomnamen, datums als tekst in DD-MM-JJJJ, geslacht als M/V/O, ICPC-codes op
de probleemlijst en allergieen als vrije tekst. Precies het soort eigen
database waar een leverancier een koppeling voor moet bouwen.

Er zitten ook drie kleine vuiltjes in, zoals in elke echte database:
- patient 1005 heeft een leeg geslacht (lege string, geen NULL)
- een stopdatum die leeg is in plaats van NULL (medicatie 2)
- ICPC L03 (lage rugklachten) staat niet in de vertaaltabel naar SNOMED

Gebruik: python3 maak_epd.py <pad-naar-epd.sqlite>
"""
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE praktijk (
    praktijk_id   INTEGER PRIMARY KEY,
    naam          TEXT NOT NULL,
    straat        TEXT,
    postcode      TEXT,
    plaats        TEXT,
    telefoon      TEXT
);

CREATE TABLE huisartsen (
    arts_id       INTEGER PRIMARY KEY,
    praktijk_id   INTEGER NOT NULL REFERENCES praktijk(praktijk_id),
    voorletters   TEXT,
    tussenvoegsel TEXT,
    achternaam    TEXT NOT NULL
);

CREATE TABLE patienten (
    pat_id        INTEGER PRIMARY KEY,
    voornaam      TEXT,
    tussenvoegsel TEXT,
    achternaam    TEXT NOT NULL,
    geslacht      TEXT,          -- 'M', 'V', 'O' of leeg
    geboortedatum TEXT,          -- DD-MM-JJJJ
    straat        TEXT,
    huisnummer    TEXT,
    postcode      TEXT,
    woonplaats    TEXT,
    telefoon      TEXT,
    arts_id       INTEGER REFERENCES huisartsen(arts_id)
);

-- Probleemlijst van de huisarts, gecodeerd met ICPC-1
CREATE TABLE episodes (
    ep_id         INTEGER PRIMARY KEY,
    pat_id        INTEGER NOT NULL REFERENCES patienten(pat_id),
    icpc          TEXT NOT NULL,
    omschrijving  TEXT NOT NULL,
    begindatum    TEXT,          -- DD-MM-JJJJ
    einddatum     TEXT,          -- DD-MM-JJJJ of NULL
    actief        TEXT           -- 'J' of 'N'
);

-- Medicatie met ATC-code
CREATE TABLE medicatie (
    med_id        INTEGER PRIMARY KEY,
    pat_id        INTEGER NOT NULL REFERENCES patienten(pat_id),
    atc           TEXT NOT NULL,
    middel        TEXT NOT NULL,
    gebruik       TEXT,          -- gebruiksvoorschrift als tekst
    startdatum    TEXT,          -- DD-MM-JJJJ
    stopdatum     TEXT           -- DD-MM-JJJJ, NULL of leeg
);

-- Allergieen als vrije tekst, zoals in veel systemen
CREATE TABLE allergieen (
    allergie_id   INTEGER PRIMARY KEY,
    pat_id        INTEGER NOT NULL REFERENCES patienten(pat_id),
    stof          TEXT NOT NULL,
    categorie     TEXT,          -- 'medicijn', 'voedsel', 'omgeving'
    ernst         TEXT,          -- 'licht', 'matig', 'ernstig'
    vastgelegd    TEXT           -- DD-MM-JJJJ
);

CREATE TABLE verrichtingen (
    verrichting_id INTEGER PRIMARY KEY,
    pat_id         INTEGER NOT NULL REFERENCES patienten(pat_id),
    omschrijving   TEXT NOT NULL,
    datum          TEXT          -- DD-MM-JJJJ
);

CREATE TABLE hulpmiddelen (
    hulpmiddel_id  INTEGER PRIMARY KEY,
    pat_id         INTEGER NOT NULL REFERENCES patienten(pat_id),
    omschrijving   TEXT NOT NULL,
    sinds          TEXT          -- DD-MM-JJJJ
);
"""

PRAKTIJK = [
    (1, "Huisartsenpraktijk Noorderhaven", "Havenkade 4", "2511 AA", "Den Haag", "070 000 0000"),
]

HUISARTSEN = [
    (11, 1, "M.", None, "Verbeek"),
    (12, 1, "J.", "van", "Leeuwen"),
]

PATIENTEN = [
    (1001, "Anna", "de", "Boer", "V", "14-03-1952", "Duinstraat", "12", "2584 AB", "Den Haag", "06 0000 0001", 11),
    (1002, "Pieter", None, "Jansen", "M", "02-11-1978", "Laan van Meerdervoort", "210", "2563 AL", "Den Haag", "06 0000 0002", 11),
    (1003, "Fatima", "el", "Amrani", "V", "30-04-1990", "Weimarstraat", "88", "2562 GV", "Den Haag", "06 0000 0003", 12),
    (1004, "Kees", "van", "Dijk", "M", "21-07-1945", "Sportlaan", "7", "2566 LA", "Den Haag", "070 000 0004", 12),
    (1005, "Sam", None, "Visser", "", "09-01-2001", "Prinsegracht", "31", "2512 EW", "Den Haag", None, 12),
]

EPISODES = [
    (1, 1001, "T90", "Diabetes mellitus type 2", "02-05-2011", None, "J"),
    (2, 1001, "K86", "Hypertensie zonder orgaanbeschadiging", "17-09-2014", None, "J"),
    (3, 1001, "L03", "Lage rugklachten zonder uitstraling", "08-01-2019", "20-03-2019", "N"),
    (4, 1002, "R96", "Astma", "01-06-1985", None, "J"),
    (5, 1004, "K78", "Atriumfibrilleren", "11-11-2016", None, "J"),
    (6, 1004, "K77", "Hartfalen", "23-02-2020", None, "J"),
    (7, 1004, "T93", "Hypercholesterolemie", "05-05-2009", None, "J"),
]

MEDICATIE = [
    (1, 1001, "A10BA02", "Metformine 500 mg tablet", "2x per dag 1 tablet", "02-05-2011", None),
    (2, 1001, "C09AA03", "Lisinopril 10 mg tablet", "1x per dag 1 tablet", "17-09-2014", ""),
    (3, 1002, "R03AC02", "Salbutamol 100 microgram/dosis aerosol", "zo nodig 1 tot 2 inhalaties", "01-06-1985", None),
    (4, 1004, "B01AF02", "Apixaban 5 mg tablet", "2x per dag 1 tablet", "11-11-2016", None),
    (5, 1004, "C07AB02", "Metoprolol 50 mg tablet met gereguleerde afgifte", "1x per dag 1 tablet", "23-02-2020", None),
    (6, 1004, "C10AA01", "Simvastatine 40 mg tablet", "1x per dag 1 tablet, 's avonds", "05-05-2009", None),
    (7, 1004, "N02BE01", "Paracetamol 500 mg tablet", "zo nodig, maximaal 6 per dag", "01-03-2022", "15-03-2022"),
]

ALLERGIEEN = [
    (1, 1001, "Penicilline", "medicijn", "ernstig", "12-08-1975"),
    (2, 1002, "Huisstofmijt", "omgeving", "licht", "01-06-1985"),
    (3, 1003, "Pinda", "voedsel", "ernstig", "30-04-1994"),
]

VERRICHTINGEN = [
    (1, 1001, "Staaroperatie", "09-10-2020"),
    (2, 1002, "Blindedarmoperatie", "14-07-1990"),
    (3, 1004, "Plaatsing pacemaker", "03-03-2021"),
]

HULPMIDDELEN = [
    (1, 1004, "Pacemaker", "03-03-2021"),
]


def bouw(pad: Path) -> None:
    pad.parent.mkdir(parents=True, exist_ok=True)
    if pad.exists():
        pad.unlink()
    conn = sqlite3.connect(pad)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO praktijk VALUES (?,?,?,?,?,?)", PRAKTIJK)
    conn.executemany("INSERT INTO huisartsen VALUES (?,?,?,?,?)", HUISARTSEN)
    conn.executemany("INSERT INTO patienten VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", PATIENTEN)
    conn.executemany("INSERT INTO episodes VALUES (?,?,?,?,?,?,?)", EPISODES)
    conn.executemany("INSERT INTO medicatie VALUES (?,?,?,?,?,?,?)", MEDICATIE)
    conn.executemany("INSERT INTO allergieen VALUES (?,?,?,?,?,?)", ALLERGIEEN)
    conn.executemany("INSERT INTO verrichtingen VALUES (?,?,?,?)", VERRICHTINGEN)
    conn.executemany("INSERT INTO hulpmiddelen VALUES (?,?,?,?)", HULPMIDDELEN)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Gebruik: python3 maak_epd.py <pad-naar-epd.sqlite>")
    doel = Path(sys.argv[1])
    bouw(doel)
    print(f"Oefen-database gebouwd: {doel}")
