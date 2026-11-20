# Hypothese: breakout van support en resistance op goud (test P), versie 1.0

Datum: 20 november 2026 · Bron: strategieboek van een EA-verkoper (sep 2026), details privé · Status: **versie 1.0, 20 november 2026. Keuzes K1-B, K2-A, K3-B en K4-B door de onderzoeker gemaakt op 20 nov; tekst goedgekeurd door de onderzoeker op 20 nov. Daarna, vóór het bekijken van data, de uitwerking in 3.9 toegevoegd. Nog geen koersdata bekeken voor deze test.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, PDF p. 62-65 en 76-77] De bron noemt de breakout van support en resistance "the G.O.A.T. of trading systems" en schrijft "it works". De werkwijze in woorden:
- belangrijke niveaus, gezocht over meerdere timeframes, waar de koers eerder keerde;
- instap als de koers het niveau breekt, bevestigd door een slot voorbij het niveau ("touching the level is not breaking it");
- stop net terug binnen het gebroken niveau;
- stop en target die meebewegen met de beweeglijkheid van de markt, "let winners run";
- intraday op goud (XAUUSD), H1;
- verder filters op volume, tijd van de dag en volatiliteit, zonder precieze regels.

[geverifieerd, PDF p. 12] Getallen van de EA van de bron (backtest 2004-2024, vaste 0,1 lot op 100K): winrate 69%, profit factor 2,13, maximaal 3 verliezen op rij, ongeveer 500 trades per jaar. De regels van die EA zijn niet openbaar [geverifieerd].

Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Een breakout van S/R op goud verdient geld | Gemiddelde netto R per trade met 95%-interval |
| C2 | De breakout kiest betere momenten dan toeval ("captures big moves") | Echt resultaat tegen de controlegroep |
| C3 | Winrate 69%, PF 2,13, max 3 verliezen op rij | Alleen beschrijvend naast onze meting, geen oordeel (zie 2.1) |

## 2. Zwakke plekken, vooraf benoemd

1. [geverifieerd] Wij testen een openbare, vooraf vastgelegde vertaling van de beschreven werkwijze, niet de EA van de bron. Een andere uitkomst dan 69% of PF 2,13 kan dus aan onze vertaling liggen. Daarom is C3 alleen beschrijvend, en zegt elke publicatie dat het een reconstructie is (zoals test J).
2. [geverifieerd] Volume laten we weg: de M30-export heeft alleen tickvolume, en de bron geeft geen regel.
3. [geverifieerd, logboek] Breakout-regels zijn al drie keer gemeten zonder edge: Donchian (artikel 1), volume breakout (Null Test 03) en de 5-min opening range breakout (test H, percentiel 18,7). Nieuw hier: goud, niveaus uit eerdere keerpunten op H4 en D1, intraday.
4. [aanname] Goud steeg sterk in 2025. Een breakout-regel gaat in een stijgende markt vaker long en krijgt dan wind mee zonder dat de timing iets toevoegt. Daarom ligt de beslissende periode vóór 2025 (5), en houdt de beslissende controlegroep dezelfde verhouding long en short aan als de regel (4).
5. [aanname] Brokertijd is waarschijnlijk GMT+2 of GMT+3. Dagslot en het aanvullende tijdfilter zijn daarom in brokertijd.

## 3. Mechanische vertaling

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Data.** `XAUUSD_M30_199804220000_202611052200.csv`, dezelfde MT5-export als test F, SHA-256 c7d40c32a3d53f7ccfcc199b51d910daccaeafc2e6f996a0a9e1925aa684d7d2 (wordt vóór de run opnieuw gecontroleerd). H1-, H4- en D1-bars worden uit de M30-bars gebouwd per brokeruur, blok van 4 uur vanaf middernacht, en brokerdatum. Het pad van elke trade wordt op M30 doorlopen.

**3.2 Bruikbare data.** Zelfde controle op volledigheid als test F: de meting begint in de eerste kalendermaand waarin elke handelsdag minstens 40 M30-bars heeft. Opwarmen: de eerste 30 handelsdagen na die start tellen niet mee.

