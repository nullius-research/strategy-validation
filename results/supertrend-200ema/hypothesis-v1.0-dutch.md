# Hypothese: Supertrend + 200 EMA

Datum: 17 november 2026 · Bron: video van een testkanaal, 11 augustus 2020, transcript met handmatige ondertitels · Status: **versie 1.0, vooraf vastgelegd en goedgekeurd op 17 november 2026 (30 minuten, Supertrend 10, 3, verder ongewijzigd), nog geen echte data bekeken**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, transcript] De regels zoals de bron ze geeft:
- Trendfilter: 200-periode exponentieel voortschrijdend gemiddelde (EMA). Boven de EMA alleen kopen, eronder alleen verkopen.
- Long: de Supertrend-lijn wordt groen en springt onder de kaarsen, terwijl de prijs nog boven de 200 EMA ligt.
- Short: het spiegelbeeld. De lijn wordt rood en springt boven de kaarsen, prijs onder de 200 EMA.
- Stop: "at or below the supertrend line" (short: erboven).
- Target: vast, 1,5 keer het risico, zoals in de andere tests van de bron.
- Getest met 100 trades, eerst op EURJPY, daarna op EURUSD omdat de data opraakte.
- Uitkomst: winrate "approximately 46 percent", en daarmee winst. Zeven winsten op rij en zeven verliezen op rij.

[geverifieerd, transcript] Niet genoemd in de bron: het tijdframe, de instellingen van de Supertrend, de periode en het aantal trades per paar.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Winrate ongeveer 46% bij 1,5R | Winrate met betrouwbaarheidsinterval |
| C2 | De strategie maakt winst ("still a profitable strategy") | Gemiddelde netto R per trade groter dan nul |
| C3 | De Supertrend-omslag met het 200 EMA-filter kiest betere momenten dan toeval | Echt resultaat tegen de controlegroep |

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd, rekenkundig] Bij een target van 1,5R is het break-evenpunt een winrate van 40% (0,4 × 1,5 = 0,6 × 1), vóór kosten. 46% betekent +0,15R per trade vóór kosten. Dat is een smalle marge: kosten van 0,15R per trade maken hem al op.
2. [geverifieerd, rekenkundig] Bij 46 winsten uit 100 trades is het 95%-interval (Wilson) ongeveer 36,6% tot 55,7%. De ondergrens ligt onder het break-evenpunt van 40%. De bron kan met 100 trades dus niet aantonen dat de winrate boven break-even ligt.
3. [geverifieerd, transcript] De bron zegt zelf dat de stop op de Supertrend-lijn soms te ver weg lag. Bij een verre stop is het target van 1,5R ook ver weg; dat drukt de winrate.
4. [geverifieerd, transcript] Tijdframe en instellingen ontbreken. Elke keuze hieronder is dus mijn vertaling, met de reden erbij.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Instrumenten en tijd.** Hoofdtest: EURUSD en EURJPY samen, de paren uit de bron, op 30 minuten. Reden voor 30 minuten: dezelfde bron gebruikte 30 minuten in de MACD-test uit dezelfde periode, en 30 minuten als instaptijdframe in een latere Supertrend-video [geverifieerd, bronnen van test A en een artikel van de bron uit november 2025]; dat de video van 2020 ook 30 minuten gebruikte, is niet gecontroleerd [aanname]. M30-bars worden gemaakt uit de M15-exports (twee bars per halfuur, beginnend op :00 en :30 servertijd). Periode: alles wat de exports bevatten. Aanvullend, apart gerapporteerd en niet beslissend: 15 minuten en 1 uur op dezelfde twee paren, en 30 minuten op de andere paren uit dezelfde M15-exports.

**3.2 Indicatoren.**
- Supertrend(10, 3): ATR-periode 10 met Wilder-afvlakking, factor 3, op (high + low) / 2. Dit is de standaardinstelling van de ingebouwde Supertrend van TradingView, omdat de bron geen getallen noemt.
- Banden zoals gebruikelijk: onderband = mid − 3 × ATR, bovenband = mid + 3 × ATR. De onderband mag alleen stijgen zolang het vorige slot erboven lag, de bovenband alleen dalen zolang het vorige slot eronder lag. Richting wordt omhoog als het slot boven de bovenband van dezelfde bar sluit (na die aanpassing), omlaag als het onder de onderband van dezelfde bar sluit. Exact de rekenregel `pine_supertrend` uit de Pine-referentie van TradingView [geverifieerd, 17 nov 2026]. De Supertrend-lijn is de onderband bij richting omhoog (groen) en de bovenband bij richting omlaag (rood).
- EMA 200 op de slotkoers.
- Alles berekend tot en met de signaalbar.

**3.3 Signaal (op de slotkoers van bar t).**
- Long: richting(t-1) omlaag, richting(t) omhoog, slot(t) > EMA200(t).
- Short: richting(t-1) omhoog, richting(t) omlaag, slot(t) < EMA200(t).

