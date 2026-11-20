# Hypothese: 9 EMA + VWAP, long op de Nasdaq 100, 5 minuten, met prop firm-uitdaging (test O)

Datum: 19 november 2026 · Bron: Instagram-reel van 16 november 2026 en een bericht op X van 17 november 2026 van dezelfde maker · Status: **versie 1.1, 20 november 2026, goedgekeurd (keuze A na de gezakte ruiscontrole van v1.0). Versie 1.0 (K1 A, K2 A) blijft bewaard, SHA-256 7de9e9f5... Nog geen echte koersdata geopend voor deze test**

Wijziging ten opzichte van 1.0: C5 is geen beslissende claim meer. De ruiscontrole van v1.0 liet zien dat de regel op markten zonder voordeel vaker het doel haalt dan willekeurige instappen (gemiddeld percentiel 69,9, grens 35 tot 65), en dat twee andere controlegroepen dat niet oplossen (percentiel 99,9 en 91,1). Zie de README bij de resultaten. De pass rate van Null A wordt beschrijvend gemeld, samen met de pass rate van de regel op de nepmarkten van de ruiscontrole. Verder is niets gewijzigd.

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 0. Wat ik al weet vóór deze test (eerlijk vooraf)

[geverifieerd, meetlog test N] Dezelfde Nasdaq-data (USTEC M1) is al gebruikt in test N, als aanvullende meting: een verwante regel op 3 minuten, long en short, uit bij een slot door de EMA 9. Uitkomst: -2,695 punt per trade, percentiel 71,5 tegen toeval. Deze test is dus niet blind voor de markt. Wel nieuw: 5 minuten, alleen long, een bevestigingskaars, een andere periode als beslissende periode, en de prop firm-uitdaging. Die nieuwe getallen heb ik nog niet gezien. Dit staat in elke publicatie.

## 1. Wat de bron belooft

[geverifieerd, ondertitels in beeld, 19 november 2026] De regels zoals de bron ze geeft:
- "It uses two lines: the VWAP and the 9 EMA."
- Regel 1: "The 9 EMA crosses above the VWAP."
- Regel 2: "Wait for a candle to close above the EMA. That's your entry."
- Regel 3: "[Hold] the trade until a candle closes back below the EMA."

[geverifieerd, beeld in de reel] Grafiek met tijdframe 5 minuten, koers rond 21.000. Resultatenscherm van een backtestplatform: 396 trades, winrate 56,6%, profit factor 1,84, gemiddelde R:R 1,41, netto +$29.985,04 (+299,85%), max drawdown -22,0%, verwachting +$75,72 per trade, gemiddelde winst +$292,78, gemiddeld verlies -$206,97.

[geverifieerd, caption en X] "This strategy has an 85% prop firm pass rate" (reel). Op X, een dag later: "the backtest results over the last 3 years", en "the prop firm pass rate of 84%".

[geverifieerd] Niet genoemd: het instrument bij naam, de sessie, de periode precies, de positiegrootte, de kosten, en welke prop firm met welke accountgrootte. [geverifieerd, website van het platform] De simulator van het platform rekent met de regels van bestaande firms (five well-known firms) en controleert sinds 5 november 2026 ook open verliezen binnen een trade.

