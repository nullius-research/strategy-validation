# Hypothese: Triple RSI op SPY (test I)

Datum: 14 november 2026 · Bron: artikel, Substack-post, video en Instagram-post van een website voor strategie-onderzoek · Status: **concept 1.0, 14 november 2026, nog niet goedgekeurd. Geen koersdata geopend voor deze test.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de eerste echte run verandert er niets; een nieuwe versie krijgt een nieuwe datum.

## 1. De claim

[geverifieerd, bronnen gelezen 14 nov 2026] Regels: RSI(5) onder 30; RSI(5) daalt voor de derde dag op rij; RSI(5) lag drie handelsdagen eerder onder 60; slot boven het 200-daags gemiddelde; kopen op het slot. Verkopen op het slot als RSI(5) boven 50 kruist. Alleen long, SPY. Geen stop, geen target, geen kosten genoemd.

Er zijn twee versies van de uitkomst:

| Versie | Bron | Periode | Trades | Winrate | Gemiddeld per trade | Profit factor |
|---|---|---|---|---|---|---|
| A | artikel en Substack, feb 2026 | "since 1993" | 103 | 90% | 1,2% | 4 |
| B | video, sep 2026 | "from 1993 until today" | 83 | "approximately 90%" | "almost 1.4%" | niet genoemd |

## 2. Toetsbare claims

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | 90% van de trades wint | Winrate met 95%-interval (Wilson) |
| C2 | Gemiddeld 1,2% winst per trade (versie A); bijna 1,4% (versie B) | Gemiddeld netto rendement per trade in procent, met 95%-interval (bootstrap per trade) |
| C3 | Profit factor 4 (versie A) | Profit factor netto, met 95%-interval (bootstrap per trade) |
| C4 | De drie RSI-voorwaarden kiezen betere instapdagen dan toeval binnen het trendfilter (impliciet: "high-probability entry points") | Gemiddeld netto rendement per trade tegen Null A |

## 3. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De bron toont de hele SPY-geschiedenis sinds 1993. Er is dus geen SPY-periode die de bron niet kon zien, behalve de dagen na de laatste publicatie. Reproductie van de getallen bewijst daarom weinig; C4 (tegen de controlegroep) beslist.
2. [geverifieerd, rekenkunde] Bij ongeveer 100 trades loopt het 95%-interval rond 90% van ongeveer 83% tot 95%. C1 valt pas als de gemeten winrate onder ongeveer 83% ligt.
3. [aanname, beredeneerd] Een uitstap zonder stop op een index met opwaartse drift geeft ook bij willekeurige instap vaak een hoge winrate. Hoge winrate alleen zegt weinig.
4. [geverifieerd] De twee versies spreken elkaar tegen (103 tegen 83 trades, langere periode met minder trades). Wij toetsen beide getallen; de regels zijn voor beide gelijk.
5. [geverifieerd, logboek] Sterk verwant aan test E (RSI(2)-pullback, niet gefalsifieerd). De uitkomsten zijn niet onafhankelijk.
6. [aanname] Rond 100 trades zit precies op onze grens. Elke subgroep (per decennium, na publicatie) heeft er minder: die melden we als onvoldoende.

## 4. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**4.1 Markt en data.** SPY dagkoersen van Yahoo Finance via het browserpaneel, vanaf de eerste handelsdag (29 januari 1993) tot de laatste afgesloten dag vóór de run. Signalen en rendementen op de slotkoers zonder dividendcorrectie ("close"). De dividendgecorrigeerde slotkoers ("adjclose") alleen als gevoeligheid.

**4.2 RSI(5).** Wilder-RSI met periode 5 op de slotkoers (afvlakking met alpha 1/5), de standaard in Amibroker. Opwarmperiode: de eerste 250 handelsdagen tellen niet mee.

**4.3 SMA 200.** Eenvoudig gemiddelde van de laatste 200 slotkoersen, tot en met de signaaldag.

**4.4 Signaal op dag t.** Alle vier tegelijk:
- RSI(t) < 30
- RSI(t) < RSI(t-1) < RSI(t-2) < RSI(t-3) (drie dalingen op rij)
- RSI(t-3) < 60
- slot(t) > SMA200(t)

**4.5 Instap.** Op het slot van dag t.

