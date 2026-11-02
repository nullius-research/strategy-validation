# Hypothese: supply-demand-levels op volumeprofiel

Datum: 29 oktober 2026 · Bron: openbaar document van een aanbieder van een tradingcursus · Status: **vooraf vastgelegd, versie 1.3, nog geen echte uitkomsten bekeken** (wijzigingen in sectie 9)

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat het document belooft

[geverifieerd] Het document doet deze toetsbare claims (in eigen woorden samengevat):

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Willekeurig long of short bij elk level, 1:1, geeft ongeveer 50 % winst en dus break-even. Dat noemt het de "vloer". | Muntworp op dezelfde levels, met kosten |
| C2 | Met het A+-filter (trend, structuur, momentum) stijgt de winrate naar 60–80 %. | Winrate gefilterd tegen ongefilterd |
| C3 | Opbrengst 5–10R per maand. | Netto R per kalendermaand |
| C4 | Op deze volume-levels móet de prijs reageren, ze verlopen niet. | Reactie op echte levels tegen nep-levels met dezelfde onderlinge afstand |
| C5 | De two-strike-regel (stop na 1 winst of 2 verliezen) verbetert het resultaat. | Zelfde systeem met en zonder dagregel |

[geverifieerd] Niet toetsbaar en dus buiten deze meting: "600+ traders verdienen ermee", "3+ jaar zelf gebruikt", de testimonials en screenshots van uitbetalingen.

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd, rekenkundig] C1 negeert kosten. Bij 50 % winst en 1:1 is het resultaat niet 0 maar min de kosten per trade. De "vloer" ligt onder nul.
2. [geverifieerd] Het document is intern niet consistent over de risk-reward. Het rekent met 1:1, maar de beschreven stop ("ongeveer in het midden van je twee omliggende levels") met als target het volgende level geeft eerder rond 2:1. Bij een entry óp een level is "het midden van de twee omliggende levels" bovendien het level zelf. Zie keuze 3.6.
3. [geverifieerd] Kernbegrippen zijn niet mechanisch gedefinieerd: welke "cloud" (periodes ontbreken), wanneer structuur "zachter" is, wat telt als "rejection aan beide kanten". Elke vertaling naar regels is dus een keuze van mij. De maker kan altijd zeggen "zo bedoel ik het niet". Daarom staan alle keuzes hieronder expliciet, en gelden ze als vast.
4. [aanname] Een volumeprofiel op een CFD meet tickvolume, geen echt verhandeld volume. Het argument "daar zit het institutionele geld" geldt alleen bij echte futures-volumes. Zie datakeuze in sectie 5.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: het zijn mijn keuzes om discretionaire tekst te vertalen naar regels. Waar het document een getal noemt, staat dat erbij.

**3.1 Instrument en tijd.** ES (S&P 500-future), het voorbeeld uit het document. Alleen reguliere sessie 9:30–16:00 ET. Signalen op 5-minutenbars. Wat om 16:00 nog open staat, gaat dicht op de slotkoers.

**3.2 Levels.**
- VRVP: volumeprofiel over de 20 voorgaande sessies, 200 rijen (getal uit het document).
- SVP: per sessie een profiel van 100 rijen (getal uit het document), daaruit de Point of Control.
- Een level is een high-volume node (lokaal maximum in het VRVP, in de bovenste 20 % van alle rijen) waar binnen 5 punten een POC van één van de 20 voorgaande sessies ligt.
- Rejection aan beide kanten: in die 20 sessies is de zone minstens één keer van boven en één keer van onder geraakt, telkens gevolgd door een beweging van minstens 10 punten weg van de zone binnen 12 bars.
- Zone = 8 punten breed, gecentreerd op de node (document: 7–10).
- Levels worden vastgesteld vóór 9:30 met alleen data van eerdere sessies. Geen look-ahead.

**3.3 Trend ("cloud").** EMA 34/50-cloud op 5 minuten én 1 uur (document noemt beide tijdframes, niet de periodes). Bullish als op beide tijdframes EMA34 > EMA50 én EMA50 hoger staat dan 6 bars eerder. Bearish andersom. Anders "vlak": niet handelen.