[aanname] Instrument: de Nasdaq 100-future (NQ). Koers rond 21.000 past daarbij, de S&P 500 stond nooit zo hoog.

Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Winrate 56,6% | Netto winrate per trade in P1 |
| C2 | De regel maakt winst, profit factor 1,84 | Gemiddeld netto resultaat per trade en profit factor in P1 |
| C3 | De regel kiest betere momenten dan toeval | Echt resultaat tegen de controlegroep met dezelfde uitstapregel |
| C4 | 85% van de prop firm-uitdagingen wordt gehaald | Aandeel gehaalde uitdagingen in P1, onder de regels uit K2 |
| C5 | Die pass rate komt van de regel, niet van de uitdaging zelf | Sinds v1.1 niet beslissend, zie de wijziging bovenaan; alleen beschrijvend |

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd, meetlog test N] Een verwante regel verloor op dezelfde data ruim zijn kosten. Ik verwacht dus geen winst [aanname]. Dat is geen reden om niet te meten.
2. [aanname] Een pass rate hangt sterk af van de regels van de uitdaging: winstdoel, maximaal verlies, positiegrootte. Een regel zonder voordeel kan een hoge pass rate halen als het doel klein is ten opzichte van de verliesgrens. Daarom C5: dezelfde uitdaging met willekeurige instappen.
3. [geverifieerd] De bron noemt geen firm. Elke keuze voor een firm is van ons. Zie K2.
4. [geverifieerd, eerdere tests] Onze data is een CFD op de Nasdaq 100 met tickvolume, geen echte future met echt volume. De VWAP wordt gewogen met tickvolume [aanname dat dit de echte VWAP benadert]. Gevoeligheid: VWAP zonder volume.
5. [aanname] Een CFD loopt in punten gelijk met de index. De future heeft een basis (rente, dividend), die verschuift alle koersen per dag nagenoeg gelijk. Voor kruisingen binnen een dag maakt dat weinig uit.

## 3. Keuzes (gekozen op 20 november 2026: K1 A, K2 A, de vetgedrukte opties)

| Keuze | A | B |
|---|---|---|
| K1 · Sessie | **Reguliere beurstijd, 9:30 tot 16:00 New Yorkse tijd.** VWAP begint om 9:30, alles dicht om 16:00. Zelfde opzet als test N, zodat de uitkomsten te vergelijken zijn | Hele futuresdag, 18:00 tot 17:00 New Yorkse tijd (CME). VWAP begint om 18:00. De dag van firm A loopt ook zo, met alles dicht om 16:10 New Yorkse tijd |
| K2 · Prop firm-uitdaging | **Firm A, 50K evaluation.** Winstdoel $3.000, maximaal verlies $2.000 meebewegend op het slot van de dag, consistentie 55%. Geen daglimiet (die is optioneel). Bron: het helpcentrum van firm A, bijgewerkt 18 en 24 september 2026 [geverifieerd] | Firm B, 25K evaluation. Winstdoel $1.250, maximaal verlies $1.000 meebewegend op het slot van de dag, consistentie 40%. Bron: het helpcentrum van firm B, 26 augustus en 18 oktober 2026 [geverifieerd]. Het platform gebruikte een 25K-rekening van firm B in een andere reel |

De niet-gekozen variant van K1 en K2 wordt aanvullend gerapporteerd, niet beslissend.

## 4. Mechanische vertaling (vast na goedkeuring)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**4.1 Sessie en dagen.** Volgens K1. Bij A: opening per dag zoals test N, de sprong in tickvolume rond 16:30 servertijd; een dag telt mee met minstens 90% van de 390 minuutbars. Bij B: van 1:00 tot 23:59 servertijd (18:00 tot 16:59 New Yorkse tijd); een dag telt mee met minstens 90% van de minuten die het bestand die dag normaal heeft.

**4.2 Bars.** 5-minutenkaarsen uit de M1-data, beginnend bij de opening van de sessie (bij A: 9:30, 9:35, ... 15:55, 78 kaarsen).

**4.3 Indicatoren.** Zoals test N, op 5 minuten:
- EMA 9 op de slotkoers van de 5-minutenkaarsen, doorlopend over de dagen, alleen binnen de sessie.
- VWAP: begint elke dag opnieuw bij de eerste kaars. Prijs per minuut OHLC4, gewicht tickvolume. Waarde op het slot van de kaars over alle minuten tot en met die kaars.

**4.4 Signaal.**
- Regel 1, de kruising, op het slot van kaars t: EMA9(t-1) ≤ VWAP(t-1) en EMA9(t) > VWAP(t). Pas vanaf de tweede kaars van de dag.
- Regel 2, de bevestiging: de eerste kaars k ≥ t+1 met slot(k) > EMA9(k), zolang EMA9 boven de VWAP blijft. Zakt de EMA 9 eerst weer onder de VWAP (op het slot van een kaars), dan vervalt de kruising zonder trade. "Wait for" lees ik als: de kruisingskaars zelf telt niet als bevestiging. De variant waarin die wel telt, rapporteer ik aanvullend.
- Instap op de open van kaars k+1. Nooit op het slot van de bevestigingskaars. Geen instap op de laatste kaars van de dag.

