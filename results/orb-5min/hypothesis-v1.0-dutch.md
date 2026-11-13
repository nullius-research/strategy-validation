# Hypothese: 5-minuten opening range breakout op de S&P 500 (test H)

Datum: 13 november 2026 · Bron: blogpost van een aanbieder van handelsdata, 18 april 2026 (`claim-bron.md`, privé) · Status: **concept 1.0, 13 november 2026, nog niet goedgekeurd. Geen koersdata geopend voor deze test.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de eerste echte run verandert er niets; een nieuwe versie krijgt een nieuwe datum.

## 1. De claim

[geverifieerd, bron gelezen 13 nov 2026] Op de S&P 500-future (ES), 1 contract, over "6 months": 115 trades, winrate 72,17%, profit factor 1,623, netto 10.825 dollar. De bron zegt zelf dat de instellingen geoptimaliseerd zijn en dat de standaardinstellingen "won't perform like this". Kosten en slippage worden niet genoemd.

## 2. Toetsbare claims

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | 72,17% van de trades wint | Winrate met 95%-interval (Wilson) |
| C2 | De regel verdient geld (profit factor 1,623) | Gemiddeld netto resultaat per trade in R, met 95%-interval (bootstrap per dag); profit factor ter informatie |
| C3 | De richting van de uitbraak zegt iets (impliciet: "trade in the direction of the break") | Gemiddeld netto R tegen Null A: zelfde instap, richting per muntworp |

## 3. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De bron noemt de periode niet precies, en ook niet: aanraking of slotkoers als uitbraak, aantal trades per dag, sluittijd, kosten. Wij vullen dat in (paragraaf 4) en melden het bij elke uitkomst.
2. [geverifieerd, rekenkunde] Target 0,5 range tegen stop 1,0 range: zonder kosten is 66,7% winst nodig om quitte te spelen. Kleine kosten wegen zwaar, want een target van een halve range is vaak maar een paar punten.
3. [aanname] Wij meten op een CFD op de S&P 500 (US500, IC Markets), niet op de ES-future. Punten zijn vergelijkbaar, de prijs niet precies (basis, spread).
4. [geverifieerd, bron] De filters (range hooguit 0,55%, geen dinsdag, maximaal 14 punten verlies) zijn gekozen op dezelfde periode als de claim. Daarom is de periode van de claim zelf niet beslissend.

## 4. Mechanische vertaling (vast)

**4.1 Sessie.** Opening 9:30 New Yorkse tijd, bepaald zoals in test G (sprong in tickvolume rond 16:30 servertijd, speling 60 minuten voor zomertijdweken). Een dag telt alleen mee met minstens 90% van de 390 minuutbars.

**4.2 Range.** Hoogste high en laagste low van de eerste 5 minuutbars (9:30 tot 9:35). Range = high min low. Range 0: geen trade.

**4.3 Filters.** Geen trade als de range groter is dan 0,55% van de openingskoers. Geen trade op dinsdag (alle richtingen) [aanname: de bron spreekt zichzelf tegen, de kop zegt alle dinsdagen].

**4.4 Instap.** Vanaf 9:35 de eerste minuutbar met een high boven de range-high (long) of een low onder de range-low (short): instap op het range-niveau, als stoporder. Opent die bar al voorbij het niveau, dan instap op de open van die bar. Raakt dezelfde bar beide kanten, dan geen trade (volgorde onbekend), wel geteld. Hooguit één trade per dag [aanname]. Geen uitbraak vóór 15:55: geen trade.

**4.5 Stop.** De andere kant van de range, maar nooit verder dan 14 punten van de instap (het maximale verlies uit de bron) [aanname: 1 ES-punt = 1 US500-punt].

**4.6 Target.** Het range-niveau plus (long) of min (short) 0,5 keer de range [geverifieerd, bron: gemeten vanaf het uitbraakniveau].

**4.7 Uitstap.** Stop, target, of anders op het slot van de laatste sessiebar (16:00) [aanname: de bron noemt geen sluittijd].

**4.8 R.** 1 R = afstand van instap tot stop. Resultaat per trade in R, netto na kosten.

## 5. Data (vast)

US500 M1, IC Markets, eigen export (`US500_M1_201208060000_202611021049.csv`). Echte minuutdata vanaf 21 maart 2017; spreadkolom pas vanaf 2019 gevuld [geverifieerd, datacontrole 2 nov]. Een verse export tot de laatste handelsdag mag, als die vóór de run binnen is.

Datacontrole vóór de run, alleen metadata: aantal geldige sessies per jaar, verdeling van de gevonden openingsminuut, aandeel dagen met lege spread.

## 6. De drie vaste regels

**Kosten.** De spread uit de SPREAD-kolom op de instapbar, plus 0,25 punt slippage per kant (instap en uitstap) [aanname: één tick van de ES]. Gevoeligheid: slippage 0, 1 en 2 keer.

**Volgorde.** Minuut voor minuut. In de instapbar telt alleen de stop. Raakt een latere bar stop en target allebei, dan telt de stop.

**Controlegroep.**
- Null A (beslissend): dezelfde dagen, dezelfde instapminuut en instapprijs, maar de richting per muntworp; stop en target op dezelfde afstand, gespiegeld. 10.000 runs, seed 31. Gemeten: gemiddeld netto R. Percentiel van de echte waarde.
- Null B (aanvullend): dezelfde dagen, een willekeurige instapminuut tussen 9:35 en 15:30, richting per muntworp, dezelfde range-afstanden. 10.000 runs.

## 7. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 1.500 handelsdagen met minuutbars, opgebouwd uit 60 stapjes per minuut (zoals test G v1.1), zonder trend en zonder openingseffect, met een vaste spread van 0,5 punt. Seed 7.

Grens, gelijk aan de audit van 10 nov: percentiel tegen Null A gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95.

## 8. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | 1 jan 2019 tot en met 17 okt 2025 | **Beslissend**: vóór het venster waarop de bron optimaliseerde |
| P0 | 18 okt 2025 tot en met 17 apr 2026 | Nagemaakte claimperiode [aanname: de 6 maanden vóór de post]. Vergelijking met 115 trades en 72,17%. Niet beslissend |
| P2 | 18 apr 2026 tot de laatste dag | Na de post. Minder dan 100 trades: gemeld als onvoldoende |
| P3 | per jaar binnen P1 | Verdeling, niet beslissend |

## 9. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd in P1 als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate ligt onder 72,17% |
| C2 | De bovengrens van het 95%-interval van het gemiddelde netto R ligt onder 0 |
| C3 | Het gemiddelde netto R ligt niet boven percentiel 95 van Null A |

Na de run: geen andere ranges, targets, filters of sluittijden. Blijft een claim staan, dan "niet gefalsifieerd in deze meting", niet "werkt".

## 10. Wat ik rapporteer, ongeacht de uitkomst

De trechter: geldige dagen, na het rangefilter, na het dinsdagfilter, met uitbraak, beide kanten in één bar, trades. Per periode: trades, winrate (95%), gemiddeld netto R (95%), profit factor, aandeel stop, target en slot. Percentielen tegen Null A en Null B. De kostengevoeligheid. De jaartabel. De ruiscontrole.

## 11. Volgende stap

1. Goedkeuring (of aanpassing). SHA-256 in het meetlog.
2. Script `orb_control.py` op basis van test G, eerst de ruiscontrole uit 7.
3. Datacontrole uit 5, dan de run.
4. Code en data op GitHub vóór publicatie.