**3.4 Instap.** Openingskoers van bar t+1. Nooit op de slotkoers van de signaalbar zelf, omdat de omslag pas vaststaat als de bar gesloten is.

**3.5 Stop.** Long: de waarde van de Supertrend-lijn op bar t (de onderband). Short: de waarde van de lijn op bar t (de bovenband). Vast, niet meebewegend. Ligt de instap al voorbij de stop (gat bij de opening), dan geen trade. Ligt de stop minder dan 5 pips van de instap (EURJPY 0,05), dan geen trade, zoals in tests A tot en met D.

**3.6 Target.** 1,5 keer de afstand van instap tot stop. Geen break-even, geen gedeeltelijke winst, geen meebewegende stop, geen tijdslimiet. Wat aan het eind van de data nog openstaat, wordt gesloten op de laatste slotkoers.

**3.7 Eén positie tegelijk per paar.** Staat er een trade open, dan vervallen nieuwe signalen op dat paar.

## 4. De drie vaste regels

**Kosten.** 1,2 pip round trip per trade, de vaste aanname uit eerdere FX-tests [geverifieerd, tests A tot en met D]. Gevoeligheid: 0, 1,2 en 2,0 pip.

**Volgorde.** Het pad wordt bar voor bar doorlopen op M15, fijner dan het signaal. Raakt één M15-bar zowel stop als target, dan telt hij als stop. Ook de instapbar zelf telt mee.

**Controlegroepen.** 10.000 runs per controle, seed 19. Bootstrap per handelsdag, beide paren samen.
- **Null A, beslissend (muntworp):** dezelfde instapmomenten als de echte trades, richting willekeurig, zelfde stopafstand gespiegeld, zelfde 1,5R, zelfde kosten. Voor FX is dit de vaste nulmeting, omdat long en short symmetrisch zijn [geverifieerd, methode en audit controlegroepen van 10 november].
- **Null B, aanvullend (timing binnen de trend):** per echte trade een willekeurige bar op hetzelfde paar en in dezelfde maand waarop de Supertrend dezelfde richting had als de trade en het slot aan dezelfde kant van de EMA200 lag, richting volgens de trend, stop op de Supertrend-lijn van die bar. Toetst of het moment van de omslag iets toevoegt bovenop de trendtoestand. Bekend uit tests A, B en D: dit soort controle kan op ruis scheef zijn in het voordeel van de regel [geverifieerd, meetlogs]. Een hoog percentiel tegen Null B telt daarom niet als bewijs.

## 5. Ruiscontrole vóór de echte data (vast)

Het script draait eerst op 24 synthetische random-walk-sets (M15, 4 jaar, EURUSD dagvol 0,5%, EURJPY dagvol 0,6%, seeds 1 tot 24, 2.000 runs per set), zonder voorspelbaarheid per constructie. Grens: gemiddeld percentiel tegen Null A tussen 35 en 65, hooguit 3 van 24 sets boven 95, en een bruto winrate rond 40%. Haalt het script dat niet, dan eerst de oorzaak zoeken en een nieuwe versie van dit document, vóór de echte data.

## 6. Data

[geverifieerd, meetlogs A, B en D] De M15-exports in `Documents\trading` bevatten EURUSD en EURJPY van augustus 2022 tot augustus 2026, van één broker, broker-offset 2. Voor deze test is nog niets geopend. Datacontrole vóór de run: ontbrekende bars, dubbele tijden, nul- of negatieve prijzen, sprongen.

[geverifieerd] De claim is van augustus 2020. De hele dataperiode ligt dus ná de claim.

## 7. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate (beide paren samen) ligt onder 46% |
| C2 | De bovengrens van het 95%-interval van de gemiddelde netto R (beide paren samen) ligt onder 0 |
| C3 | Het echte resultaat (gemiddelde netto R) ligt niet boven percentiel 95 van Null A |

Valt C3, dan is het idee dood: niet repareren, niet optimaliseren, geen andere Supertrend-instellingen, stopregels of tijdframes proberen. Onder 100 trades staat in het rapport "onvoldoende trades".

## 8. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades per paar en samen, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A en Null B, resultaat per jaar, som van de beste 5% trades naast het totaal, de drie kostenniveaus, de mediane stopafstand in pips tegenover de kosten, de langste reeks winsten en verliezen (de bron noemt zeven en zeven), en de aanvullende tijdframes en paren uit 3.1.

## 9. Volgende stap

1. Goedgekeurd op 17 november 2026. SHA-256 staat in de interne meetlog.
2. Meetscript `supertrend_control.py`: eerst Supertrend en EMA controleren tegen een handberekening, dan de ruiscontrole uit 5.
3. Map `Documents\trading` koppelen voor de M15-exports, datacontrole, run 01.
