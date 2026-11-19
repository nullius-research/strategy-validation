# Hypothese: 9 EMA + VWAP op 3 minuten (test N)

Datum: 18 november 2026 · Bron: Instagram-reel van 30 oktober 2026, regels uit de gesproken tekst · Status: **versie 1.0, vooraf vastgelegd en goedgekeurd op 18 november 2026 (K1 A, K2 A, K3 A), nog geen echte koersdata geopend voor deze test**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, transcript en caption] De regels zoals de bron ze geeft:
- Tijdframe 3 minuten.
- EMA 9 op de slotkoers.
- VWAP met ankerperiode "session" op OHLC4 ((open + high + low + close) / 4).
- Long ("calls"): de EMA 9 kruist boven de VWAP. Short ("puts"): de EMA 9 kruist onder de VWAP.
- Uitstap: "If candle breaches the EMA 9 on the 3-minute time frame, exit your position."
- Noodrem: "If it's a fake out, exit at -25% to -30%" (van de optiepremie [aanname]).
- Resultaat: "I made over $255,000 in ONE MONTH" (oktober 2026), met opties.

[geverifieerd] Niet genoemd: de onderliggende waarde, sessietijden, aantal trades, winrate, positiegrootte.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | De regel maakt winst ("insane trading strategy", "$255,000 in one month") | Gemiddeld netto resultaat per trade op de onderliggende waarde groter dan nul, over alle data |
| C2 | De kruising van EMA 9 en VWAP kiest betere momenten dan toeval | Echt resultaat tegen de controlegroep met dezelfde uitstapregel |
| C3 | Oktober 2026, de maand van de claim, was winstgevend met deze regel | Gemiddeld netto resultaat per trade in oktober 2026 groter dan nul |

[geverifieerd] Niet toetsbaar: het bedrag van $255.000. Dat is het persoonlijke resultaat van één rekening met opties, met onbekende positiegrootte en onbekende keuzes per trade. Wij meten de regel, niet de rekening. Dat staat zo in elke publicatie.

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd] Eén maand is één steekproef. Een sterke maand zegt weinig over de regel zelf; dat geldt voor elke maand die achteraf wordt uitgekozen.
2. [aanname] Een kruising van twee lijnen op 3 minuten geeft per dag waarschijnlijk meerdere signalen, met korte trades. Bij korte trades wegen spread en slippage zwaar.
3. [geverifieerd, transcript] De uitstapregel is in twee betekenissen te lezen: een kaars die door de EMA 9 sluit, of een kaars die de EMA 9 alleen raakt. Zie keuze K1.
4. [geverifieerd] De noodrem is in procenten van een optiepremie. Op de onderliggende waarde bestaat die grens niet zonder aannames over looptijd, strike en volatiliteit. Zie keuze K2.
5. [geverifieerd, eerdere tests] Onze data is een CFD op de S&P 500 met tickvolume, geen echt verhandeld volume. De VWAP wordt dus gewogen met tickvolume [aanname dat dit de echte VWAP benadert]. Gevoeligheid: VWAP zonder volume (alle minuten even zwaar).

## 3. Keuzes (gekozen op 18 november 2026: K1 A, K2 A, K3 A, de vetgedrukte opties)

| Keuze | A | B |
|---|---|---|
| K1 · Uitstap "candle breaches the EMA 9" | **Slotkoers van de 3-minutenkaars aan de andere kant van de EMA 9, uit op de opening van de volgende kaars.** Zo las ook de enige andere test die ik vond het (een ander testkanaal) [geverifieerd, transcript] | Kaars raakt de EMA 9 (long: low onder de EMA 9), uit op de EMA 9 zelf. Geeft eerdere uitstappen en meer kleine verliezen |
| K2 · Noodrem van -25 tot -30% | **Geen extra stop. Alleen de EMA-uitstap en sluiten aan het eind van de sessie.** De grens bestaat alleen voor opties; elke vertaling naar punten is ons eigen getal. Ik rapporteer wel het grootste verlies per trade | Vaste stop van 0,3% van de koers [aanname: ruwe vertaling van -25% premie bij een delta rond 0,5 en een premie van ongeveer 0,6% van de koers] |
| K3 · Beslissend instrument | **US500 (S&P 500).** Het andere testkanaal testte op de ES-future; de bron noemt geen instrument | USTEC (Nasdaq 100). "75 point uptrend" past even goed bij de Nasdaq [aanname] |

