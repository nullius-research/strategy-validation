# Hypothese: MACD-signalen met ATR-stop (1,5 ATR) en ATR-target (1 ATR)

Datum: 5 november 2026, aangepast 6 november 2026 (21 paren) · Status: **versie 1.0, goedgekeurd op 6 november 2026 (ATR vast vanaf de signaalbar, swap niet meegerekend), vóór de eerste run op echte data**

Bron: een open-source strategiescript op een grafiekplatform (augustus 2020), de video waarin de maker de uitkomst presenteert, en een openbare spreadsheet van de maker met winrates per paar en signaal. Naam en links staan in de privé projectbestanden (besluit 2 nov 2026: geen namen in publicaties).

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run verandert er niets. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst staan.

## 1. Wat de bron belooft

[geverifieerd, video en scriptpagina] "we've hit the 90% WinRAte mark on the Euro New Zealand Dollar chart". Dagelijkse grafiek, "3 year period", "28 different graphs", vijf MACD-signalen. Stop 1,5 x ATR, target 1 x ATR.

[geverifieerd, transcript] "if it is over 60 [%] i am convinced that the strategy i am testing can be really profitable". Gemiddelde winrate over 28 paren: Reversal 59,57%, MACD Line zero cross 62,54%, Signal Line zero cross 64,25% ("our winner").

[geverifieerd, spreadsheet] EURNZD, MACD Line zero cross: 94,12%. Hoogste cel van 140 (28 paren x 5 signalen). Laagste cel 23,08%. De gemiddelden in de sheet zijn ongewogen gemiddelden van de 28 winrates per paar.

[geverifieerd, rekenkundig] 94,12% = 16/17. Dat de cel op 17 trades rust, is [aanname]: 32/34 geeft hetzelfde, maar 34 nulkruisingen van de MACD-lijn in 2,6 jaar dagdata is onwaarschijnlijk.

Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | EURNZD, MACD Line ZC: winrate 94,12% ("90%") | Winrate met 95%-interval, zelfde periode en daarna |
| C2 | MACD Line ZC over 28 paren: 62,54% | Winrate over alle trades, met interval |
| C3 | Signal Line ZC over 28 paren: 64,25%, de beste | Idem |
| C4 | Boven 60% is "really profitable": de signalen kiezen betere momenten dan toeval | Gemiddelde netto R tegen een muntworp (Null A) |

## 2. Zwakke plekken die vóór de test al zichtbaar zijn

1. [geverifieerd, rekenkundig] Target 1 ATR, stop 1,5 ATR. Break-even winrate vóór kosten: 1,5 / (1 + 1,5) = **60%**. De grens van de bron ("over 60 = convinced") is precies break-even zonder kosten.
2. [geverifieerd, wiskundig: kans op +a vóór -b bij een driftloze random walk is b/(a+b)] Zonder enige voorspellende waarde haalt deze stop en target al ongeveer **60%** winrate. De 62,54% en 64,25% liggen daar dus net boven. Discrete dagbars, gaten en de regel "stop en target in één bar telt als stop" kunnen dat basisniveau verlagen [aanname, wordt gemeten op ruisdata].
3. [geverifieerd, binomiaal] Bij een echte kans van 60% is de kans op 16 of meer winsten in 17 trades 0,21%. Maar 94,12% is het maximum van 140 cellen, vaak met minder dan 30 trades per cel [aanname over de aantallen]. Het hoogste getal uit veel kleine steekproeven ligt vanzelf hoog. Dit wordt gemeten door de 140 cellen te herhalen op ruisdata.
4. [geverifieerd, broncode] De beschrijving zegt dat bij het target 50% wordt genomen en de stop naar break-even gaat. **De code doet dat niet**: `strategy.exit` sluit de hele positie op het target of de stop. De winrates in de sheet komen dus uit de code zonder scaling out [aanname: de sheet is met deze code gemaakt; dat zegt de video].
5. [geverifieerd, broncode] `timeFilter = year > 2020 - 3`: trades pas vanaf 1 januari 2018. De "3 jaar" is tot de publicatie (aug 2020) ongeveer 2,6 jaar.
6. [geverifieerd, broncode] Geen commissie, spread of slippage ingesteld. [aanname] Standaard rekent het grafiekplatform dan nul kosten.
7. [geverifieerd, broncode] `strategy.entry` in tegengestelde richting draait een open positie om. Een tegengesteld signaal sluit dus ook een trade. Een trade telt in het grafiekplatform als winst als hij met winst sluit [aanname over de definitie van "percent profitable"].
8. [aanname] Wat het grafiekplatform doet als target en stop in één dagbar vallen, hangt af van zijn aanname over het pad binnen de bar. Hier telt dat als stop (vaste regel), en het pad wordt op H1 gevolgd.