**4.6 Uitstap.** Op het slot van de eerste dag na de instap waarop RSI(5) boven 50 kruist: RSI van de dag ervoor hooguit 50, RSI van die dag boven 50. Geen stop, geen target, geen tijdslimiet. Open aan het eind van de data: sluiten op het laatste slot en apart melden.

**4.7 Eén positie tegelijk.** Een nieuw signaal tijdens een open trade vervalt.

## 5. De drie vaste regels

**Kosten.** 2 basispunten round trip per trade, gelijk aan Buy the Dip en test E. Gevoeligheid: 0, 2 en 4 bp.

**Volgorde.** Instap en uitstap op slotkoersen. De regel kent geen stop of target binnen de dag, dus het pad binnen de dag doet niet mee [geverifieerd, regels]. Wel gemeten per trade: de diepste tussentijdse daling op slotkoersen, omdat zonder stop het risico daar zit.

**Controlegroep.** 10.000 runs, seed 37.
- **Null A, beslissend:** willekeurige instapdagen uit de dagen met slot boven de SMA200, evenveel trades als de regel, één positie tegelijk. Elke nep-trade krijgt de looptijd van een echte trade (de echte looptijden, geschud). Toetst of de drie RSI-voorwaarden betere dagen kiezen dan een willekeurige dag in dezelfde trend, met dezelfde tijd in de markt.
- **Null B, aanvullend:** zoals Null A, maar met de eigen uitstapregel (RSI(5) kruist boven 50), zoals Null A van test E. Bij een instap met RSI al boven 50 wacht die nep-trade op een daling en herstel; de looptijd kan dan sterk afwijken.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 8.400 handelsdagen (ongeveer 33 jaar, zodat elke set rond de 100 trades kan geven), willekeurige wandeling met dagrendementen zonder geheugen, drift 0,03% en volatiliteit 1,2% per dag [aanname: ruwweg SPY]. Seed 7.

Grens, gelijk aan de audit van 10 nov: percentiel tegen Null A gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95.

## 7. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | 29 jan 1993 tot en met de laatste dag | **Beslissend** voor C1 tot en met C4 |
| P0a | 29 jan 1993 tot en met 20 feb 2026 (datum Substack-post) | Reproductie versie A: komen we bij 103 trades, 90%, 1,2%, PF 4? Niet beslissend |
| P0b | 29 jan 1993 tot en met 18 sep 2026 (datum video) | Reproductie versie B: 83 trades, ongeveer 90%, bijna 1,4%. Niet beslissend |
| P2 | per decennium binnen P1 | Verdeling. Onder 100 trades: onvoldoende |
| P3 | S&P 500-index (^GSPC), 3 jan 1950 tot 28 jan 1993 | Buiten de bron: dezelfde regels vóór SPY bestond. Aanvullend, niet beslissend |

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd in P1 als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate ligt onder 90% |
| C2 | De bovengrens van het 95%-interval van het gemiddelde netto rendement ligt onder 1,2% (versie A); apart gemeld tegen 1,4% (versie B) |
| C3 | De bovengrens van het 95%-interval van de profit factor ligt onder 4 |
| C4 | Het gemiddelde netto rendement per trade ligt niet boven percentiel 95 van Null A |

Na de run: geen andere RSI-periodes, drempels, filters of uitstappen. Blijft een claim staan, dan "niet gefalsifieerd in deze meting", niet "werkt".

## 9. Wat ik rapporteer, ongeacht de uitkomst

De trechter: dagen boven de SMA200, dagen met RSI onder 30, met drie dalingen, met RSI(t-3) onder 60, signalen, vervallen tijdens een open trade, trades. Per periode: trades, winrate (95%), gemiddeld netto rendement (95%), profit factor (95%), slechtste trade, diepste tussentijdse daling, gemiddelde looptijd, tijd in de markt, en kopen en vasthouden over dezelfde periode. Percentielen tegen Null A en Null B. Kostengevoeligheid en de versie met dividendcorrectie. De ruiscontrole.

## 10. Volgende stap

1. Erwin keurt goed (of past aan). SHA-256 in het meetlog.
2. Script `triple_rsi_control.py` op basis van test E (`rsi2_control.py`), eerst de ruiscontrole uit 6.
3. Data ophalen via het browserpaneel, datacontrole (alleen metadata), dan de run.
4. Code en data op GitHub vóór publicatie.