Het niet-gekozen instrument uit K3 wordt aanvullend gerapporteerd, niet beslissend. De niet-gekozen K1-variant ook.

## 4. Mechanische vertaling (vast na goedkeuring)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**4.1 Sessie.** Alleen de reguliere beurstijd, 9:30 tot 16:00 New Yorkse tijd, zoals het andere testkanaal het las ("RTH"). De opening per dag zoals in test G en H: de sprong in tickvolume rond 16:30 servertijd. Een dag telt alleen mee met minstens 90% van de 390 minuutbars.

**4.2 Bars.** 3-minutenkaarsen uit de M1-data, beginnend op 9:30: 9:30, 9:33, ... 15:57. 130 kaarsen per dag.

**4.3 Indicatoren.**
- EMA 9 op de slotkoers van de 3-minutenkaarsen, alleen reguliere sessie, doorlopend over de dagen (zoals een grafiek met alleen beurstijd dat doet).
- VWAP: begint elke dag opnieuw bij de kaars van 9:30. Prijs per minuut is OHLC4 van die minuut, gewicht is het tickvolume van die minuut. Waarde op het slot van de 3-minutenkaars = som(prijs × volume) / som(volume) vanaf 9:30 tot en met de laatste minuut van die kaars.
- Alles berekend tot en met de signaalkaars.

**4.4 Signaal (op het slot van 3-minutenkaars t).**
- Long: EMA9(t-1) ≤ VWAP(t-1) en EMA9(t) > VWAP(t).
- Short: EMA9(t-1) ≥ VWAP(t-1) en EMA9(t) < VWAP(t).
- Pas vanaf de tweede kaars van de dag (de VWAP begint om 9:30 opnieuw, een vergelijking met de vorige dag zegt niets). Geen signalen op de laatste kaars van de dag.

**4.5 Instap.** Openingskoers van kaars t+1 (de open van de eerste minuut). Nooit op het slot van de signaalkaars.

**4.6 Uitstap.** Volgens K1. Bij A: long uit als slot(k) < EMA9(k), short uit als slot(k) > EMA9(k), gecontroleerd vanaf het slot van de instapkaars, uit op de open van kaars k+1. Verder: alles dicht op het slot van de laatste kaars (16:00). Geen doel in punten, geen meebewegende stop. Noodrem volgens K2.

**4.7 Eén positie tegelijk.** Een nieuwe kruising in dezelfde richting terwijl de positie openstaat, vervalt. Een kruising in de andere richting terwijl de positie openstaat: de positie gaat dicht en de nieuwe opent, beide op de open van de volgende kaars.

**4.8 Resultaat.** Per trade in punten en in basispunten van de instapkoers, netto na kosten. Er is geen vaste stop, dus geen R.

## 5. De drie vaste regels

**Kosten.** De spread uit de SPREAD-kolom op de instapminuut, plus 0,25 punt slippage per kant (instap en uitstap), zoals test H [geverifieerd, hypothese test H]. Gevoeligheid: slippage 0, 1 en 2 keer. Voor USTEC dezelfde opbouw met 1 punt slippage per kant [aanname].

**Volgorde.** Het pad wordt minuut voor minuut doorlopen. Bij K1-A en K2-A vallen alle uitstappen op een kaarsopening, dus speelt de volgorde binnen een minuut geen rol. Bij K1-B of K2-B: raakt één minuut zowel de uitstap als de noodrem, dan telt de slechtste uitkomst.

