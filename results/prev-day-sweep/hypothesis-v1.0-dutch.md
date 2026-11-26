# Hypothese: vorige-dag-sweep met 1-uurstrend op de Nasdaq 100 (test S)

Datum: 23 november 2026 · Bron: YouTube-video van 17 november 2026 van een tradingkanaal, met een gratis sessie-indicator (open broncode) · Status: **versie 1.0, 23 november 2026, vooraf vastgelegd door de dagtaak, nog geen echte koersdata geopend voor deze test**

Keuzes: alle keuzes in 3 zijn "keuze dagtaak (aanbevolen optie), vooraf akkoord 22 nov 2026" (opdracht `opdracht-dagelijkse-test.md` v2). Na run 01 verandert er niets meer.

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, beschrijving en transcript van de video, scriptbeschrijving] De regel:
- Tijden in New Yorkse tijd. De handelsdag begint om 20:00. Londense kill zone 02:00 tot 05:00, New Yorkse kill zone 07:00 tot 11:00.
- Setup "previous-day sweep": "inside the London or New York kill zone price trades through yesterday's high/low and closes back inside." Door het hoog van gisteren en terug erin: short. Door het laag en terug erin: long.
- Bevestiging "higher-timeframe trend": "close vs an EMA on a higher timeframe (default 1h EMA 200), using the last completed higher-timeframe bar". Long alleen boven, short alleen onder.
- "Every signal enters at the next candle's open." Stop "past the sweep extreme, with a minimum of 0.5 × ATR 14". Uitstap: "hold to 16:00 New York".
- "One signal per setup per weekday. If both sides of a range are taken before a close back inside, that day is skipped."
- Kosten in de video: "Nasdaq / S&P CFD 0.01 % per side".

[geverifieerd, beschrijving van de video] De uitkomst die de video meldt:
- "Nasdaq 100 · previous-day sweep + 1 hour trend · 5 min · hold to 16:00 New York — profit factor 1.95 (290 trades; 1.95 on 2021–24, 1.96 on 2025–26). On 15 min: 2.20."
- "about 70 % of the trades lose", in het transcript "71% of these trades lost".
- "without the 5 best days the Nasdaq setup is close to break even" (transcript: profit factor "about 1.1"), "the longest losing streak was 18 trades".
- Transcript: zonder trendfilter profit factor 1,11 op de oude data en 0,84 op de nieuwe; 2024 als geheel verlieslatend; januari tot september 2026 33 trades, 5 winnaars, -23 R.
- De instellingen zijn gekozen uit 26.825 backtests op 2021-2024 en één keer gecontroleerd op 2025-2026.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | "profit factor 1.95" na kosten | Profit factor in R, netto, over P1 |
| C2 | De sweep met trendfilter is een voorsprong ("The edge is real") | Gemiddeld netto R per trade tegen de controlegroep met willekeurig instapmoment in dezelfde kill zone en willekeurige richting (Null B) |
| C3 | "1.95 on 2021–24, 1.96 on 2025–26": het houdt stand op de jaren waarop het gekozen is én op de nieuwe jaren | Profit factor netto per deelperiode |

Beschrijvend, niet beslissend: aantal trades (290 in 2021-2026), aandeel verliezers (ongeveer 70%), profit factor zonder de 5 beste dagen (ongeveer 1,1), langste verliesreeks (18), 2024 negatief, januari tot september 2026, de variant op 15 minuten (2,20), het kostenniveau van de video, de controlegroep met de trend als richting (Null T, zie 5).

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd, transcript] De instelling is gekozen uit 26.825 combinaties. Ook al is 2025-2026 apart gecontroleerd, de keuze van markt, setup, bevestiging, timeframe en uitstap is op dezelfde jaren gemaakt. Een deel van het resultaat kan uit die keuze komen. Onze test op data van een andere bron, met een controlegroep, is daarom de kern.
2. [geverifieerd, transcript] De maker zegt zelf dat de winst uit een paar grote trenddagen komt. Het resultaat is dus gevoelig voor enkele dagen. We rapporteren het zonder de 5 beste dagen.
3. [geverifieerd] De Pine-broncode is voor deze test niet uitgelezen; de regels komen uit de scriptbeschrijving en het transcript. Waar die niet eenduidig zijn (welk "gisteren", wanneer een niveau "genomen" is, wat er gebeurt als de trend op de terugkeerkaars niet klopt), leggen we in 4 een keuze vast. Een verschil met het script kan daaruit komen.
4. [geverifieerd, eerdere tests N, O, R] Onze data is een CFD op de Nasdaq 100 (USTEC, IC Markets) met tickvolume. De video gebruikte volgens de beschrijving ook een Nasdaq-CFD, maar van een andere aanbieder [aanname, welke aanbieder staat er niet].
5. [aanname] Onze kosten (spread uit de data plus 1 punt slippage per kant) liggen rond het niveau van de video (0,01% per kant is ongeveer 2 punt per kant bij een koers van 20.000). We rapporteren beide.
6. [geverifieerd, test R] De server van de data staat het hele jaar op New Yorkse tijd + 7 uur. Dat is gecontroleerd voor de opening om 9:30; voor de nachturen nemen we hetzelfde aan [aanname].

