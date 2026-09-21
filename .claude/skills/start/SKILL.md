---
name: start
description: Start de wizard die de gebruiker stap voor stap van eigen testdata naar een goedgekeurde HL7 Europe Patient Summary brengt. Gebruik bij "/start", "begin", "start de wizard", "help me op weg", "waar begin ik".
---

# Start de wizard

Lees `WIZARD.md` in de hoofdmap van dit project en volg die van stap 0 tot en met stap 7.

- Gebruik AskUserQuestion voor elke keuze: een vraag per keer, 2 tot 4 opties, je
  aanbeveling bovenaan. Vul altijd `question`, `header` (maximaal 12 tekens), `multiSelect`
  en per optie `label` en `description`.
- Voer alle commando's zelf uit. De gebruiker kiest en controleert alleen.
- Houd je aan de harde regels in `WIZARD.md`, vooral: alleen testdata, en nooit een code raden.