**Controlegroep.** 10.000 runs, seed 43, bootstrap per handelsdag.
- **Null A, beslissend voor C2:** dezelfde dagen, dezelfde sessie, dezelfde uitstapregel en dezelfde kosten. Een opeenvolgend proces: op elke 3-minutenkaars waarop geen positie openstaat (behalve de eerste en laatste van de dag), opent toeval een positie met kans p. De richting is de kant waar het slot ligt ten opzichte van de EMA 9 (boven: long, onder: short), zodat de uitstapregel precies zo werkt als bij de echte trades. p is zo gekozen dat het gemiddelde aantal trades gelijk is aan dat van de regel. Toetst of de kruising met de VWAP iets toevoegt bovenop willekeurige instappen met dezelfde EMA-uitstap. Opgezet zoals de lessen van test J en K: zelfde opbouw als de regel vanaf het begin [geverifieerd, overdracht 25].
- Percentiel van het echte gemiddelde netto resultaat per trade.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 1.500 handelsdagen met minuutbars, opgebouwd uit 60 stapjes per minuut (zoals test G en H), zonder trend en zonder openingseffect, met een vaste spread van 0,5 punt en willekeurig tickvolume. Seed 7.

Grens, gelijk aan de audit van 10 november: percentiel tegen Null A gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95. Haalt het script dat niet, dan eerst de oorzaak zoeken en een nieuwe versie van dit document, vóór de echte data.

## 7. Data

[geverifieerd, hypothese en datacontrole test H] US500 M1, IC Markets, `Test\lce-supply-demand\US500_M1_201208060000_202611021049.csv`, echte minuutdata vanaf 21 maart 2017, spreadkolom vanaf 2019 gevuld. Loopt tot 2 november 2026, dus oktober 2026 zit erin. USTEC M1 uit test G (`Test\box-theory\USTEC_M1_201208060000_202611052200.csv`). Voor deze test is nog niets geopend.

Perioden:
- **P1, beslissend voor C1 en C2:** alle geldige sessies vanaf 2019 (spreadkolom gevuld) tot en met 30 oktober 2026.
- **P0, beslissend voor C3:** oktober 2026.
- Aanvullend: 2017 en 2018 met de mediane spread van 2019 [aanname].

Datacontrole vóór de run, alleen metadata: aantal geldige sessies per jaar, verdeling van de gevonden openingsminuut, aandeel dagen met lege spread, minuten met tickvolume nul.

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval (dagbootstrap) van het gemiddelde netto resultaat per trade in P1 ligt onder 0 |
| C2 | Het echte gemiddelde netto resultaat in P1 ligt niet boven percentiel 95 van Null A |
| C3 | De bovengrens van het 95%-interval van het gemiddelde netto resultaat per trade in oktober 2026 ligt onder 0 |

Valt C2, dan is het idee dood: niet repareren, niet optimaliseren, geen filters, andere lengtes of tijdframes proberen. Onder 100 trades in een periode staat in het rapport "onvoldoende trades".

## 9. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades en trades per dag, winrate (beschrijvend, de bron noemt er geen), gemiddeld netto resultaat in punten en basispunten met 95%-interval, profit factor, percentiel tegen Null A, het resultaat zonder kosten, de drie kostenniveaus, mediane duur van een trade, grootste verlies per trade (vanwege K2), long en short apart, per jaar, oktober 2026 apart, de niet-gekozen K1-variant, de VWAP zonder volume, en het niet-gekozen instrument uit K3.

Titel volgens de vaste regel: geen percentage in de claim, dus het hoofdgetal: "$255,000 claimed", met onze meting ernaast.

## 10. Volgende stap

1. Goedgekeurd op 18 november 2026 (K1 A, K2 A, K3 A). SHA-256 in `meetlog-vwap-9ema.md`. Engelse versie ernaast.
2. Script `vwap_control.py`: eerst EMA en VWAP controleren tegen een handberekening, dan de ruiscontrole uit 6.
3. Datacontrole uit 7, dan run 01.
