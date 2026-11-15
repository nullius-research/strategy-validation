# Hypothese: UT Bot Alerts op Nasdaq 5 minuten (test K)

Datum: 15 november 2026 · Bron: video van een tradingkanaal over een van de populairste indicatoren op TradingView (bron met naam privé) · Status: **versie 1.1, goedgekeurd op 15 november 2026, na gezakte ruiscontrole van versie 1.0. Alleen de controlegroep verandert (paragraaf 5, zie 11). Versie 1.0 (SHA-256 3ec64d8c...) blijft bewaard. De regel is nog niet op koersdata gedraaid. De Nasdaq-data is dezelfde export als bij test G; daar is hij voor een andere regel gebruikt.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de eerste echte run verandert er niets; een nieuwe versie krijgt een nieuwe datum.

## 1. De claim

[geverifieerd, transcript gelezen 15 nov 2026] Nasdaq op 5 minuten, één maand (oktober 2023), handmatig getest. UT Bot Alerts (sleutelwaarde 2, ATR-periode 1) geeft het signaal. Alleen in de New York-sessie, de eerste drie signalen per dag. Een koop alleen bij een groene kaars die boven de signaallijn van de Linear Regression Candles sluit (lengte 11, signaal 7); een verkoop spiegelbeeldig. Instap op het slot. Stop achter de laatste swing. Uitstap op het eerste slot aan de andere kant van de signaallijn, maar alleen als de trade dan in winst staat; anders blijft de trade lopen tot de stop.

| Getal | In de video |
|---|---|
| Trades | 66 (44 winst, 22 verlies) |
| Winrate | "just over a 66%" (44 van 66 is 66,7%) |
| Rekening | +123% in een maand (sizing niet genoemd) |
| Beste trade | 10,59R |

## 2. Toetsbare claims

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Winrate 66,7% | Winrate met 95%-interval (Wilson) |
| C2 | Winstgevend ("123% profit", "will make you rich") | Gemiddeld netto resultaat per trade in R, met 95%-interval (bootstrap per handelsdag) |
| C3 | De regel kiest betere momenten dan toeval | Gemiddeld netto R tegen Null A |

Niet getoetst, wel gemeld: het rendement op de rekening (sizing onbekend) en de beste trade.

## 3. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De claim rust op één maand en 66 trades, handmatig gedaan. Bij 66 trades loopt het 95%-interval rond 66,7% van ongeveer 54,7% tot 76,8%. De video kan dus geluk hebben gehad zonder dat de maker iets fout deed.
2. [aanname] "Recent swing high" en "swing low" zijn niet gedefinieerd. Onze keuze staat in 4.6; een andere keuze geeft een andere stop en dus andere R-waarden.
3. [aanname] "Candle is red ... green": in de video kleurt UT Bot de kaarsen zelf (groen boven de trailing stop). Bij een koopsignaal is die kleur altijd groen, dus de regel zou niets filteren. Wij nemen de gewone kaars (slot boven of onder de open). De kleur van de Linear Regression Candles meten we als gevoeligheid.
4. [geverifieerd] De bron handelt "the NASDAQ" zonder merk of broker. Wij gebruiken de Nasdaq 100 CFD van test G (USTEC). Prijsverloop vrijwel gelijk, kosten en tijden niet.
5. [aanname, beredeneerd] Met een vaste stop en een uitstap alleen in winst zijn veel kleine winsten en minder, grotere verliezen te verwachten. Een hoge winrate zegt daarom weinig; het gemiddelde netto R beslist.

## 4. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de video naar regels te vertalen.

**4.1 Markt en data.** USTEC M1 uit MT5 (servertijd), samengevoegd tot bars van 5 minuten op de servertijd. Vanaf 1 januari 2018 (eerste volle jaar met gevulde SPREAD-kolom). Per dag wordt de opening van de reguliere sessie (9:30 New York) uit de sprong in tickvolume bepaald, zoals in test G.

**4.2 Sessie.** New York 08:00 tot 17:00 America/New_York, de standaard van de sessie-indicator met precies de vier sessies uit de video. Een signaal telt als de signaalbar binnen dat venster sluit.

**4.3 UT Bot.** Exact de openbare code, sleutelwaarde 2, ATR-periode 1, geen Heikin Ashi. ATR(1) is de true range van die bar. Koopsignaal en verkoopsignaal zoals in de code (slot kruist de trailing stop).

**4.4 Linear Regression Candles.** Exact de openbare code: lineaire regressie (lengte 11, offset 0) van open, hoog, laag en slot; signaallijn = SMA met lengte 7 van het regressieslot.

**4.5 Filter en telling.** Per dag de eerste drie UT Bot-signalen binnen de sessie, in volgorde van tijd. Een signaal wordt een trade als:
- koop: slot boven open van de signaalbar en slot boven de signaallijn; verkoop: slot onder open en slot onder de signaallijn;
- er geen trade openstaat.
Een signaal dat het filter niet haalt of tijdens een open trade valt, telt wel mee als een van de drie.

**4.6 Instap en stop.** Instap op het slot van de signaalbar. Stop koop: het laagste laag van de laatste 10 bars van 5 minuten, signaalbar inbegrepen. Stop verkoop: het hoogste hoog van die 10 bars. R = afstand van instap tot stop. Is R kleiner dan 1 punt, dan geen trade (kosten zouden alles bepalen).