**3.3 ATR.** ATR(14) volgens Wilder op H1, waarde van de afgesloten bar.

**3.4 Niveaus (K1-B).** Keerpunten op H4 en op D1. Een weerstand is de high van een bar j die hoger is dan de highs van de twee bars ervoor en de twee bars erna (strikt hoger). Een steun is de low van een bar j die lager is dan de lows van de twee bars ervoor en de twee bars erna (strikt lager). Het niveau is actief vanaf de eerste H1-bar die begint na het slot van bar j+2. Een niveau is pas bekend als de bars die het bevestigen afgesloten zijn. Er wordt dus niet vooruit gekeken. Een niveau vervalt na zijn eerste breakout (gebruikt) of na 20 handelsdagen.

**3.5 Signaal op H1-bar t.**
- Long: slot(t) > weerstand en slot(t−1) ≤ weerstand (eerste slot erboven).
- Short: slot(t) < steun en slot(t−1) ≥ steun.
- Breken meerdere niveaus tegelijk, dan telt het één keer.
- Geen signaal op de laatste H1-bar van de brokerdag.
- Geen tijdfilter (K2-A). Aanvullend gerapporteerd: alleen signaalbars die openen tussen 09:00 en 21:00 brokertijd.

**3.6 Instap en stop.** Instap op het slot van bar t. Stop net terug binnen het niveau: long op weerstand − 0,5 × ATR, short op steun + 0,5 × ATR. Minimale stop 1,00 USD, zoals test F; is de stop kleiner, dan geen trade.

**3.7 Uitstap (K3-B, meelopende stop).** Geen target. A = ATR(14) H1 op bar t, vast voor de hele trade. Na het slot van elke M30-bar vanaf de instap: long, stop = max(stop, hoogste M30-slot sinds instap − 2 × A); short, stop = min(stop, laagste M30-slot sinds instap + 2 × A). De stop schuift nooit terug. De nieuwe stop geldt vanaf de volgende M30-bar. Uiterlijk uitstap op het slot van de laatste M30-bar van de brokerdag (intraday, zoals de bron). R = netto resultaat in USD gedeeld door de eerste stopafstand (instap tot stop uit 3.6).

**3.8 Eén positie tegelijk.** Een signaal tijdens een open trade vervalt. Een niveau dat tijdens een open trade breekt, vervalt ook.

**3.9 Uitwerking voor het script (20 nov, na akkoord, vóór het bekijken van data).**
- Breken meerdere niveaus in dezelfde richting tegelijk, dan hoort de stop bij het niveau dat het dichtst bij het slot ligt (long: de hoogste gebroken weerstand, short: de laagste gebroken steun). Breken in dezelfde bar een weerstand en een steun, dan geen trade.
- De meelopende stop wordt ook bijgewerkt na het slot van de instapbar zelf (hoogste slot sinds instap begint bij de instapprijs).
- Wachttijden in de controlegroep worden geteld in H1-bars, van de H1-bar waarin de vorige trade sloot tot de H1-bar van de instap.
- Stopafstand in de controlegroep: getrokken als veelvoud van de ATR (stopafstand van de regel gedeeld door zijn ATR bij instap, 20 kwantielen) en toegepast met de ATR op de instapbar van de controletrade. Reden: goud steeg in de meetperiode van ongeveer 400 naar ruim 2.000 USD, dus een stopafstand in dollars uit het ene jaar past niet in het andere [aanname, keuze]. Is die stop kleiner dan 1,00 USD, dan geen trade, net als bij de regel.
- Winrate = aandeel trades met netto R > 0 (na kosten).

### Gemaakte keuzes (20 nov 2026)

| | Keuze | Niet gekozen (wordt na de run ook niet geprobeerd) |
|---|---|---|
| K1 niveau | B. Keerpunten H4 en D1 | A. Hoog en laag vorige dag · C. Hoog en laag van 5 dagen |
| K2 tijdfilter | A. Geen filter (09:00-21:00 alleen aanvullend) | B. Filter beslissend |
| K3 uitstap | B. Meelopende stop 2 × ATR | A. Vast target 2R |
| K4 richting controlegroep | B. Zelfde verhouding long en short als de regel (beslissend) | A. Muntworp 50/50 (aanvullend) |

