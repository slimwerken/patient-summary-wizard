# Van eigen database naar Patient Summary, in zes stappen

Je werkt in VS Code met Claude Code. Je typt gewone zinnen, Claude doet het werk,
jij controleert. Kopieer de opdrachten gerust letterlijk.

**Vooraf, thuis:** typ `python3 tools/valideer.py --controleer`. Dat zet de keuring klaar
en haalt de benodigde bestanden op, zodat het op de dag zelf niet op de wifi wacht.

**Met je eigen systeem?** Vervang `data/epd.sqlite` in de opdrachten door hoe je bij je
eigen testomgeving komt (een testdatabase, een export met testdata, een API). Alleen
testdata, nooit productie. Lukt dat vandaag niet, oefen dan eerst op `data/epd.sqlite`:
de stappen zijn precies hetzelfde.

---

### 1. Verkennen

> Bekijk data/epd.sqlite. Welke tabellen en kolommen zijn er, en welke daarvan gaan over
> de patient, problemen, allergieen, medicatie, verrichtingen en hulpmiddelen? Laat een
> paar voorbeeldrijen zien. Nog niets bouwen.

### 2. De spec lezen en de mapping maken

> Lees de Patient Summary-specificatie in specs/ (pak het pakket uit). Welke onderdelen
> zijn verplicht? Maak mijn-koppeling/mapping.md: per kolom uit onze database het FHIR-pad
> en de regel voor de omzetting. Zet alles wat je niet zeker weet onder "Open vragen".
> Nog geen code.

### 3. Controleren (jij, niet Claude)

Lees `mijn-koppeling/mapping.md`. Klopt het met hoe jullie systeem echt werkt? Vraag de
open vragen na bij iemand die de spec kent. Dit is het moment waarop jouw vakkennis telt.

### 4. Bouwen

> Schrijf mijn-koppeling/converter.py die volgens mapping.md per patient een Patient
> Summary-bundel maakt in output/. Alleen standaard Python, geen AI in het script, en
> vaste id's zodat dezelfde invoer altijd dezelfde uitvoer geeft. Zet de codevertalingen
> in een aparte tabel en raad geen codes: wat je niet weet meld je. Schrijf tests in mijn-koppeling/tests/
> en draai ze.

### 5. Keuren en verbeteren

> Keur de output met python3 tools/valideer.py --alles. Los de fouten op: eerst de
> mapping, dan de code, en voeg per fout een test toe die hem had moeten vangen. Herhaal
> tot er geen fouten meer zijn en vertel welke waarschuwingen er overblijven en waarom.

Schrik niet van de waarschuwingen. Een deel komt uit de spec zelf (Europese codelijsten
die de keuring niet kan ophalen, en Nederlandse codelijsten zoals ICPC die hij niet kent).
Fouten moeten weg, waarschuwingen moet je kunnen uitleggen. En let op: de keuring kijkt
naar de vorm. Of de inhoud klopt, controleer jij in de mapping.

### 6. Vastleggen als skill

> Leg deze werkwijze vast als skill in .claude/skills/patient-summary/SKILL.md: hoe je
> de koppeling draait, de output keurt, een fout oplost, en wat je doet als de spec
> verandert. Kort en in stappen.

Vanaf nu typ je `/patient-summary` en draaien alle stappen in een keer.

---

## Thuis verder

- Komt er een nieuwe versie van de spec? Typ: *"De spec is veranderd, hier is de nieuwe
  versie. Wat raakt dit in onze mapping en code?"* Je krijgt eerst een lijstje, dan pas
  aanpassingen.
- Groene eigen tests zeggen iets over je code. De validator zegt iets over de spec.
  Je hebt ze allebei nodig.