**4.7 Uitstap.** Per bar van 5 minuten na de instap:
- raakt de bar de stop, dan uit op de stop (opent de bar al voorbij de stop, dan op de open);
- anders: sluit de bar aan de andere kant van de signaallijn (koop: slot onder de lijn) en staat de trade op dat slot in winst, dan uit op dat slot;
- geen tijdslimiet en geen verplichte uitstap aan het eind van de sessie; open aan het eind van de data: uit op het laatste slot, apart gemeld.

**4.8 Eén positie tegelijk.**

## 5. De drie vaste regels

**Kosten.** Spread uit de SPREAD-kolom op de instapbar plus 1 punt slippage per kant, verrekend in R, zoals test G. Gevoeligheid: slippage 0, 1 en 2 punten per kant.

**Volgorde.** Bar voor bar op 5 minuten. Stop binnen de bar gaat vóór een uitstap op het slot. Instap op het slot van de signaalbar, dus de eerste bar die meetelt is de volgende.

**Controlegroep.** 10.000 runs, seed 37. Opeenvolgend proces door de tijd, zoals test J v1.1.
- **Null A, beslissend:** na elke uitstap (en vanaf het begin) een willekeurige wachttijd in bars binnen de sessie (geometrisch, gemiddeld zo dat het aantal trades rond dat van de regel ligt), dan instap op het slot van de eerste bar vanaf daar die door hetzelfde filter komt als de regel: koop bij een groene kaars die boven de signaallijn sluit, verkoop bij een rode kaars die eronder sluit. Het filter bepaalt dus de richting. Zelfde stop, zelfde uitstap, zelfde kosten, hooguit drie instappen per dag, alleen binnen de sessie. Toetst wat het UT Bot-signaal toevoegt bovenop het filter.
- **Null B, aanvullend:** zoals Null A, maar zonder filter en met een muntworp voor de richting (de controlegroep van versie 1.0). Let op: de regel verslaat Null B ook op markten zonder patroon (zie 11); Null B is daarom alleen ter vergelijking.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 5 jaar M1 met sessiestructuur, de generator van test G v1.1 (random walk zonder drift, 20% per jaar, 60 stapjes per minuut, 70% van de dagbeweging in de sessie), seed 7, 2.000 runs per set.

Grens: gemiddeld percentiel tegen Null A tussen 35 en 65, hooguit 3 van 24 boven 95.

## 7. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | 1 jan 2018 tot en met de laatste volle dag (5 nov 2026) | **Beslissend** voor C1 tot en met C3 |
| P0 | Oktober 2023 | Reproductie van de maand in de video: komen we bij ongeveer 66 trades en 66,7%? Niet beslissend |
| P2 | 6 nov 2023 tot en met de laatste volle dag | Na de video. Aanvullend |
| P3 | Per jaar binnen P1, en long en short apart | Verdeling. Onder 100 trades: onvoldoende |

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd in P1 als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate ligt onder 66,7% |
| C2 | De bovengrens van het 95%-interval van het gemiddelde netto R ligt onder 0 |
| C3 | Het gemiddelde netto R ligt niet boven percentiel 95 van Null A |

Na de run: geen andere instellingen, swings, sessies of uitstappen. Blijft een claim staan, dan "niet gefalsifieerd in deze meting", niet "werkt".

Gevoeligheid, vooraf vastgelegd en niet beslissend: kaarskleur van de Linear Regression Candles in plaats van de gewone kaars; verplichte uitstap om 17:00 New York; slippage 0 en 2 punten.

## 9. Wat ik rapporteer, ongeacht de uitkomst

De trechter: handelsdagen, UT Bot-signalen in de sessie, binnen de eerste drie, door het kleurfilter, door de signaallijn, vervallen tijdens een open trade, vervallen door R onder 1 punt, trades. Per periode: trades, winrate (95%), gemiddeld netto R (95%), profit factor, mediane stop in punten tegenover de kosten, beste en slechtste trade in R, langste reeks verliezen, gemiddelde looptijd, aandeel trades dat over de nacht loopt. Percentielen tegen Null A en Null B. De gevoeligheden. De ruiscontrole.

## 10. Volgende stap

1. Goedkeuring (of aanpassing). SHA-256 in het meetlog.
2. Script `utbot_control.py`: eerst UT Bot en de signaallijn controleren tegen handberekening, dan de ruiscontrole uit 6.
3. Run in de cloud op de USTEC-export van test G (alleen metadata gecontroleerd voor deze test).
4. Code en data op GitHub vóór publicatie.

## 11. Wijziging naar versie 1.1 (vóór de echte data)

[geverifieerd] De ruiscontrole van versie 1.0 zakte: gemiddeld percentiel 99,1, 23 van 24 boven 95 (`noise_24sets_v1.0.txt`). Oorzaak gemeten (`diag_k.py`, twee nepmarkten): willekeurige instappen aan de verkeerde kant van de signaallijn stoppen meteen of verliezen meer (gemiddeld -0,49 R voor long), en hebben een kleinere stop (mediaan 18,3 tegen 25,7 punten bij de regel), zodat de kosten zwaarder wegen. Willekeurige instappen die door hetzelfde kleur- en lijnfilter komen, doen het ongeveer even goed als de regel (-0,13 en -0,11 R tegen -0,12 R). Het filter verandert dus de vorm van de trade, los van enige voorspelling. De controlegroep krijgt daarom hetzelfde filter; C3 toetst nu wat het UT Bot-signaal toevoegt.

Ruiscontrole met versie 1.1: gemiddeld percentiel 44,9, 1 van 24 boven 95 (`noise_24sets.txt`). Geslaagd. Regel, data, periodes, criteria en kosten blijven gelijk aan versie 1.0.
