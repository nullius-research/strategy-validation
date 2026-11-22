# Hypothese: noise-area intraday momentum (test R)

Datum: 21 november 2026 · Bron: YouTube-video van 14 november 2026 (een testkanaal), gebaseerd op een onderzoekspaper uit 2024 · Status: **versie 1.0, vooraf vastgelegd, keuzes K1 A, K2 A, K3 A, K4 C, K5 A gekozen door Erwin op 21 november 2026, nog geen echte koersdata geopend voor deze test**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, beschrijving en transcript van de video] De regel, door de video overgenomen uit het paper:
- Ruisband: voor elk tijdstip van de dag de gemiddelde absolute beweging vanaf de opening over de laatste 14 dagen. De band ligt rond de opening en wordt bij een gap verschoven: "If there was a gap overnight, the band starts at yesterday's close on that side."
- Elke 30 minuten vanaf 10:00 New Yorkse tijd: long boven de bovenband, short onder de onderband.
- Uit: "when the price falls back into the band or when it crosses the VWAP". Altijd plat bij het slot.
- Test van de video: CME-futures, minuutbars, januari 2020 tot oktober 2026, één contract, commissie en één tick slippage per instap en per uitstap.

[geverifieerd, beschrijving van de video] De uitkomsten die de video meldt:
- Nasdaq-futures: "1,564 trades, +6.8 points per trade after costs, t-statistic 2.6, 41% winners, every year 2020-2026 positive."
- "Random direction: 4 of 1,000 reached the real result."
- S&P 500-futures: "+0.5 points per trade, t-statistic about 1."
- Na het verschijnen van het paper (mei 2024): 8,4 punt per trade op 549 trades (transcript).

[geverifieerd, samenvatting op SSRN] Het paper zelf meldt op SPY, 2007 tot begin 2024: totaal 1.985% na kosten, 19,6% per jaar, Sharpe 1,33. Dat getal toetsen wij niet beslissend (zie K1).

[geverifieerd] Toetsbare claims (beslissend op de Nasdaq 100, keuze K1 A):

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | "+6.8 points per trade after costs" | Gemiddeld netto resultaat per trade in punten over P1 |
| C2 | De regel kiest betere momenten en richtingen dan toeval ("unlikely that this is just luck") | Echt resultaat tegen de controlegroep met willekeurig instapmoment en willekeurige richting (Null B) |
| C3 | "every year 2020-2026 positive" | Netto som per kalenderjaar in P1 |

Beschrijvend, niet beslissend: winrate 41%, aantal trades 1.564, de munttest op de richting (4 van 1.000), de S&P 500, de periode na het paper.

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd] Deze regel is al vaker openbaar getest: een onafhankelijke herhaling op SPY en ES, een tweede paper buiten de oorspronkelijke steekproef, het testkanaal zelf en een TradingView-script. Onze data overlapt grotendeels met die van de video (2020 tot oktober 2026). Dit is dus een herhaling op data van een andere bron, geen test op nieuwe data.
2. [geverifieerd, eerdere tests] Onze data is een CFD op de Nasdaq 100 (USTEC) met tickvolume, geen future met beursvolume. De VWAP wordt gewogen met tickvolume [aanname dat dit de echte VWAP benadert]. Gevoeligheid: VWAP zonder volume (alle minuten even zwaar).
3. [aanname] CFD-punten liggen dicht bij NQ-punten, maar niet precies gelijk (de future heeft een renteopslag). Voor een vergelijking per trade is dat verschil klein.
4. [geverifieerd, eerdere tests N en O] Onze vaste kosten op USTEC (spread plus 1 punt slippage per kant) zijn hoger dan die van de video (één tick van 0,25 punt per kant plus commissie). C1 kan dus vallen door de kosten alleen. Daarom rapporteren we ook het niveau van de video (K5 B) en zonder kosten, en zegt elke publicatie welk niveau beslist.
5. [geverifieerd, transcript] Volgens de video komt de winst uit een paar grote dagen ("If you take out the 10 best days ... drop to about $7,300"). Het resultaat is dus gevoelig voor enkele dagen. We rapporteren het resultaat zonder de 10 beste dagen.
6. [geverifieerd] De video beschrijft niet welke prijs de VWAP gebruikt, of de controle op de slotkoers van de minuut valt, en waar de order wordt gevuld. Die keuzes leggen we in 4 vast.

## 3. Keuzes (gekozen op 21 november 2026: K1 A, K2 A, K3 A, K4 C, K5 A, de vetgedrukte opties)

