# Hypothese: morning star met trendfilter op goud, met prop firm-uitdaging (test Q), versie 1.0

Datum: 21 november 2026 · Bron: een korte video op sociale media van 7 november 2026 (naam in privébestanden) · Status: **versie 1.0, 21 november 2026. Keuzes K1-A, K2-A, K3-A en K4-A gemaakt op 21 nov; tekst goedgekeurd  op 21 nov. Regels van de firm op 21 nov gecontroleerd op de eigen site van de firm (hoofdstuk 6). Nog geen koersdata bekeken voor deze test.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 0. Niet blind voor deze markt

[geverifieerd, logboek] Dezelfde goud-export (XAUUSD M30) is gebruikt in test F (MA 9/21 + 200 MA, dood, percentiel 63,9) en test P (S/R-breakout, C2 gefalsifieerd, percentiel 91,2). Ik ken dus het grove verloop van goud in deze periode, onder meer de sterke stijging in 2025. Nieuw hier: het kaarspatroon (morning star en evening star), MA 14 en MA 200 als filter, een vast doel van 2R, en de prop firm-uitdaging met risico in procenten van de rekening. Die getallen heb ik nog niet gezien. Dit staat in elke publicatie.

## 1. Wat de bron belooft

[geverifieerd, caption gelezen op 21 nov 2026] Regels in woorden:
- goud (XAUUSD), 1 uur;
- long: de koers staat boven de 14- en de 200-"moving average";
- de kaarsen vormen een morning star: "a falling candle, a small candle, then a strong rising candle";
- koop "when the price goes higher than the third candle";
- stop op het laagste punt van de drie kaarsen, doel 2 × het risico;
- short: alles gespiegeld (evening star onder beide MA's);
- 1% risico per trade, "$1,000 on a $100K account".

[geverifieerd, caption] Getallen van de bron: "In 5 years of gold, it took 512 trades and 43% won", gemiddelde winst ongeveer 2 × gemiddeld verlies, slechtste dag -3,6%, maximale drawdown 7,5%. "81% of 1,000 simulated [firm A] challenges passed", ongeveer 1 op 8 gezakt, de rest niet klaar binnen een jaar, mediaan 155 dagen tot geslaagd, langste reeks 7 doelen op rij.

[geverifieerd] Niet genoemd: soort MA (simpel of exponentieel), wanneer een kaars "klein" of "sterk" is, hoe lang de koopopdracht geldt, kosten, of "passed" één fase of beide fasen betekent, en hoe de 1.000 uitdagingen zijn getrokken.

Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | De regel verdient geld na kosten | Gemiddelde netto R per trade met 95%-interval |
| C2 | Het patroon kiest betere momenten dan toeval binnen dezelfde trend | Echt resultaat tegen Null A (zelfde trendfilter, geen patroon) |
| C3 | 512 trades in 5 jaar, 43% winst, max drawdown 7,5% | Alleen beschrijvend naast onze meting (reconstructie, zie 2.1) |
| C4 | 81% van de uitdagingen gehaald | Pass rate in onze simulatie (hoofdstuk 6), met 95%-interval |
| C5 | Die pass rate komt van de regel, niet van de uitdaging zelf | Alleen beschrijvend: dezelfde simulatie met de trades van Null A (zoals test O v1.1) |

## 2. Zwakke plekken, vooraf benoemd

1. [geverifieerd] Wij testen een openbare, vooraf vastgelegde vertaling van de caption, niet de code van de bron (die alleen te krijgen is met een account; daar is bewust van afgezien). Een andere uitkomst dan 43% of 512 trades kan aan onze vertaling liggen. Daarom is C3 alleen beschrijvend, en zegt elke publicatie dat het een reconstructie is (zoals test J en P).
2. [aanname] Een vast doel van 2R met 43% winst geeft vóór kosten +0,29R per trade. Kleine verschillen in winrate maken hier veel uit: bij 2R ligt het omslagpunt rond 33% vóór kosten [geverifieerd, rekensom].
3. [aanname] Een pass rate hangt sterk af van de regels van de uitdaging en de positiegrootte. Daarom C5.
4. [geverifieerd, eigen simulatie 21 nov] Bij onafhankelijke trades met 43% winst en 2R/-1R is de mediane langste winreeks over 512 trades 7 (past bij de claim), en de mediane maximale drawdown ongeveer 13,5R. Een drawdown van 7,5% bij 1% risico kan als het risico in dollars vast blijft terwijl de rekening groeit [aanname over hoe de bron rekent]. Geen oordeel vooraf.
5. [aanname] Brokertijd is waarschijnlijk GMT+2 of GMT+3. H1-bars en handelsdagen zijn in brokertijd. De daglimiet van de firm geldt in de tijdzone van de firm (CE(S)T); het verschil van 1 tot 2 uur negeer ik.

## 3. Mechanische vertaling

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Data.** `XAUUSD_M30_199804220000_202611052200.csv`, dezelfde MT5-export als test F en P, SHA-256 c7d40c32a3d53f7ccfcc199b51d910daccaeafc2e6f996a0a9e1925aa684d7d2 (wordt vóór de run opnieuw gecontroleerd). H1-bars worden uit de M30-bars gebouwd per brokeruur. Het pad van elke trade wordt op M30 doorlopen.

**3.2 Bruikbare data.** Zelfde controle op volledigheid als test F en P: de meting begint in de eerste kalendermaand waarin elke handelsdag minstens 40 M30-bars heeft. Opwarmen: de eerste 200 H1-bars na die start tellen niet mee (MA 200).

**3.3 MA's (K1).** Op het slot van H1-bars, waarde van de afgesloten bar.

**3.4 Patroon op H1-bars t−2, t−1, t (K2).** Lichaam = |slot − open|.
- Morning star: kaars t−2 dalend (slot < open); lichaam t−1 ≤ 1/3 van lichaam t−2; kaars t stijgend (slot > open) en slot(t) > midden van het lichaam van t−2. Geen gat vereist (goud handelt bijna doorlopend).
- Evening star: gespiegeld (t−2 stijgend, t−1 klein, t dalend met slot onder het midden van het lichaam van t−2).
- Trendfilter op het slot van t: long alleen als slot(t) > MA14 en slot(t) > MA200; short alleen als slot(t) < MA14 en slot(t) < MA200.

**3.5 Instap (K3).** Long: koopstop op de high van kaars t. Short: verkoopstop op de low van kaars t. De opdracht geldt alleen in de H1-bar t+1 (doorlopen op M30). Opent een M30-bar al voorbij het niveau, dan instap op die open. Niet geraakt: geen trade.

**3.6 Stop en doel.** Long: stop op de laagste low van t−2, t−1 en t; doel op instap + 2 × (instap − stop). Short gespiegeld. Minimale stop 1,00 USD, zoals test F en P; is de stop kleiner, dan geen trade. Geen tijdslimiet en geen dagslot: de trade loopt tot stop of doel (de bron noemt geen andere uitstap).

**3.7 Eén positie tegelijk.** Een signaal tijdens een open trade vervalt.

**3.8 Winrate** = aandeel trades met netto R > 0 (na kosten). R = netto resultaat in USD per ounce gedeeld door de stopafstand vanaf de werkelijke instap.

**3.9 Uitwerking voor het script (21 nov, na akkoord, vóór het bekijken van data).**
- In de M30-bar van de instap telt alleen de stop (raakt die bar na de instap de stop, dan verlies); het doel telt pas vanaf de volgende M30-bar. Dat werkt tegen de regel in, net als "stop en doel in één bar = stop".
- ATR(14) volgens Wilder op H1, waarde van de afgesloten bar; alleen gebruikt voor de stopafstand van de controlegroep.
- Handelsdag en "begin van de dag" in de uitdaging: brokerdatum (zie 2.5).
- Maximale drawdown in % (C3): over P1 met vast risico van $1.000 op $100.000 zonder herbeleggen, gemeten op afgesloten saldo tegen de hoogste stand ervoor.
- Gaat het slot van een trade over een weekend of feestdag, dan geldt de eerste open daarna (regel "opent voorbij de stop of het doel").

### Gemaakte keuzes (21 nov 2026)

| | Gekozen (beslissend) | Niet gekozen (alleen aanvullend gerapporteerd, wordt na de run niet geprobeerd als reparatie) | Waarom |
|---|---|---|---|
| K1 soort MA | A. Simpel (SMA 14 en SMA 200) | B. Exponentieel (EMA 14 en EMA 200) | "Moving average" zonder toevoeging is meestal simpel; MT5 en TradingView hebben SMA als standaard [aanname] |
| K2 patroon | A. Klassiek: lichaam midden ≤ 1/3 van kaars 1, kaars 3 sluit boven het midden van kaars 1 | B. Ruim: lichaam midden < lichaam kaars 1, kaars 3 sluit boven de open van kaars 2 | Gangbare leerboekdefinitie [aanname] |
| K3 geldigheid koopopdracht | A. Alleen de volgende H1-bar | B. Tot de stop eerst geraakt wordt, maximaal 5 H1-bars | "When the price goes higher than the third candle" leest als direct [aanname] |
| K4 wat telt als gehaald | A. Beide fasen (10% en daarna 5%), zoals de firm "geslaagd" bedoelt | B. Alleen fase 1 (10%) | Pas na fase 2 krijg je een rekening [aanname over wat de bron bedoelt] |

## 4. De drie vaste regels

**Kosten.** 0,40 USD per ounce round trip (spread plus slippage), gelijk aan test F en P [aanname]. Gevoeligheid: 0, 0,40 en 0,80 USD. De mediane spread uit de kolom SPREAD wordt alleen gerapporteerd.

**Volgorde.** Het pad loopt per M30-bar vanaf de instap. Raakt een bar stop en doel samen, dan telt het als stop. Opent een bar voorbij de stop of het doel, dan uitstap op die open. In de instapbar zelf telt alleen het deel na de instap niet apart: raakt de instap-M30-bar na de instap de stop, dan geldt die bar als stop (stop gaat voor).

**Controlegroep.** 10.000 runs, seed 31. Een willekeurig opeenvolgend proces, één positie tegelijk, zoals test F en P:
- na elke uitstap (of bij de start) een wachttijd in H1-bars, getrokken uit de wachttijden van de regel in dezelfde periode;
- dan instap op de open van de eerstvolgende H1-bar waarvan de vorige bar voldoet aan het filter van de nulmeting;
- stopafstand getrokken uit de stopafstanden van de regel (20 kwantielen, als veelvoud van de ATR(14) H1 op de instapbar), doel 2R; stop kleiner dan 1,00 USD: geen trade;
- dezelfde kosten en padregels.

Vergeleken wordt de gemiddelde netto R per trade.
- **Null A, beslissend:** alleen het trendfilter van 3.4, zonder patroon. Slot boven beide MA's: long; onder beide: short; anders geen instap. Toetst of het patroon iets toevoegt bovenop de trend.
- **Null B, aanvullend:** muntworp, long en short elk 50%, zonder filter.

Volgorde van kijken: eerst de controlegroep, dan de regel.

## 5. Periodes

| Run | Periode | Rol |
|---|---|---|
| P1 | 6 nov 2021 tot de laatste bar (5 nov 2026) | **Beslissend**. De "5 years of gold" van de bron [aanname: de bron eindigt rond de reel van 7 nov 2026] |
| P0 | Start bruikbare data (3.2) tot 5 nov 2021 | Aanvullend: dezelfde regel vóór de periode van de claim |
| P3 | per jaar | Verdeling over de jaren, niet beslissend |

## 6. De prop firm-simulatie (vast)

[geverifieerd, eigen site van firma A, 21 nov 2026] Regels van de standaarduitdaging in twee fasen, rekening $100.000: doel fase 1 10%, fase 2 5%, gehaald met alle posities gesloten; maximaal dagverlies 5% van het beginkapitaal onder het saldo aan het begin van de dag (dag 1: het beginkapitaal), op equity inclusief open verlies; maximaal verlies vast op $90.000, op equity; minimaal 4 handelsdagen per fase, een handelsdag is een dag (CE(S)T) waarop minstens één positie wordt geopend. De pagina noemt geen tijdslimiet [geverifieerd]; andere pagina's van de firm zeggen "unlimited" [geverifieerd].

[aanname, vertaling naar code]
- **Positie:** risico 1% van het beginsaldo ($1.000) per trade, zoals de bron. Ounces = 1.000 / stopafstand. Kosten per trade = ounces × 0,40 USD.
- **Dagverlies:** mislukt zodra het saldo inclusief open verlies (laagste koers per M30-bar bij long, hoogste bij short) $5.000 onder het saldo aan het begin van de handelsdag zakt.
- **Maximaal verlies:** mislukt zodra het saldo inclusief open verlies onder $90.000 zakt.
- **Doel:** fase gehaald op het eerste moment dat het afgesloten saldo het doel haalt én er minstens 4 handelsdagen met een instap in die fase zijn. Daarna start fase 2 met een nieuwe rekening van $100.000 op de volgende handelsdag (bij K4-A).
- **Trekking:** 1.000 uitdagingen, startdag willekeurig getrokken uit de handelsdagen van P1 (seed 31), met de trades van de regel vanaf die dag. Een uitdaging die na 1 jaar (365 kalenderdagen) of aan het eind van de data nog loopt, telt als "niet klaar", zoals de bron. Startdagen in het laatste jaar van P1 tellen niet mee.
- **Pass rate** = gehaald / 1.000, met 95%-interval (Wilson, met de kanttekening dat overlappende trekkingen niet onafhankelijk zijn). Daarnaast: gezakt, niet klaar, mediane duur tot gehaald.
- **C5 (beschrijvend):** dezelfde simulatie met trades van Null A, 2.000 runs.
- Geen inschrijfgeld, geen uitbetalingsregels.

## 7. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval (dagbootstrap) van de gemiddelde netto R per trade in P1 ligt onder 0 |
| C2 | De gemiddelde netto R per trade in P1 ligt niet boven percentiel 95 van Null A |
| C3 | Geen oordeel; alleen naast elkaar gezet |
| C4 | De bovengrens van het 95%-interval van de pass rate ligt onder 81% |
| C5 | Geen oordeel; alleen beschrijvend |

Valt C2, dan is het idee dood: niet repareren, niet optimaliseren, geen andere MA's, patroondefinities, filters of doelen proberen. Dat geldt ook voor de varianten die bij K1 tot K4 niet gekozen zijn. Onder 100 trades in P1: "onvoldoende trades".

Blijven C1 en C2 staan, dan rapporteer ik "niet gefalsifieerd", met de beperkingen, en niet "werkt".

## 8. Wat ik rapporteer, ongeacht de uitkomst

- Aantal patronen, hoeveel binnen het trendfilter, hoeveel koopopdrachten geraakt, hoeveel afvallen door de minimale stop, aantal trades, aandeel long.
- Winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor.
- Percentiel tegen Null A en Null B.
- Resultaat per jaar, de drie kostenniveaus, mediane stopafstand in USD tegenover de kosten.
- Langste reeks winsten en verliezen; maximale drawdown in R en in % bij 1% vast risico.
- Pass rate, gezakt, niet klaar, mediane duur, naast 81%, 1 op 8 en 155 dagen.
- P0 naast P1; C3 naast 512 trades, 43% en 7,5%.

## 9. Ruiscontrole vóór de echte data (vast)

24 synthetische reeksen: random walk met de beweeglijkheid van goud (15% per jaar), drift 0 en 8% per jaar, met 60 stappen per M30-bar (zoals test P, open beslissing 52) [aanname, gekozen vóór het zien van de data]. Vereist: gemiddeld percentiel tegen Null A tussen 35 en 65, hooguit 3 van 24 boven 95. Haalt het script dat niet, dan eerst de oorzaak zoeken en een nieuwe versie van dit document, vóór de echte data.

## 10. Volgende stap

1. Goedgekeurd op 21 nov (K1 tot K4 = A). SHA-256 van de NL- en EN-versie in `meetlog-morning-star-goud.md`.
2. Regels van de firm gecontroleerd op 21 nov (zie 6).
3. Script: zelftest (patroon tegen een tweede implementatie, uitdaging tegen een handberekening), ruiscontrole, datacontrole, dan run 01.
