# Hypothese: Stochastic + RSI + MACD

Datum: 5 november 2026 · Bron: een YouTube-video van een tradingkanaal (geüpload maart 2021) die de strategie 100 keer test. Gelezen via het automatische Engelse transcript (266 segmenten) · Status: **vooraf vastgelegd, versie 1.0, goedgekeurd door Erwin op 5 november 2026, nog geen echte data bekeken**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run verandert er niets. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst staan.

Naamregel: deze versie noemt geen kanaal of maker. Verder gelijk aan het interne document dat vóór de run is vastgelegd.

## 1. Wat de bron belooft

[geverifieerd, transcript] De regels zoals de bron ze geeft:
- Stochastic geeft het hoofdsignaal. Long: wacht tot de K- en de D-lijn allebei oversold zijn.
- RSI als trendfilter: de niveaus in de instellingen op 50 zetten. Boven 50 alleen kopen, onder 50 alleen verkopen.
- MACD als bevestiging: daarna wachten tot de MACD-lijn boven de signaallijn kruist.
- Daarbij mogen beide stochastic-lijnen sinds het oversold-moment nog niet overbought zijn geweest.
- Short: het spiegelbeeld.
- Stop: long onder de dichtstbijzijnde swing low, short boven de dichtstbijzijnde swing high.
- Target: 1,5 keer de stop.
- Backtest: EURUSD, 30 minuten, startkapitaal 1.000, 2% risico per trade, hefboom 200.
- Eén positie tegelijk; signalen tijdens een open trade vallen weg.

[geverifieerd, transcript] Gerapporteerde uitkomst: 100 trades in 134 dagen, winrate 56%, langste reeks 5 winsten en 3 verliezen, winst 280,41 dollar, ongeveer 28% op 1.000.

[geverifieerd, transcript] Na de backtest noemt de bron als verbetering: de stop beperken tot 0,15%. Dat zat niet in de 100 trades.

[geverifieerd] Niet in de bron: instellingen van stochastic, RSI en MACD, de grenzen voor oversold en overbought, de definitie van een swing low, de periode van de 134 dagen, kosten.

Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Winrate 56% bij target 1,5R | Winrate met 95%-interval |
| C2 | Ongeveer 28% winst op 100 trades bij 2% risico, dus ongeveer +0,14R per trade | Gemiddelde netto R per trade |
| C3 | De combinatie kiest betere momenten dan toeval | Echt resultaat tegen de controlegroepen |

## 2. Zwakke plekken die vóór de test al zichtbaar zijn

1. [geverifieerd, rekenkundig] Break-even bij 1,5R is een winrate van 40%, vóór kosten. Een winrate van 56% betekent +0,40R per trade.
2. [geverifieerd, rekenkundig] De twee getallen van de bron passen niet bij elkaar. 56 winsten van 1,5R en 44 verliezen van 1R is +40R. Bij 2% risico per trade is dat ongeveer +80% zonder herbelegging, niet 28%. Een winst van 28% is +14R, wat bij 1,5R hoort bij een winrate van ongeveer 45,6%. Mogelijke verklaringen, geen van alle gecontroleerd: kosten of slippage, een risico per trade dat anders was dan 2%, targets of stops die in de praktijk anders lagen, of een rekenfout. [aanname: welke het is, valt uit de video niet vast te stellen]
3. [geverifieerd, rekenkundig, binomiaal] Bij 100 trades en 56% loopt het 95%-interval van ongeveer 46% tot 66%.
4. [geverifieerd] Instellingen, niveaus en de swing low zijn niet mechanisch gedefinieerd. Elke vertaling hieronder is mijn keuze, met reden.
5. [geverifieerd] De bron testte één periode van 134 dagen in of vóór begin 2021. Deze meting gebruikt 2022 tot 2026. Een verschil kan dus ook aan de periode liggen; dat staat in elk rapport.
6. [aanname, niet nagemeten] Een openbare TradingView-implementatie (2021) meldt dat de regels nauwelijks signalen geven, in crypto. Hier wordt het aantal signalen per maand gerapporteerd.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Instrument en tijd.** Hoofdtest: EURUSD op 30 minuten, zoals de bron. M30-bars worden gemaakt uit de M15-exports (twee bars per halfuur, beginnend op :00 en :30 servertijd). Periode: alles wat de export bevat. Aanvullend en niet beslissend: dezelfde regels op de andere acht paren uit de M15-set.