**3.4 Structuur.** Swingpunten met een fractal van 2 bars links en rechts op 5 minuten. Bullish als de laatste twee swing highs én swing lows allebei hoger liggen. Bearish andersom. Anders geen trade.

**3.5 Momentum.** In de laatste 6 bars heeft de prijs de 5m-cloud geraakt en de laatste bar sloot weer aan de trendkant van de cloud.

**3.6 Entry, stop, target.**
- Long: prijs komt van boven in een zone, trend en structuur bullish, momentum bevestigd. Short: spiegelbeeld bij een zone die van onder wordt geraakt.
- Entry op de slotkoers van de eerste 5m-bar in de zone waarop alle filters kloppen.
- Stop: halverwege tussen dit level en het volgende level áchter de trade.
- Target: het volgende level vóór de trade.
- Stop naar break-even zodra de koers 50 % van de afstand naar het target heeft afgelegd (uit het document).
- Is het volgende level er niet (buiten de kaart), dan geen trade.

**3.7 Dagregels.** Stop na 1 winst of na 2 verliezen (A+-checklist). Basisvariant zonder extra limiet. Variant "1 trade per dag" (fase "week 5+" uit het document) wordt apart gerapporteerd, niet als vervanging.

## 4. De drie vaste regels

**Kosten.** [aanname] 1 tick slippage per kant (0,25 punt = $12,50) plus $4,50 commissie per round trip per contract. [geverifieerd, rekenkundig] Bij een stop van 12,5 punten ($625) is dat ongeveer 0,05R per trade. Gevoeligheid: 0, 1 en 2 ticks per kant.

**Volgorde.** Bar voor bar op 1-minutendata waar beschikbaar. Raakt één bar zowel stop als target, dan telt hij als stop. De break-evenverschuiving geldt pas vanaf de bar ná de bar waarin 50 % werd gehaald.

**Controlegroepen.** 10.000 runs per controle, seed 19.
- **Null A, beslissend voor C2:** dezelfde level-aanrakingen, zónder filter, richting per muntworp, zelfde stop-, target- en break-evenregels, zelfde dagregels, zelfde kosten. Dit is precies de "vloer" uit het document, dus meteen de toets van C1.
- **Null B, beslissend voor C4:** nep-levels. De echte levelkaart van die dag wordt als geheel verschoven met een willekeurig bedrag tussen 5 en 15 punten (boven of onder). Zelfde onderlinge afstanden, zelfde filters, zelfde regels. Toetst of de volume-levels iets toevoegen tegenover willekeurige lijnen met hetzelfde ritme.
- **Null C, aanvullend:** zelfde dagen en filterstatus, entry op een willekeurig tijdstip waarop de filters ook klopten maar zonder level, zelfde stopafstand in punten. Toetst of "bij het level zijn" ertoe doet.

## 5. Data: keuze ligt bij jou

| | A. MT5 broker-data US500 (CFD) | B. ES-futures 1m met echt volume (betaalde bron) | C. SPY 5m via Yahoo |
|---|---|---|---|
| Kosten | Gratis [aanname] | Betaald, prijs niet gecontroleerd [aanname] | Gratis [geverifieerd, TSLA-test] |
| Periode | Meerdere jaren M1 [aanname, verschilt per broker] | Meerdere jaren [aanname] | Ongeveer 60 dagen [geverifieerd, TSLA-test: 59 sessies] |
| Volume | Tickvolume, niet het "institutionele" volume [aanname] | Echt verhandeld volume, past bij de claim | Echt volume van de ETF, wel ander instrument |
| Trouw aan het document | Zwak op levels, goed op prijs | Hoogst | Matig (SPY, niet ES; punten herschalen) |
| Genoeg trades (≥100)? | Ja bij ≥2 jaar [aanname] | Ja bij ≥2 jaar [aanname] | Nee, maximaal ~60 met 1 trade/dag [geverifieerd, rekenkundig] |
| Bruikbaar als | Volwaardige test, met kanttekening op C4 | Volwaardige test, sterkste publicatie | Alleen pilot om het script te testen |

