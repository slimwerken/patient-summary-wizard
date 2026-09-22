# Zo maak je een export van je testdata

De wizard heeft een bestand met testdata nodig. De vorm maakt niet uit: Excel, CSV,
JSON, XML, een database-dump, een schermafdruk of een paar losse rijen is allemaal goed.
Zet het bestand in de map `mijn-data/` en typ `/start`.

**Alleen testdata.** Nooit een export van productie, nooit echte patienten.

## Wat je minimaal nodig hebt

De tabellen (of schermen) over: patient, problemen of diagnoses, allergieen, medicatie,
verrichtingen en hulpmiddelen. Heb je er een paar niet? Ook goed, dan blijft dat onderdeel
leeg. Een klein setje van 5 tot 25 patienten is genoeg.

## Per systeem

| Systeem | Zo maak je de export |
|---|---|
| **Microsoft SQL Server** | In SQL Server Management Studio: rechtsklik op de database, Tasks, Export Data, kies "Flat File" (CSV) per tabel. Of per tabel: `bcp "SELECT * FROM dbo.Patient" queryout patient.csv -c -t, -S <server> -d <testdb> -T` |
| **PostgreSQL** | `psql -d <testdb> -c "\copy patient TO 'patient.csv' CSV HEADER"` per tabel. Of de hele structuur plus data: `pg_dump --inserts <testdb> > dump.sql` |
| **MySQL / MariaDB** | `mysqldump --skip-extended-insert <testdb> > dump.sql`. Of per tabel via MySQL Workbench: Table Data Export Wizard, CSV |
| **Oracle** | In SQL Developer: rechtsklik op de tabel, Export, CSV. Of `expdp` voor een hele dump |
| **SQLite** | Kopieer het `.sqlite`- of `.db`-bestand zelf. Of: `sqlite3 test.db ".dump" > dump.sql` |
| **MongoDB** | `mongoexport --db <testdb> --collection patients --out patients.json` |
| **Access** | Externe gegevens, Exporteren, Tekstbestand (CSV) per tabel |
| **Excel** | Het bestand zelf, met een tabblad per tabel |
| **Een web-API** | Sla een voorbeeldantwoord op als JSON (bijvoorbeeld uit Postman of de browser), of de API-documentatie |
| **Geen toegang tot de database** | Maak schermafdrukken van een patientdossier: de patientgegevens, de probleemlijst, medicatie en allergieen. De wizard leest de velden uit het beeld en bouwt daar de mapping op. Voor het script zelf is later alsnog een echt bestand nodig |

## Twijfel?

Vraag het aan je assistent: *"Ik werk met <systeem>. Hoe maak ik een export van de
testtabellen voor de Patient Summary?"* Of vraag het op de dag zelf aan Bart, Remco of
Lilian.
