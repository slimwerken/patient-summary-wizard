# Bart's dummy data

De export die Bart gebruikte in de live demo op de AI mini-plugathon van Nictiz
(23 september 2026). Een verzonnen huisartsenpraktijk, Noorderhaven, met vijf
verzonnen patienten. Alles is testdata: geen echte personen.

## Zo gebruik je het

1. Kopieer alle bestanden uit deze map naar `mijn-data/`.
2. Open Claude Code en typ `/start`.

## Wat erin staat

Acht CSV-bestanden, een per tabel, zoals een huisartsensysteem ze exporteert. Het
patientnummer (`pat_id`) koppelt alles aan elkaar.

| Bestand | Wat |
|---|---|
| `patienten.csv` | De vijf patienten (1001 tot en met 1005) |
| `episodes.csv` | Problemen, met ICPC-code |
| `medicatie.csv` | Medicijnen, met ATC-code |
| `allergieen.csv` | Allergieen, als vrije tekst |
| `verrichtingen.csv` | Operaties en ingrepen |
| `hulpmiddelen.csv` | Bijvoorbeeld een pacemaker |
| `huisartsen.csv` | De twee huisartsen |
| `praktijk.csv` | De praktijk |
| `LEESMIJ.txt` | De korte uitleg die bij de export hoort |

Scheidingsteken: puntkomma. Datums: DD-MM-JJJJ. Patient 1005 heeft bewust geen
medische gegevens, zo zie je hoe een leeg dossier eruitziet.