## 3. Keuzes (keuze dagtaak, aanbevolen optie vetgedrukt, vooraf akkoord 22 nov 2026)

| Keuze | A | B |
|---|---|---|
| K1 · Beslissende claim, markt en timeframe | **De claim van de maker: Nasdaq 100 (USTEC), 5 minuten, vorige-dag-sweep + 1-uurstrend, vasthouden tot 16:00** | Daarnaast de 15-minutenvariant (2,20) beslissend |
| K2 · Periode | **P1 = 2 januari 2020 tot en met 5 november 2026 (einde van onze data); P0 = 2013 tot en met 2019, aanvullend** | P1 = 2021 tot en met 2026, precies het venster van de claim |
| K3 · Kosten | **Onze vaste methode: spread uit de data op de instapminuut plus 1 punt slippage per kant** | Kostenniveau van de video: 0,01% van de koers per kant, zonder spread |
| K4 · Controlegroep | **Null B beslissend (willekeurig instapmoment in dezelfde kill zone van dezelfde dag, munt op de richting, zelfde stopafstand); Null A en Null T aanvullend** | Null A beslissend |
| K5 · Openingstijden | **Vaste tijden op de klok (server = New York + 7), geen detectie uit tickvolume (audit 21 nov)** | |

De niet-gekozen varianten van K1, K2 en K3 worden aanvullend gerapporteerd, niet beslissend. Het venster 2021-2026 (K2 B) wordt altijd apart gemeld, omdat de 290 trades van de claim daarover gaan.

## 4. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**4.1 Tijd.** Servertijd = New Yorkse tijd + 7 uur, het hele jaar (zie 2.6). Een bar heet naar zijn begintijd. New York 20:00 = server 03:00; 02:00 = 09:00; 07:00 = 14:00; 11:00 = 18:00; 16:00 = 23:00.

**4.2 Bars.** Vijfminutenbars uit de minuutbars van de data, uitgelijnd op de klok (:00, :05, ...). Uurbars op dezelfde manier, uitgelijnd op het hele uur. Een bar bestaat als er minstens één minuutbar in valt.

**4.3 Handelsdag.** Handelsdag D loopt van 20:00 New Yorkse tijd op de kalenderdag vóór D tot 20:00 op dag D (server 03:00 tot 03:00). Alleen handelsdagen D van maandag tot en met vrijdag kunnen een trade geven (de dag van maandag begint zondag 20:00). Een handelsdag is geldig als minstens 90% van de minuten van 02:00 tot 16:00 New Yorkse tijd (840 minuten) een minuutbar heeft. Ongeldige dagen (feestdagen, halve dagen) geven geen trade.

**4.4 Gisteren.** Hoog en laag van gisteren (PDH, PDL) = hoogste high en laagste low van alle minuutbars van de laatste eerdere handelsdag met minstens 600 minuutbars in zijn venster van 20:00 tot 20:00. Voor maandag is dat meestal vrijdag.

**4.5 Genomen.** Een niveau is genomen bij de eerste vijfminutenbar van dag D (vanaf 20:00) met high > PDH (voor het hoog) of low < PDL (voor het laag). Daarna bestaat dat niveau die dag niet meer. Een sweep telt alleen als die eerste keer binnen een kill zone valt: een bar met begintijd 02:00 tot en met 04:55 (Londen) of 07:00 tot en met 10:55 (New York). Is het niveau eerder genomen (in Azië, tussen de zones), dan geeft die kant die dag geen sweep.