[aanname] Mijn inschatting: C als pilot voor het script, daarna B als de publiceerbare meting. A is een redelijk alternatief als B te duur blijkt, maar dan is C4 niet hard te maken.

Minimaal: 2 volle jaren, alle jaren gerapporteerd, geen enkele parameter gekozen op basis van de uitkomst.

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | Null A gemiddeld netto R duidelijk onder 0 (90 %-bootstrapinterval volledig negatief). Dan is de "vloer" geen break-even. |
| C2 | Echt resultaat (gem. netto R) niet boven percentiel 95 van Null A, óf winrate gefilterd onder 60 %. |
| C3 | Mediaan netto R per maand onder 5. |
| C4 | Echt resultaat niet boven percentiel 95 van Null B. |
| C5 | Variant zonder dagregel heeft een gelijke of hogere gemiddelde netto R per trade. |

Valt C2 én C4, dan is het systeem dood volgens stap 5: niet repareren, niet optimaliseren.

## 7. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades, winrate, gemiddelde netto R met dagbootstrap (90 %), percentiel tegen Null A, B en C, netto R per maand (verdeling, niet alleen gemiddelde), resultaat per jaar, aandeel van de beste 5 % trades in het totaal, en de drie kostenniveaus.

## 8. Volgende stap

Meetscript `levels_control.py` (levels, filters, Null A/B/C, kosten, bar-voor-bar), eerst gedraaid op de pilotdata (optie C) om het script te controleren, nog niet om conclusies te trekken.

## 9. Wijzigingen vóór de eerste echte run

De tekst hierboven blijft staan zoals hij is vastgelegd. Wat hieronder staat vervangt de betreffende punten. Er is bij geen van deze wijzigingen echte marktdata bekeken.

### Versie 1.1 · 29-10-2026 · datakeuze

- Gekozen: **optie A, MT5 broker-data US500, M1**. Daarmee is C4 vooraf al niet hard te maken: het profiel meet tickvolume, geen echt verhandeld volume [aanname, zie sectie 2 punt 4]. Een C4-uitkomst wordt zo ook gerapporteerd.
- De pilot (optie C) vervalt. Het script is in plaats daarvan gecontroleerd op synthetische data, zie 1.2.
- Kosten: de spread komt per bar uit de SPREAD-kolom van de export [geverifieerd dat het script die kolom gebruikt], plus 1 tick (0,25 punt) slippage per kant. Gevoeligheid 0, 1 en 2 ticks. Geen commissie [aanname: CFD-broker zonder commissie; rekent jouw broker die wel, dan moet die erbij].
- Sessie: 16:30–23:00 servertijd [aanname: broker met servertijd gelijk aan New York + 7 uur]. Het script controleert dit zelf aan de tickvolumesprong bij de opening en meldt hoeveel dagen kloppen.
- Prijzen zijn bid. De spread wordt één keer per trade als kosten afgetrokken, ook bij shorts. Het pad van een short wordt op bid gecontroleerd, niet op ask [aanname, kleine optimistische afwijking voor shorts].

Uitwerkingen die in versie 1 niet expliciet stonden, nu vast:
- Volume van een M1-bar wordt gelijk verdeeld over de rijen die de bar raakt. VRVP en POC alleen uit RTH-bars.
- Lokaal maximum = groter of gelijk aan alle rijen binnen ±2.
- EMA-cloud en swingpunten op alle uren (zoals een grafiek ze toont), uurtrend uit de laatste afgesloten uurbar.
- Rejection-venster: de 12 bars ná de aanraakbar, binnen dezelfde sessie.
- Dagregel telt winst en verlies op het bruto resultaat. Een break-evenexit telt als geen van beide.
- Eén kandidaat per zonebezoek. Staat er nog een positie open, dan vervalt dat bezoek.
- Null B: verschuivingen in stappen van 0,25 punt (5,00 tot 15,00, boven of onder).
- Null C: per echte trade een willekeurige vervanger op dezelfde dag, zonder dagregels.