## 3. Mechanische vertaling (vast)

Alles hieronder is **[aanname]**: keuzes om de code naar een meting te vertalen. Waar de code iets vastlegt, volg ik de code.

**3.1 Instrument en tijd.** Dagbars (D1) van 21 van de 28 paren uit de spreadsheet: EURGBP, EURAUD, EURNZD, EURUSD, EURCAD, EURCHF, GBPAUD, GBPNZD, GBPUSD, GBPCAD, GBPCHF, AUDUSD, NZDUSD, NZDCAD, NZDCHF, USDCHF, NZDJPY, CHFJPY, EURJPY, USDJPY, GBPJPY. Bron: MT5-export (IC Markets EU, demo-account).

Niet meegenomen: AUDNZD, AUDCAD, AUDCHF, USDCAD, CADCHF, CADJPY, AUDJPY. Bij deze server hebben ze pas data vanaf 2 jan 2025, ook na een tweede export [geverifieerd, datacontrole 5 en 6 nov]. Besluit 6 nov 2026, vóór de eerste run: door met 21 paren (optie B). Elk rapport noemt dit als beperking.

**3.2 Perioden.**
- Periode R (replicatie, niet beslissend): 1 jan 2018 tot en met 14 aug 2020, de periode van de bron volgens de code.
- Periode T (toets, beslissend): 15 aug 2020 tot en met het einde van de export. Deze data heeft de bron niet gezien.
- Indicatoren mogen opwarmen op data vóór de periode.

**3.3 Indicatoren** (zoals de code): MACD 12, 26, 9 met EMA op de slotkoers. ATR 14 volgens Wilder (RMA van de true range), zoals `atr()` in het script.

**3.4 Signalen** (zoals de code, op de slotkoers van dagbar t):
- MACD Line ZC: long als MACD van ≤ 0 naar > 0 gaat, short als MACD van ≥ 0 naar < 0 gaat.
- Signal Line ZC: hetzelfde met de signaallijn.
- Continuation, Reversal, Histogram: zoals de code, aanvullend gerapporteerd, niet beslissend.
- `crossover(a, b)` = a(t) > b(t) en a(t-1) ≤ b(t-1). `crossunder` gespiegeld.

**3.5 Entry.** Openingskoers van dagbar t+1. [aanname: dat is wat het grafiekplatform standaard doet bij `strategy.entry` zonder `process_orders_on_close`]

**3.6 Stop en target.** ATR(14) op de signaalbar t, vast voor de hele trade. Stop 1,5 ATR, target 1 ATR van de entrykoers. Afwijking van de code: in het script wordt `strategy.exit` elke bar opnieuw aangeroepen met de ATR van die bar, waardoor de niveaus kunnen verschuiven [aanname over het gedrag van het script]. Een vaste ATR is eenduidig en gebruikelijk; het verschil wordt in periode R zichtbaar als afwijking van de sheet.

**3.7 Uitstap.** Target, stop, of een tegengesteld signaal (sluit op de opening van de volgende dagbar en opent de omgekeerde trade, zoals de code). Een signaal in dezelfde richting als een open trade doet niets. Geen tijdslimiet. Open aan het einde van de data: sluit op de laatste slotkoers.

