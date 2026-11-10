# Hypothese: MA 9/21-kruising met 200 MA op goud (test F), versie 1.1

Datum: 9 november 2026 · Bron: een tradingvideo met artikel (15 nov 2025); bron met naam staat in de privéprojectbestanden · Status: **versie 1.1, 9 november 2026, goedgekeurd (optie A). Vervangt v1.0 alleen in de controlegroep (4), omdat v1.0 de ruiscontrole niet haalde (zie meetlog, niet gepubliceerd; uitkomst in noise_24sets_v1.0_failed.txt). Regels, periodes en drempels ongewijzigd. Nog geen koersdata bekeken**



Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, artikel] Goud (XAUUSD). Dagfilter: koers boven de 9 EMA op de daggrafiek, plus met de hand getekende vakken rond trage markt. Instap op 30 minuten: long als de 9 MA boven de 21 MA kruist, op de slotkoers van die kaars; de kaars ligt boven beide MA's; koers en beide MA's boven de 200 MA. Target 1,5 keer de stopafstand. Geen stop gegeven. Alleen long.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Winrate rond 58% op 100 trades in de "goede markt" | Winrate met 95%-interval |
| C2 | De regel verdient geld: rond +45% bij 1% risico, dus ongeveer +0,45R per trade vóór kosten | Gemiddelde netto R per trade met interval |
| C3 | De instap (kruising met kaars boven de MA's) kiest betere momenten dan toeval binnen dezelfde trend | Echt resultaat tegen de controlegroep |

## 2. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De 58% hoort bij trades die met de hand zijn uitgekozen (buiten de getekende vakken). Die vakken zijn niet na te maken. Deze test meet alleen het mechanische deel: dagfilter, kruising, 200 MA en stop. Een lagere winrate kan dus ook aan het weglaten van de handselectie liggen. Dat staat in elke publicatie.
2. [geverifieerd] De bron geeft geen stop. De stop is onze keuze (3.6), dezelfde als bij test A en D. Een andere stop geeft een ander resultaat; we proberen geen andere.
3. [geverifieerd, rekenkundig] Break-even bij 1,5R is 40% vóór kosten. Op een random walk zonder drift is 40% ook de verwachte winrate.
4. [aanname] Goud steeg sterk in 2024 en 2025. Een long-only regel krijgt daar wind mee. Daarom is de beslissende periode de tijd buiten 2024-2025, en is de controlegroep long binnen hetzelfde filter.
5. [geverifieerd, Wilson-interval] Ook als 58% de echte winrate is, ligt het 95%-interval over 100 trades tussen 48,2% en 67,2%.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen. Gekozen op 9 november 2026.

**3.1 Data.** `XAUUSD_M30_199804220000_202611052200.csv`, MT5-export, 9 nov 2026, SHA-256 c7d40c32a3d53f7ccfcc199b51d910daccaeafc2e6f996a0a9e1925aa684d7d2. Brokertijd. Dagbars worden uit de M30-bars gebouwd per brokerdatum.

**3.2 Bruikbare data.** De export loopt vanaf 1998, maar oude M30-data is vaak dun. De meting begint in de eerste kalendermaand waarin elke handelsdag minstens 40 M30-bars heeft. Dit is een controle op volledigheid, geen keuze op basis van koersen. Opwarmen: de eerste 300 M30-bars en 30 dagen na die start tellen niet mee.

**3.3 MA's.** EMA 9, EMA 21 en EMA 200 op de M30-slotkoers. Dagfilter: EMA 9 op de dagslotkoers.

**3.4 Dagfilter.** Op M30-bar t: het slot van de vorige afgesloten dag ligt boven de EMA 9 van die dag. De lopende dag doet niet mee, anders kijkt het filter vooruit.

**3.5 Signaal op M30-bar t.** Alle vijf tegelijk:
- EMA9(t) > EMA21(t) en EMA9(t-1) ≤ EMA21(t-1) (de kruising gebeurt op bar t);
- low(t) > max(EMA9(t), EMA21(t)) (de hele kaars ligt boven beide MA's, "not crossing them");
- slot(t) > EMA200(t);
- EMA9(t) > EMA200(t) en EMA21(t) > EMA200(t);
- dagfilter waar.

**3.6 Instap, stop en target.** Instap op het slot van bar t. Stop A: laagste low van de laatste 10 M30-bars tot en met t (5 uur), gelijk aan test A en D. Target: instap + 1,5 × (instap − stop). Minimale stop 1,00 USD; is de stop kleiner, dan geen trade (bij 0,40 USD kosten zou anders meer dan 40% van de stop naar kosten gaan).

**3.7 Uitstap.** Het pad wordt bar voor bar doorlopen vanaf bar t+1. Raakt één bar zowel stop als target, dan telt hij als stop. Opent een bar voorbij de stop (gat, bijvoorbeeld na het weekend), dan uitstap op de open van die bar. Opent hij voorbij het target, dan uitstap op het target. Posities lopen door over nacht en weekend. Open aan het eind van de data: sluiten op het laatste slot en apart melden.

**3.8 Eén positie tegelijk.** Een signaal tijdens een open trade vervalt.

## 4. De drie vaste regels

**Kosten.** 0,40 USD per ounce round trip (spread plus slippage) [aanname: een gangbare spread op XAUUSD ligt rond 0,20 tot 0,35 USD]. Gevoeligheid: 0, 0,40 en 0,80 USD. Aanvullend: de mediane spread uit de kolom SPREAD van de export, alleen gerapporteerd, niet beslissend.

**Volgorde.** Zie 3.7. Ook de instapbar t+1 zelf telt mee.

**Controlegroep (v1.1).** 10.000 runs, seed 23. Een willekeurig proces dat net als de regel door de tijd loopt, één positie tegelijk: na elke uitstap (of bij de start) een wachttijd, getrokken uit de wachttijden van de regel zelf in dezelfde periode; dan long op de eerstvolgende toegestane bar. Stopafstand getrokken uit de stopafstanden van de regel (20 kwantielen), target 1,5R, zelfde kosten, zelfde padregels (3.7). Het aantal trades volgt uit het proces en ligt lager dan bij de regel; vergeleken wordt de gemiddelde netto R per trade.
- **Null A, beslissend:** toegestane bars = dezelfde trendcontext (dagfilter waar, slot, EMA9 en EMA21 boven EMA200), zonder kruising en zonder kaarsregel. Toetst of de kruising iets toevoegt bovenop de trend.
- **Null B, aanvullend:** toegestane bars = alle bars. Laat zien hoeveel de trend zelf oplevert.

Waarom niet zoals v1.0 [geverifieerd, ruiscontrole 9 nov]: met willekeurige trades zonder overlap en stop A per bar scoorde de regel op 24 ruisreeksen in 13 gevallen boven percentiel 95. Oorzaken: grotere stops bij de regel (kosten wegen minder in R) en een voorkeur voor korte, vaker verliezende trades bij de trekking zonder overlap. Met de controlegroep van v1.1: gemiddeld percentiel 46,0, boven 95 in 0 van 24.

Een muntworp is hier niet de juiste nulmeting: de regel is alleen long, op een markt met opwaartse drift [geverifieerd, methode].

## 5. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P0 | 1 jan 2024 tot 14 nov 2025 | Vermoedelijke periode van de bron [aanname: de bron noemt geen datums]. Ter vergelijking, niet beslissend |
| P1 | Start bruikbare data (3.2) tot 31 dec 2023, plus 1 jan 2026 tot de laatste bar | **Beslissend**: buiten 2024-2025 |
| P2 | per jaar | Verdeling over de jaren, niet beslissend |

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate in P1 ligt onder 58% |
| C2 | De bovengrens van het 95%-interval van de gemiddelde netto R per trade in P1 ligt onder 0 |
| C3 | De gemiddelde netto R per trade in P1 ligt niet boven percentiel 95 van Null A |

Valt C3, dan is het idee dood: niet repareren, niet optimaliseren, geen andere MA's, stops of filters proberen. Onder 100 trades in P1: "onvoldoende trades".

Blijft C3 staan, dan rapporteer ik het als "niet gefalsifieerd", met de beperkingen, en niet als "werkt".

## 7. Wat ik rapporteer, ongeacht de uitkomst

Aantal signalen en hoeveel er afvallen door de minimale stop, aantal trades, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A en Null B, resultaat per jaar, de drie kostenniveaus, mediane stopafstand in USD tegenover de kosten, langste reeks verliezen, som van de beste 5% trades naast het totaal, en P0 naast de claim.

## 8. Volgende stap

1. SHA-256 van deze versie in `meetlog-ma-9-21-goud.md`.
2. Meetscript `ma921_control.py` eerst op 24 synthetische reeksen (random walk met de beweeglijkheid van goud, 15% per jaar, en drift 0 en 8% per jaar [aanname, gekozen vóór het zien van de data]). Daar moet de regel gemiddeld niet beter uitkomen dan Null A, en moeten de percentielen ongeveer gelijk verdeeld zijn. Pas dan de echte data.