**4.5 Uitstap.** Regel 3: uit als slot(j) < EMA9(j), gecontroleerd vanaf het slot van de instapkaars, uit op de open van kaars j+1. Verder: alles dicht op het slot van de laatste kaars van de sessie. Geen doel en geen stop in punten (de bron noemt er geen).

**4.6 Eén positie tegelijk, alleen long.** Een nieuwe kruising terwijl de positie openstaat, vervalt. Shorts bestaan niet in deze regel.

**4.7 Resultaat.** Per trade in punten en in dollars voor 1 NQ-contract ($20 per punt), netto na kosten. 1 contract is een [aanname]: de gemiddelde winst uit de bron ($292,78) komt bij 1 contract neer op ca. 14,6 punt, wat past bij trades op 5 minuten; bij 1 micro-contract zou het 146 punt zijn. Gevoeligheid: 2 contracten in de prop firm-simulatie.

## 5. De drie vaste regels

**Kosten.** De spread uit de SPREAD-kolom op de instapminuut, plus 1 punt slippage per kant, zoals USTEC in test N [geverifieerd, hypothese test N]. Gevoeligheid: slippage 0, 1 en 2 keer. In dollars: punten × $20. Geen aparte commissie; de slippage van 1 punt per kant ($40 per ronde) is ruimer dan de commissie van een NQ-contract [aanname].

**Volgorde.** Het pad wordt minuut voor minuut doorlopen. Alle uitstappen vallen op een kaarsopening. In de prop firm-simulatie telt het open verlies per minuut mee (zie 6): de laagste koers van elke minuut tegen de instap, minus de kosten.

**Controlegroep.** 10.000 runs, seed 43, bootstrap per handelsdag.
- **Null A, beslissend voor C3:** dezelfde dagen, dezelfde sessie, dezelfde uitstapregel en dezelfde kosten, alleen long. Een opeenvolgend proces: op elke 5-minutenkaars zonder open positie (behalve de eerste en laatste van de dag) waarop het slot boven de EMA 9 ligt, opent toeval een long met kans p, op de open van de volgende kaars. p is zo gekozen dat het gemiddelde aantal trades gelijk is aan dat van de regel. Toetst of de kruising met de VWAP iets toevoegt bovenop een willekeurige instap boven de EMA 9 met dezelfde uitstap.
- **Null A in de uitdaging, beschrijvend (sinds v1.1):** dezelfde simulatie van de uitdaging, met de trades van Null A. 2.000 runs, seed 43.

## 6. De prop firm-simulatie (vast)

[aanname, vertaling van de regels van de firm naar code; bronnen in K2]
- **Rekening:** startsaldo volgens K2. 1 NQ-contract per trade, de regel uit 4.
- **Verliesgrens:** maximaal verlies onder het hoogste saldo op het slot van een handelsdag; de grens stijgt alleen en stopt bij het startsaldo (firm A) of op startsaldo + $100 (firm B). Uitdaging mislukt zodra het saldo inclusief het open verlies (laagste koers per minuut) de grens raakt.
- **Doel:** gehaald op het slot van een handelsdag waarop de netto winst sinds de start minstens het doel is en de consistentieregel klopt. Firm A: beste dag hoogstens 55% van het doel; is de beste dag groter, dan wordt het doel beste dag / 0,55. Firm B: beste dag hoogstens 40% van de totale winst. Minimaal 2 handelsdagen.
- **Pogingen na elkaar (beslissend):** de eerste poging begint op de eerste handelsdag van P1. Na gehaald of mislukt begint de volgende poging op de volgende handelsdag, met een nieuwe rekening. Een poging die aan het eind van P1 nog loopt, telt niet mee (wordt wel gemeld).
- **Pass rate** = gehaald / afgerond, met 95%-interval (Wilson).
- Aanvullend: een poging die op elke handelsdag begint (overlappend, beschrijvend), mediane duur van een poging in dagen.
- Geen kosten voor de uitdaging zelf (inschrijfgeld), geen uitbetalingsregels: alleen de vraag of het doel wordt gehaald.