**3.8 Eén positie per paar.**

**3.9 Winst.** Een trade telt als winst als de netto uitkomst in R groter is dan 0. R = de stopafstand (1,5 ATR). Een trade op target is +0,667R min kosten.

## 4. De drie vaste regels

**Kosten.** 1,2 pip round trip per trade [geverifieerd, vaste aanname uit eerdere tests]. Gevoeligheid: 0, 1,2 en 3,0 pip (crosses als GBPNZD hebben bredere spreads [aanname]). Swap (financiering over nacht) wordt niet meegerekend [aanname, beperking die in elk rapport staat; trades lopen vaak meerdere dagen].

**Volgorde.** Het pad wordt bar voor bar op H1 doorlopen, waar H1-data er is. Raakt één H1-bar zowel stop als target, dan telt hij als stop. Waar alleen D1 bestaat: dezelfde regel per dagbar. Het aandeel trades zonder H1-pad wordt gerapporteerd.

**Controlegroepen.** 10.000 runs per controle, seed 23. Bootstrap per handelsdag.
- **Null A, beslissend (muntworp):** dezelfde entrymomenten en ATR-afstanden als de echte trades, richting willekeurig, zelfde stop, target en kosten, zelfde pad. Voor FX de juiste nulmeting [geverifieerd, methode].
- **Ruiscontrole vooraf:** script eerst op synthetische random-walk-data (D1 en H1, 28 paren, 9 jaar, 24 sets). Daar moet "dood" uitkomen, en daar wordt gemeten (a) welke winrate deze stop en target op ruis halen en (b) hoe hoog de hoogste van 140 cellen op ruis komt.

## 5. Data

[geverifieerd, `datacontrole-export-1.md`] Export met `ExportFX_D1_H1.mq5`. De 21 paren hebben D1 vanaf jan 2010 (GBPNZD vanaf mei 2010) en H1 vanaf jan 2015 (EURCHF vanaf 19 jan 2015). Geen dubbele of ongeldige bars; gaten langer dan 4 dagen alleen vóór 2018.

## 6. Wanneer is het idee dood (vooraf)

Beslissend is periode T, alle 21 paren samen, per signaal (MACD Line ZC en Signal Line ZC). De drempels van C2 en C3 blijven de gemiddelden van de bron over 28 paren.

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate op EURNZD (MACD Line ZC, periode T) ligt onder 90%. Minder dan 100 trades: "onvoldoende", wel gerapporteerd |
| C2 | De bovengrens van het 95%-interval van de winrate (MACD Line ZC, periode T, alle paren) ligt onder 62,54% |
| C3 | Idem voor Signal Line ZC onder 64,25% |
| C4 | Het gemiddelde netto R (periode T, alle paren) ligt niet boven percentiel 95 van Null A. Getoetst per signaal; dood als het voor beide signalen geldt |

C1 gebruikt 90%, het getal uit de kop, niet 94,12%, zodat de toets niet strenger is dan de bron.

Valt C4, dan is het systeem dood: niet repareren, niet optimaliseren, geen andere ATR-factoren, signalen of filters. Ook de scaling out uit de beschrijving wordt niet achteraf toegevoegd; die zat niet in de code die de cijfers maakte.

## 7. Wat ik rapporteer, ongeacht de uitkomst

Per signaal en periode: trades per paar, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A. De spreadsheet van de bron naast onze periode R per cel (105 cellen: 21 paren x 5 signalen). Winrate op ruisdata naast de echte. De hoogste cel op ruis naast 94,12%. De drie kostenniveaus. Aandeel trades zonder H1-pad. Resultaat per jaar.

## 8. Volgende stap

1. Het document wordt goedgekeurd of aangepast. Daarna ligt het vast (SHA-256 in de meetlog).
2. Export gedaan (5 en 6 nov 2026).
3. Meetscript `macdatr_control.py` op ruisdata (28 synthetische paren, zodat de hoogste cel van 140 vergelijkbaar is met de spreadsheet), dan pas de echte data.