**4.6 Terug erin.** Na het nemen (de bar zelf telt mee) is de triggerbar de eerste vijfminutenbar in dezelfde kill zone met slot < PDH (na een sweep van het hoog) of slot > PDL (na een sweep van het laag). Komt er in die kill zone geen slot terug erin, dan geeft deze sweep geen trade. Alleen deze eerste terugkeer telt: klopt de trend daar niet, dan geeft deze sweep geen trade.

**4.7 Beide kanten.** Zijn op het moment van de triggerbar (bij zijn slot) PDH én PDL op dag D allebei genomen, waar en wanneer ook, dan is de dag voor deze setup overgeslagen: geen trade en geen latere trade.

**4.8 Trend.** EMA 200 op de slotkoersen van de uurbars (alle uren, ook 's nachts), alfa 2/201, gestart met het gemiddelde van de eerste 200 slotkoersen. Op de triggerbar geldt de EMA van het laatste uur dat bij het slot van de triggerbar al volledig is afgesloten. Long alleen als het slot van de triggerbar boven die EMA ligt, short alleen als het eronder ligt.

**4.9 Eén per dag.** Hoogstens één trade per handelsdag voor deze setup: de eerste triggerbar die aan 4.6 tot en met 4.8 voldoet.

**4.10 Instap.** Op de openingskoers van de vijfminutenbar direct na de triggerbar (de open van de eerste minuutbar daarin).

**4.11 Stop.** ATR 14 = Wilder-gemiddelde van de true range van de vijfminutenbars (doorlopend over de dagen), waarde op de triggerbar. Sweepextreem = laagste low (long) of hoogste high (short) van de bars vanaf de nemingsbar tot en met de triggerbar. Stopafstand d = max(|instap − sweepextreem|, 0,5 × ATR) met de stop aan de verliezende kant: long stop = instap − d, short stop = instap + d. Geen extra tick.

**4.12 Pad en uitstap.** Het pad wordt minuut voor minuut gevolgd vanaf de instapminuut. Raakt een minuutbar de stop (low ≤ stop bij long, high ≥ stop bij short), dan uit op de stop, of op de open van die minuut als die al voorbij de stop ligt. Anders uit op het slot van de laatste minuutbar vóór 16:00 New Yorkse tijd. Geen doel, dus "stop en doel in één bar" komt niet voor.

**4.13 Resultaat.** R per trade = (uitstap − instap) × richting − kosten, gedeeld door d. Profit factor = som van de positieve netto R gedeeld door de absolute som van de negatieve netto R (één R risico per trade). Ook in punten.

## 5. De drie vaste regels

**Kosten.** K3 A: de spread uit de SPREAD-kolom op de instapminuut (eenheid 0,01, in punten, zoals test R), plus 1 punt slippage per kant. Gevoeligheid: slippage 0, 1 en 2 keer, en zonder kosten. Aanvullend K3 B: 0,01% van de instapkoers per kant, zonder spread. Is de spread op de instapminuut 0 of leeg (vooral vóór 2019), dan geldt de mediane spread van dat kalenderjaar; P1 heeft dat bijna nooit [aanname, controle in de datacontrole].

**Volgorde.** Pad minuut voor minuut (4.12). Signalen alleen op gesloten vijfminutenbars.

**Controlegroep.** 10.000 runs, seed 43. Percentiel van het echte gemiddelde netto R per trade tegen de verdeling van de runs; betrouwbaarheidsintervallen met bootstrap per handelsdag, ook 10.000 keer.
- **Null B, beslissend voor C2:** voor elke echte trade in P1 één toevalstrade op dezelfde dag en in dezelfde kill zone: instap op de open van een willekeurige vijfminutenbar van 02:05 tot en met 05:00 (Londen, 36 mogelijkheden) of van 07:05 tot en met 11:00 (New York, 48 mogelijkheden), richting met een eerlijke munt, dezelfde stopafstand d in punten, dezelfde uitstap om 16:00, dezelfde kosten. Toetst of de sweep met trendfilter betere momenten en richtingen kiest dan toeval met dezelfde blootstelling.
- **Null A, aanvullend:** elke echte trade met dezelfde instap, stop en uitstap, de richting met een eerlijke munt.
- **Null T, aanvullend:** als Null B, maar de richting volgt de trend (slot van de vorige vijfminutenbar tegen de EMA 200 van het laatste afgesloten uur). Toetst of de sweep iets toevoegt aan alleen de trend volgen in dezelfde kill zone.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 1.500 handelsdagen (alleen weekdagen, 24 uur per dag, geen pauze), minuutbars opgebouwd uit 60 stapjes per minuut, zonder trend, zonder sessie-effect, met een vaste spread van 1 punt. Beginkoers 15.000, volatiliteit vergelijkbaar met de Nasdaq 100 (ongeveer 1,2% per dag) [aanname]. Seed 7. 2.000 runs per set.

Grens, gelijk aan de eerdere tests: percentiel tegen Null B gemiddeld tussen 35 en 65, hooguit 2 van 24 boven 95 (opdracht v2). Ook Null A en Null T worden op ruis gemeten en moeten dezelfde grens halen. Haalt het script dat niet, dan eerst de oorzaak zoeken en een nieuwe versie van dit document (hoogstens twee herstelrondes), vóór de echte data.

Daarnaast vóór de ruiscontrole een zelftest: handgemaakte dagen (sweep van het laag met trend omhoog, zelfde met trend omlaag, niveau eerder genomen, beide kanten genomen, geen terugkeer in de zone, stop geraakt, minimale stop 0,5 ATR, uitstap om 16:00) en een tweede, eenvoudige implementatie die op nepdagen precies dezelfde trades moet geven.

## 7. Data

[geverifieerd, `data/README.md` en eerdere tests] USTEC M1, IC Markets, `USTEC_M1_201208060000_202611052200.csv` (SHA-256 begint met 714b4cc0), servertijd, loopt tot 5 november 2026. Voor deze test is nog niets geopend.

Perioden:
- **P1, beslissend voor C1, C2 en C3:** handelsdagen van 2 januari 2020 tot en met 5 november 2026.
- C3 gebruikt de deelperioden van de claim: 2021 tot en met 2024, en 1 januari 2025 tot en met 5 november 2026.
- Aanvullend: het venster 2021 tot en met 5 november 2026 (aantal trades tegen 290), P0 2013 tot en met 2019, de 15-minutenvariant (zelfde regels op vijftienminutenbars) in P1.

Datacontrole vóór de run, alleen metadata: aantal geldige handelsdagen per jaar, minuutbars per dag, ontbrekende uren 's nachts, aandeel minuten met spread 0, mediane spread per jaar, en of de stilte rond de dagpauze op server 00:00 tot 01:00 (New York 17:00 tot 18:00) valt.

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval (dagbootstrap) van de netto profit factor in P1 ligt onder 1,95 |
| C2 | Het echte gemiddelde netto R per trade in P1 ligt niet boven percentiel 95 van Null B |
| C3 | De netto profit factor in 2021-2024 of in 2025-2026 is 1,0 of lager |

Valt C2, dan is het idee dood: niet repareren, niet optimaliseren, geen andere bevestiging, kill zone, uitstap of timeframe proberen. Onder 100 trades in een periode, deelperiode of groep staat in het rapport "onvoldoende trades".

## 9. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades (P1, 2021-2026 tegen 290, per jaar, Londen en New York apart, long en short apart), aandeel verliezers (tegen ongeveer 70%), gemiddeld netto R met 95%-interval, profit factor met 95%-interval, percentiel tegen Null B, Null A en Null T, zonder kosten, slippage 0, 1 en 2 keer, K3 B, profit factor zonder de 5 beste dagen, langste verliesreeks, grootste daling in R, gemiddelde stopafstand in punten, januari tot september 2026, de 15-minutenvariant, P0.

Titel volgens de vaste regel: "profit factor 1.95 claimed" met onze meting ernaast. Geen namen van het kanaal, de video of de indicator in publicaties.

## 10. Volgende stap

1. Opslaan, SHA-256 in `meetlog-prev-day-sweep.md`, commit vóór de data. Engelse versie ernaast.
2. Script `sweep_test.py`: zelftest, ruiscontrole.
3. Datacontrole uit 7, dan run 01, controlegroep eerst.