## 7. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 1.500 handelsdagen met minuutbars, zoals test N (60 stapjes per minuut, geen trend, geen openingseffect, vaste spread, willekeurig tickvolume), op het prijsniveau van de Nasdaq (start 15.000, spread 1 punt). Seed 7.

Grenzen:
- Percentiel van het gemiddelde netto resultaat tegen Null A gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95.
- (v1.0, vervallen in v1.1) Percentiel van de pass rate tegen Null A in de uitdaging gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95. Gezakt, zie bovenaan.

Haalt het script dat niet, dan eerst de oorzaak zoeken en een nieuwe versie van dit document, vóór de echte data.

## 8. Data

[geverifieerd, meetlog test N] USTEC M1, IC Markets, `Test\box-theory\USTEC_M1_201208060000_202611052200.csv`, SHA-256 714b4cc0..., loopt tot 5 november 2026, spreadkolom gevuld vanaf 2019.

Perioden:
- **P1, beslissend voor C1 tot en met C5:** de "last 3 years" uit de bron, gerekend vanaf het bericht op X: 17 november 2023 tot en met 5 november 2026 (eind van de data).
- Aanvullend: 2019 tot 16 november 2023.

Datacontrole vóór de run, alleen metadata: aantal geldige sessies per jaar, aandeel minuten met lege spread of tickvolume nul.

## 9. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval (Wilson) van de netto winrate in P1 ligt onder 56,6% |
| C2 | De bovengrens van het 95%-interval (dagbootstrap) van het gemiddelde netto resultaat per trade in P1 ligt onder 0, of de bovengrens van het 95%-interval van de profit factor ligt onder 1,84 |
| C3 | Het echte gemiddelde netto resultaat in P1 ligt niet boven percentiel 95 van Null A |
| C4 | De bovengrens van het 95%-interval (Wilson) van de pass rate (pogingen na elkaar) ligt onder 85% |
| C5 | Vervallen in v1.1: niet beslissend, alleen beschrijvend |

Valt C3, dan is de regel dood: niet repareren, niet optimaliseren. Onder 100 trades staat in het rapport "onvoldoende trades". Onder 20 afgeronde pogingen staat bij de pass rate "onvoldoende pogingen".

## 10. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades en trades per dag (de bron: 396 in ca. 3 jaar), winrate netto en bruto, gemiddeld netto resultaat in punten en dollars met 95%-interval, profit factor met interval, gemiddelde winst en gemiddeld verlies in dollars (de bron: +$292,78 en -$206,97), percentiel tegen Null A, het resultaat zonder kosten, de drie kostenniveaus, mediane duur van een trade, per jaar, aantal pogingen, gehaald, mislukt en lopend, pass rate met interval, pass rate van Null A (beschrijvend), de pass rate van de regel op de nepmarkten uit de ruiscontrole, mediane duur van een poging, de overlappende pass rate, de niet-gekozen varianten uit K1 en K2, de bevestigingsvariant uit 4.4, de VWAP zonder volume, 2 contracten, en 2019 tot november 2023.

Titel volgens de vaste regel: de strategie met het percentage, geclaimd en gemeten, bijvoorbeeld "9 EMA + VWAP: 85% prop pass rate claimed, X% measured".

## 11. Volgende stap

1. Goedgekeurd op 20 november 2026 (K1 A, K2 A). SHA-256 in de README bij de resultaten en de Engelse versie ernaast.
2. Script `vwap_prop.py`, gebouwd op `vwap_control.py`: eerst zelftest (EMA, VWAP, regel tegen een tweede implementatie, de uitdaging tegen een handberekening van een paar dagen), dan de ruiscontrole uit 7.
3. Datacontrole uit 8, dan run 01.