**3.2 Indicatoren, allemaal op de slotkoers, tot en met de signaalbar.**
- Stochastic: %K 14, %K-smoothing 1, %D 3, grenzen 20 en 80. Dit zijn de standaardwaarden van TradingView; de bron noemt geen getallen.
- RSI 14 (Wilder), grens 50, zoals de bron.
- MACD 12, 26, 9, de standaard.

**3.3 Oversold en overbought.** Oversold op bar s: K(s) < 20 en D(s) < 20, op dezelfde bar ("both the K and D lines"). Overbought op bar s: K(s) > 80 en D(s) > 80. Dezelfde definitie aan beide kanten, zodat "nog niet overbought" en "overbought" hetzelfde betekenen.

**3.4 Setup.**
- Long-setup gaat aan op de eerste oversold-bar s. Een volgende oversold-bar houdt hem aan.
- De long-setup vervalt bij de eerste overbought-bar na s. Op die bar gaat de short-setup aan.
- Short-setup: spiegelbeeld.
- Maximale wachttijd: één handelsdag, dus 48 M30-bars vanaf en met bar s. Een trigger op bar t telt alleen als t ≤ s + 47. Bars in het weekend bestaan niet en tellen dus niet mee. De bron noemt geen limiet; dit is een keuze van Erwin (5 nov 2026, vóór de eerste run), omdat een setup zonder limiet dagen open kan blijven. Een rollend venster van 48 bars en niet het einde van de kalenderdag, zodat elke setup even lang leeft. Een nieuwe oversold-bar zet het venster opnieuw op 48.
- Een setup wordt opgebruikt bij de eerste geldige trigger, ook als er op dat moment al een positie open staat (die trigger valt dan weg).

**3.5 Trigger (op de slotkoers van bar t, met t ≥ s).**
- Long: long-setup aan, MACD(t-1) ≤ signaal(t-1) en MACD(t) > signaal(t), RSI(t) > 50.
- Short: short-setup aan, MACD(t-1) ≥ signaal(t-1) en MACD(t) < signaal(t), RSI(t) < 50.

**3.6 Entry.** Openingskoers van bar t+1. Nooit op de slotkoers van de signaalbar, omdat de kruising pas vaststaat als die bar gesloten is.

**3.7 Stop ("nearest swing low").**
- Swing low: een M30-bar waarvan de low lager is dan de lows van de 2 bars ervoor en de 2 bars erna (5-bar fractal). Een swing low op bar j is pas bekend na sluiting van bar j+2, dus alleen swings met j+2 ≤ t tellen.
- Long-stop: de low van de meest recente bekende swing low onder de entrykoers, gezocht in de laatste 50 bars tot en met t. Short: spiegelbeeld met swing highs boven de entry.
- Geen buffer voorbij de swing; de kosten zitten in de R.
- Geen swing gevonden, of stop minder dan 5 pips van de entry: geen trade. Les uit de LCE-test: te krappe stops worden opgegeten door de kosten [geverifieerd in die test].

**3.8 Target en uitstap.** Target 1,5 keer de afstand entry tot stop. Geen break-even, geen gedeeltelijke winst, geen tijdslimiet. Wat aan het eind van de data nog openstaat, sluit op de laatste slotkoers.

**3.9 Eén positie tegelijk**, zoals de bron [geverifieerd, transcript].