### Versie 1.2 · 29-10-2026 · fouten gevonden op synthetische data

Het script is gedraaid op vier sets kunstmatige random-walk-data van 2 jaar (geen enkele voorspelbaarheid, dus elk "resultaat" is ruis). Twee fouten in mijn opzet kwamen boven:

1. [geverifieerd] **Geen minimale stopafstand.** De entry op de slotkoers kon vlak boven de stop liggen. Trades met minder dan 1 punt risico verloren gemiddeld 4,2R, puur door de kosten. Nieuwe regel: geen trade als entry tot stop kleiner is dan 4 punten. Grond in het document: de stop mag niet zo krap staan dat gewone ruis je eruit haalt. Geldt voor de echte trades en alle controlegroepen.
2. [geverifieerd] **Null A had niet hetzelfde aantal trades.** Het echte systeem (16 trades) werd vergeleken met een band van muntworpruns met honderden trades. Op pure ruis gaf dat percentiel 96,7, dus een vals "voordeel". Null A is daarom gesplitst:
   - **Null A0 (de vloer, voor C1):** muntworp op alle level-aanrakingen, met dagregels, zoals in versie 1.
   - **Null A (beslissend voor C2):** per dag precies zoveel trades als het echte systeem die dag nam, willekeurig gekozen uit de geldige level-aanrakingen van die dag, richting willekeurig.
3. Extra rapportregel: onder 100 trades staat in het rapport "onvoldoende trades". De criteria uit sectie 6 worden dan wel toegepast, maar de uitkomst geldt als niet beslissend.

[geverifieerd] Controle na de wijzigingen: op alle vier ruissets oordeelde het script "dood", met percentielen tegen Null A tussen 8 en 90. Het bruto resultaat van de muntworp was -0,01 punt per trade (standaardfout 0,28), dus de stop-eerst-regel geeft geen merkbare scheefheid. De vloer kwam alleen door de kosten onder nul.

[geverifieerd] Waarschuwing vooraf: op ruisdata gaf het filter maar 13 tot 21 trades in 2 jaar. Of de echte markt er veel meer geeft is onbekend [aanname]. Komt de echte run onder 100 uit, dan is de afspraak nu al: zoveel extra jaren data als de broker levert, met dezelfde regels, en geen enkele regelaanpassing.

### Versie 1.3 · 02-11-2026 · periode en kosten na de datacontrole

Alleen de metadata van de export is bekeken (bars per dag, SPREAD-kolom), geen enkele uitkomst van het systeem of de controlegroepen. Zie `datacontrole-us500-m1.md`.

- Data: export US500 M1 van IC Markets EU (demo-account), gemaakt op 2 november 2026 (`US500_M1_201208060000_202611021049.csv`).
- **Periode: 1 januari 2019 tot en met 30 oktober 2026** (gekozen vóór de run, optie A). Reden: vóór 21 maart 2017 bevat het bestand alleen dagbars, en in 2017 en 2018 is de SPREAD-kolom (bijna) leeg [geverifieerd]. Met die jaren erbij zou het systeem daar vrijwel zonder kosten handelen. 2 november 2026 is een lopende dag en valt eruit.
- **Commissie: 0.** [geverifieerd] Het productblad Indices van IC Markets (CySEC) noemt voor US500 geen commissie, alleen een gemiddelde spread van 0,36 punt. [aanname] De commissie van $3,50 per lot per kant op de site van IC Markets geldt voor forex op een Raw-account, niet voor index-CFD's. Ter vergelijking: de mediane spread in de export is 0,50 punt [geverifieerd], dus de kosten uit de kolom liggen eerder boven dan onder het gemiddelde dat de broker opgeeft.
- **Werkwijze:** het script blijft ongewijzigd. Het bestand wordt vooraf gefilterd op de periode hierboven (`US500_M1_2019-2026.csv`), daarna gaat het met dezelfde argumenten door `levels_control.py`.