| Keuze | A | B | C |
|---|---|---|---|
| K1 · Beslissende claim en markt | **Nasdaq 100 (USTEC), de claim uit de video** | S&P 500 (US500), de claim uit het paper, pas vanaf 2017 te meten | Beide beslissend |
| K2 · Instap | **Alleen buiten de band, zoals de video het beschrijft** | Buiten de band én aan dezelfde kant van de VWAP, zoals het TradingView-script en het tweede paper het lezen | |
| K3 · Periode | **2 januari 2020 tot en met 5 november 2026 (einde van onze data)** | 2017 tot 2026 | |
| K4 · Controlegroep | Zelfde trades, munt op de richting (de test van de video) | Willekeurig instapmoment, munt op de richting, houdtijd uit de echte trades | **Beide, B beslissend** |
| K5 · Kosten | **Onze vaste methode: spread uit de data plus slippage per kant (1 punt op USTEC, 0,25 punt op US500), gevoeligheid 0, 1 en 2 keer** | Kostenniveau van de video: 0,25 punt slippage plus 0,125 punt commissie per kant, samen 0,75 punt per trade [aanname: commissie van ongeveer $2,50 per kant op één NQ van $20 per punt] | |

De niet-gekozen varianten van K1, K2 en K5 worden aanvullend gerapporteerd, niet beslissend.

## 4. Mechanische vertaling (vast na goedkeuring)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**4.1 Sessie.** Alleen de reguliere beurstijd, 9:30 tot 16:00 New Yorkse tijd, 390 minuutbars. De opening per dag zoals in test G, H en N: de sprong in tickvolume rond 16:30 servertijd. Een dag is geldig met minstens 90% van de 390 minuutbars. Halve handelsdagen vallen daardoor vanzelf af (zoals het script ze ook overslaat). Een minuutbar heet naar zijn begintijd: de bar van 9:59 sluit om 10:00.

**4.2 Ruisband.** Voor minuut t van de sessie (t = 0 voor de bar van 9:30) en geldige dag d:
- O_d = openingskoers van de bar van 9:30.
- C_d = slotkoers van de bar van 15:59.
- beweging(d, t) = |slot van bar t / O_d − 1|.
- σ_t op dag D = gemiddelde van beweging(d, t) over de 14 voorafgaande geldige dagen (dag D zelf telt niet mee).
- Bovenband_t = max(O_D, C_vorige) × (1 + σ_t); onderband_t = min(O_D, C_vorige) × (1 − σ_t). C_vorige is het slot van de voorgaande geldige dag.
- Breedtefactor 1, terugblik 14 dagen (vast, zoals paper, video en script). De eerste 14 geldige dagen van de data handelen niet (opwarmen); P1 begint pas na die 14 dagen, de opwarming valt in december 2019.

**4.3 VWAP.** Begint elke dag opnieuw bij de bar van 9:30. Prijs per minuut = (high + low + close) / 3, gewicht = tickvolume van die minuut. VWAP op controletijdstip = som(prijs × volume) / som(volume) over alle minuutbars die vóór dat tijdstip gesloten zijn.

**4.4 Controlemomenten.** 10:00, 10:30, ..., 15:30 (12 per dag). Op elk moment geldt de slotkoers P van de minuutbar die op dat moment sluit (bar t = 29 om 10:00, enzovoort), met σ_t van dezelfde bar.

**4.5 Signaal en uitstap op een controlemoment, in deze volgorde.**
- Long open: uit als P < max(bovenband, VWAP).
- Short open: uit als P > min(onderband, VWAP).
- Daarna, als er (nog of weer) geen positie is: long als P > bovenband, short als P < onderband (K2 A). Bij K2 B (aanvullend) moet P ook boven (long) of onder (short) de VWAP liggen.
- Een uitstap en een nieuwe instap op hetzelfde moment (omkeren) is toegestaan.
- Een positie die nog voldoet, blijft gewoon staan.

**4.6 Vullen.** Instap en uitstap op de openingskoers van de minuutbar direct na het controlemoment (om 10:00 dus de open van de bar van 10:00). Nooit op de slotkoers waarop het signaal is bepaald.

**4.7 Slot.** Een positie die om 16:00 nog openstaat, gaat dicht op de slotkoers van de bar van 15:59. Ook een instap om 15:30 mag; die gaat uiterlijk om 16:00 dicht.

**4.8 Positiegrootte.** Eén eenheid per trade, resultaat in indexpunten, zoals de video (één contract). De volatiliteitsdoelstelling en hefboom van het paper vallen buiten deze test; het jaarpercentage van het paper wordt dus niet gemeten.

**4.9 Resultaat.** Per trade in punten en in basispunten van de instapkoers, netto na kosten. Er is geen vaste stop, dus geen R.

## 5. De drie vaste regels

**Kosten.** K5 A: de spread uit de SPREAD-kolom op de instapminuut (in punten), plus slippage per kant (instap en uitstap): 1 punt op USTEC, 0,25 punt op US500, zoals test N en O [geverifieerd, README test N]. Gevoeligheid: slippage 0, 1 en 2 keer. Aanvullend K5 B: 0,75 punt per trade, zonder spread.

**Volgorde.** Het pad wordt minuut voor minuut doorlopen. Alle beslissingen vallen op controlemomenten en alle vullingen op de open van de volgende minuut; er zijn geen stops of doelen binnen een bar, dus de volgorde binnen een minuut speelt geen rol.