## 4. De drie vaste regels

**Kosten.** 0,40 USD per ounce round trip (spread plus slippage), gelijk aan test F [aanname]. Gevoeligheid: 0, 0,40 en 0,80 USD. De mediane spread uit de kolom SPREAD wordt alleen gerapporteerd.

**Volgorde.** Het pad loopt per M30-bar vanaf de bar na de instap. Binnen een bar geldt de stop zoals die na het slot van de vorige bar stond; pas na het slot van de bar schuift hij mee. Raakt de bar de stop, dan uitstap op de stop. Opent een bar voorbij de stop, dan uitstap op de open van die bar. Er is geen target, dus de regel "stop en target in één bar telt als stop" komt niet voor.

**Controlegroep.** 10.000 runs, seed 23. Een willekeurig proces dat net als de regel door de tijd loopt, één positie tegelijk, zoals test F v1.1:
- na elke uitstap (of bij de start) een wachttijd, getrokken uit de wachttijden van de regel in dezelfde periode;
- dan instap op het slot van de eerstvolgende H1-bar die niet de laatste van de brokerdag is;
- stopafstand getrokken uit de stopafstanden van de regel (20 kwantielen, als veelvoud van de ATR, zie 3.9);
- richting volgens de nulmeting hieronder;
- dezelfde meelopende stop (3.7, met de ATR op de eigen instapbar), dagslot, kosten en padregels.

Vergeleken wordt de gemiddelde netto R per trade.
- **Null A, beslissend:** elke trade long met kans p, short met kans 1 − p, waarbij p het aandeel long van de regel in dezelfde periode is. Toetst alleen de timing.
- **Null B, aanvullend:** muntworp, long en short elk 50%.

Volgorde van kijken: eerst de controlegroep, dan de regel.

## 5. Periodes

| Run | Periode | Rol |
|---|---|---|
| P1 | Start bruikbare data (3.2) tot 31 dec 2024 | **Beslissend**. Valt samen met de backtestperiode van de bron (2004-2024) |
| P2 | 1 jan 2025 tot de laatste bar (5 nov 2026) | Aanvullend: de periode van de live-claim (+105% in 2025) |
| P3 | per jaar | Verdeling over de jaren, niet beslissend |

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de gemiddelde netto R per trade in P1 ligt onder 0 |
| C2 | De gemiddelde netto R per trade in P1 ligt niet boven percentiel 95 van Null A |
| C3 | Geen oordeel; alleen naast elkaar gezet |

Valt C2, dan is het idee dood: niet repareren, niet optimaliseren, geen andere niveaus, filters, stops of uitstappen proberen. Dat geldt ook voor de varianten die bij K1 tot K4 niet gekozen zijn. Onder 100 trades in P1: "onvoldoende trades".

Blijven C1 en C2 staan, dan rapporteer ik "niet gefalsifieerd", met de beperkingen, en niet "werkt".

## 7. Wat ik rapporteer, ongeacht de uitkomst

- Aantal signalen, hoeveel afvallen door de minimale stop, aantal trades, aandeel long.
- Winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor.
- Percentiel tegen Null A en Null B.
- Resultaat per jaar, de drie kostenniveaus, mediane stopafstand in USD tegenover de kosten.
- Langste reeks verliezen, met hoe vaak de controlegroep een even korte of kortere reeks heeft.
- Som van de beste 5% trades naast het totaal.
- P2 naast de live-claim; C3 naast 69%, 2,13 en 3.

## 8. Volgende stap

1. Goedgekeurd op 20 nov. SHA-256 van de NL- en EN-versie in `meetlog-sr-breakout.md`.
2. Meetscript `sr_breakout.py` eerst op 24 synthetische reeksen: random walk met de beweeglijkheid van goud (15% per jaar), drift 0 en 8% per jaar, zoals test F [aanname, gekozen vóór het zien van de data]. Daar moet de regel gemiddeld niet beter uitkomen dan Null A, en moeten de percentielen ongeveer gelijk verdeeld zijn. Pas dan de echte data.