**3.10 Variant met stoplimiet, vooraf vastgelegd en niet beslissend.** De bron raadt na de backtest aan de stop te beperken tot 0,15%. Uitleg hier: is de stopafstand groter dan 0,15% van de entrykoers, dan komt de stop op 0,15% en het target op 1,5 keer die afstand. Het moment en de richting van de trades blijven gelijk. Apart gerapporteerd. Dit is geen reparatie achteraf: het staat hier vóór de run.

## 4. De drie vaste regels

**Kosten.** 1,2 pip round trip per trade, de vaste aanname uit eerdere tests [geverifieerd, Overdracht Nullius Research]. Gevoeligheid: 0, 1,2 en 2,0 pip.

**Volgorde.** Het pad wordt bar voor bar op M15 doorlopen, fijner dan het signaal. Raakt één M15-bar zowel stop als target, dan telt hij als stop.

**Controlegroepen.** 10.000 runs per controle, seed 19. Bootstrap per handelsdag.
- **Null A, beslissend (muntworp):** dezelfde entrymomenten als de echte trades, richting willekeurig, zelfde stopafstand gespiegeld, zelfde 1,5R, zelfde kosten. Voor FX de juiste nulmeting, omdat long en short symmetrisch zijn [geverifieerd, methode].
- **Null B, aanvullend (stochastic en MACD bovenop het RSI-filter):** per echte trade een willekeurige M30-bar op hetzelfde paar en in dezelfde maand waarop RSI aan dezelfde kant van 50 lag, richting volgens RSI, zelfde stopregel als 3.7. Let op: in de MACD-test was Null B scheef in het voordeel van de regel, ook op ruisdata [geverifieerd, meetlog MACD]. Daarom wordt Null B hier eerst op de ruissets gedraaid en wordt de verdeling op ruis naast het echte percentiel gezet.

## 5. Data

[geverifieerd, Bollinger-test] De M15-set bevat negen paren: EURUSD, EURJPY, GBPUSD, GBPJPY, USDJPY, USDCHF, USDCAD, NZDUSD, EURGBP, van augustus 2022 tot augustus 2026, één broker.
[aanname] De ruwe bestanden staan in `C:\Users\evand\Documents\trading`, zoals bij de MACD-test. Nog niet geopend voor deze test.
[aanname] Bij dezelfde frequentie als de bron (100 trades in 134 dagen) geeft vier jaar EURUSD ruwweg 1.000 trades. Het werkelijke aantal blijkt pas uit de run.

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate ligt onder 56% |
| C2 | De bovengrens van het 95%-interval van de gemiddelde netto R ligt onder +0,14R |
| C3 | Het echte resultaat (gemiddelde netto R, EURUSD) ligt niet boven percentiel 95 van Null A |

C2 gebruikt de lagere van de twee getallen uit de bron (+0,14R uit de 28%, niet +0,40R uit de winrate), zodat de toets niet strenger is dan de bron zelf.

Valt C3, dan is het systeem dood: niet repareren, niet optimaliseren, geen andere instellingen, niveaus of stopregels. Minder dan 100 trades op EURUSD: het rapport zegt "onvoldoende trades" en er volgt geen oordeel. Per aanvullend paar onder 100 trades: "onvoldoende" voor dat paar.

## 7. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades per paar en per maand, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A en Null B (plus Null B op ruis), resultaat per jaar, aandeel van de beste 5% trades, de drie kostenniveaus, de mediane stopafstand in pips tegenover de kosten, het aantal signalen dat afviel door geen swing of een stop onder 5 pips, en de variant met stoplimiet.

## 8. Volgende stap

1. Goedgekeurd door Erwin op 5 november 2026, met de wachttijd van één handelsdag. Het document ligt vast.
2. Meetscript `srm_control.py` schrijven (deels uit `macd_control.py`) en eerst draaien op synthetische random-walk-data (M15, 4 jaar, negen paren). Daar moet "dood" uitkomen, en Null B op ruis wordt vastgelegd. Pas dan de echte data.
3. Daarna optie C (MACD, stop 1,5 ATR, target 1 ATR); die vraagt een export van EURNZD M15.