**Controlegroep.** 10.000 runs, seed 43. Percentiel van het echte gemiddelde netto resultaat per trade tegen de verdeling van de runs. Betrouwbaarheidsintervallen met bootstrap per handelsdag, ook 10.000 keer.
- **Null B, beslissend voor C2:** dezelfde geldige dagen in P1, dezelfde controlemomenten, dezelfde kosten. Een opeenvolgend proces: op elk controlemoment zonder open positie opent toeval een positie met kans p, richting met een eerlijke munt. De houdtijd in controlemomenten (1, 2, ...) wordt per trade getrokken uit de verdeling van de echte trades in P1; de uitstap valt op de open na dat controlemoment, of op het slot om 16:00 als dat eerder komt. p is zo gekozen dat het verwachte aantal trades gelijk is aan dat van de regel. Toetst of de ruisband betere momenten en richtingen kiest dan toeval met dezelfde blootstelling.
- **Null A, aanvullend (de test van de video):** elke echte trade met dezelfde instap en uitstap, de richting met een eerlijke munt.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 1.500 handelsdagen met minuutbars (alleen 9:30 tot 16:00 en een kleine nachtsprong), opgebouwd uit 60 stapjes per minuut zoals test G, H en N, zonder trend, zonder openingseffect en zonder momentum, met een vaste spread van 1 punt en willekeurig tickvolume. Seed 7. Beginkoers en jaarvolatiliteit als in test N [aanname].

Grens, gelijk aan de audit van 10 november: percentiel tegen Null B gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95. Ook Null A wordt op ruis gemeten en moet dezelfde grens halen. Haalt het script dat niet, dan eerst de oorzaak zoeken en een nieuwe versie van dit document, vóór de echte data.

Daarnaast vóór de ruiscontrole een zelftest: ruisband, VWAP en de beslisregel tegen een tweede, eenvoudige implementatie op een paar handgemaakte dagen (gap omhoog, gap omlaag, omkeren, slot om 16:00).

## 7. Data

[geverifieerd, bestandsnamen en datacontroles test G en N] USTEC M1, IC Markets, `Test\box-theory\USTEC_M1_201208060000_202611052200.csv`, loopt tot 5 november 2026. US500 M1, `Test\lce-supply-demand\US500_M1_201208060000_202611021049.csv`, echte minuutdata vanaf 21 maart 2017, spreadkolom vanaf 2019 gevuld, loopt tot 2 november 2026. Voor deze test is nog niets geopend.

Perioden:
- **P1, beslissend voor C1, C2 en C3:** USTEC, alle geldige sessies van 2 januari 2020 tot en met 5 november 2026.
- Aanvullend: US500 over dezelfde periode (tot 2 november 2026); USTEC 2017 tot en met 2019 (K3 B); USTEC vanaf 14 mei 2024 (het paper staat sinds die dag online [geverifieerd, SSRN]).

Datacontrole vóór de run, alleen metadata: aantal geldige sessies per jaar, verdeling van de gevonden openingsminuut, aandeel minuten met lege spread, minuten met tickvolume nul, eenheid van de spreadkolom op USTEC.

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval (dagbootstrap) van het gemiddelde netto resultaat per trade in P1 ligt onder 6,8 punt |
| C2 | Het echte gemiddelde netto resultaat in P1 ligt niet boven percentiel 95 van Null B |
| C3 | Minstens één kalenderjaar 2020 tot en met 2026 (2026 tot 5 november) heeft een negatieve netto som |

Valt C2, dan is het idee dood: niet repareren, niet optimaliseren, geen filters, andere terugblik of controle-interval proberen. Onder 100 trades in een periode of jaar staat in het rapport "onvoldoende trades".

## 9. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades en trades per dag, winrate (beschrijvend, tegen 41%), gemiddeld netto resultaat in punten en basispunten met 95%-interval, profit factor, percentiel tegen Null B en Null A, het resultaat zonder kosten, de drie slippageniveaus en K5 B, mediane houdtijd, gemiddelde winst en gemiddeld verlies, long en short apart, per jaar, de periode na het paper, het resultaat zonder de 10 beste dagen, de grootste daling van de opgetelde punten, K2 B, de VWAP zonder volume, US500 (K1 B) en USTEC 2017 tot en met 2019.

Titel volgens de vaste regel: geen percentage in de claim, dus het hoofdgetal: "+6.8 points per trade claimed", met onze meting ernaast. Geen namen van het paper, de video of het script in publicaties.

## 10. Volgende stap

1. Erwin keurt deze versie goed. SHA-256 in `meetlog-noise-area-momentum.md`. Engelse versie ernaast.
2. Script `noise_area.py`: zelftest uit 6, dan de ruiscontrole.
3. Datacontrole uit 7, dan run 01, controlegroep eerst.
