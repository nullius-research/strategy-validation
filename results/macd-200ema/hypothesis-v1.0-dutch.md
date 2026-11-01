# Hypothese: Trading Rush "MACD + 200 EMA"

Datum: 1 november 2026 · Bron: tradingrush.net, "I risked MACD Trading Strategy 100 TIMES" (transcript van de video van Trading Rush) · Status: **vooraf vastgelegd, versie 1.0, nog geen echte data bekeken**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, tradingrush.net] De regels zoals de bron ze geeft:
- Trendfilter: 200 EMA. Boven de 200 EMA alleen kopen, eronder alleen verkopen.
- Long: de MACD-lijn kruist boven de signaallijn, en die kruising gebeurt onder de nullijn.
- Short: het spiegelbeeld. MACD-lijn kruist onder de signaallijn, boven de nullijn, prijs onder de 200 EMA.
- Stop: "below the pullback of the trend".
- Target: in de backtest 1,5 keer het risico. Elders in dezelfde bron: 25% eraf op 1R, stop naar break-even, rest op 2R. De bron brengt die twee niet met elkaar in overeenstemming.
- Getest op 30-minutengrafieken, eerst EURUSD, daarna EURJPY. 1% risico per trade.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | 62 van de 100 trades winst, dus winrate 62% bij 1,5R | Winrate met betrouwbaarheidsinterval |
| C2 | Na 100 trades ongeveer 50% winst op het account bij 1% risico, dus ongeveer +0,5R per trade | Gemiddelde netto R per trade |
| C3 | De combinatie MACD + 200 EMA kiest betere momenten dan toeval | Echt resultaat tegen de controlegroepen |

[geverifieerd] Niet toetsbaar en buiten deze meting: "werkt op elk tijdframe en in elke markt". De bron sloeg 3 trades over met een "onduidelijke" entry. Dat is een discretionaire keuze die niet na te bootsen is; hier telt elke trade mee.

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd, rekenkundig] Bij een target van 1,5R is het break-evenpunt een winrate van 40% (0,4 × 1,5 = 0,6 × 1), vóór kosten. Een claim van 62% betekent +0,55R per trade, een uitzonderlijk hoog getal voor één indicatorcombinatie op de meest verhandelde valutaparen [aanname dat dit uitzonderlijk is].
2. [geverifieerd] Honderd trades geven bij een echte winrate van 50% een 95%-interval van ongeveer 40% tot 60% [rekenkundig, binomiaal]. Een gemeten 62% over 100 trades sluit dus niet uit dat de echte winrate rond 50% ligt.
3. [geverifieerd] De stop ("below the pullback") is niet mechanisch gedefinieerd. Elke vertaling is mijn keuze. Daarom staat hij hieronder vast, met de reden.
4. [geverifieerd] Twee verschillende targetregels in één bron. Hier wordt de regel van de backtest getest (1,5R), omdat de 62% daarbij hoort.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Instrumenten en tijd.** Hoofdtest: EURUSD en EURJPY op 30 minuten, de paren uit de bron. M30-bars worden gemaakt uit de M15-exports (twee bars per halfuur, beginnend op :00 en :30 servertijd). Periode: alles wat de exports bevatten. Aanvullend, apart gerapporteerd en niet beslissend: dezelfde regels op de andere zeven paren uit de Bollinger-test.

**3.2 Indicatoren.** MACD(12, 26, 9) op de slotkoers, de standaardinstelling, omdat de bron geen getallen noemt. EMA 200 op de slotkoers. Alles berekend tot en met de signaalbar.

**3.3 Signaal (op de slotkoers van bar t).**
- Long: MACD(t-1) ≤ signaal(t-1) en MACD(t) > signaal(t), MACD(t) < 0 en signaal(t) < 0, slot(t) > EMA200(t).
- Short: MACD(t-1) ≥ signaal(t-1) en MACD(t) < signaal(t), MACD(t) > 0 en signaal(t) > 0, slot(t) < EMA200(t).

**3.4 Entry.** Openingskoers van bar t+1. Nooit op de slotkoers van de signaalbar zelf, omdat de kruising pas vaststaat als de bar gesloten is.

**3.5 Stop ("below the pullback").** Long: laagste low van de laatste 10 bars tot en met t. Short: hoogste high van de laatste 10 bars tot en met t. Tien bars op 30 minuten is 5 uur, ongeveer de lengte van een pullback in de voorbeelden van de bron [aanname, niet gemeten]. Ligt de stop minder dan 5 pips van de entry (EURJPY 0,05), dan geen trade. Les uit de LCE-test: te krappe stops worden opgegeten door de kosten [geverifieerd in die test].

**3.6 Target.** 1,5 keer de afstand entry tot stop. Geen break-even, geen gedeeltelijke winst. Geen tijdslimiet. Wat aan het eind van de data nog openstaat, wordt gesloten op de laatste slotkoers.

**3.7 Eén positie tegelijk per paar.** Staat er een trade open, dan vervallen nieuwe signalen op dat paar. Zoals de bron het beschrijft: één trade na de andere [aanname dat de bron zo werkte].

## 4. De drie vaste regels

**Kosten.** 1,2 pip round trip per trade, de vaste aanname uit eerdere tests [geverifieerd, Overdracht Nullius Research]. Gevoeligheid: 0, 1,2 en 2,0 pip.

**Volgorde.** Het pad wordt bar voor bar doorlopen op M15, dus fijner dan het signaal. Raakt één M15-bar zowel stop als target, dan telt hij als stop.

**Controlegroepen.** 10.000 runs per controle, seed 19. Bootstrap per handelsdag, beide paren samen.
- **Null A, beslissend (muntworp):** dezelfde entrymomenten als de echte trades, richting willekeurig, zelfde stopafstand gespiegeld, zelfde 1,5R, zelfde kosten. Voor FX is dit de juiste nulmeting, omdat long en short symmetrisch zijn [geverifieerd, methode].
- **Null B, aanvullend (timing binnen de trend):** per echte trade een willekeurige bar op hetzelfde paar en in dezelfde maand waarop de slotkoers aan dezelfde kant van de EMA200 lag, richting volgens de trend, zelfde stopregel als 3.5. Toetst of de MACD-kruising iets toevoegt bovenop het trendfilter.

## 5. Data

[geverifieerd, README op GitHub] De M15-exports van de Bollinger-test bevatten negen paren, waaronder EURUSD en EURJPY, van augustus 2022 tot augustus 2026, van één broker. [aanname] De ruwe bestanden staan nog in een lokale map. Die map is nog niet gekoppeld; er is nog niets geopend.

[geverifieerd, rekenkundig] Vier jaar is ongeveer 50.000 M30-bars per paar (48 per handelsdag, ongeveer 260 handelsdagen per jaar). Hoeveel signalen dat geeft, is onbekend tot de synthetische controle [aanname].

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate ligt onder 62% |
| C2 | De bovengrens van het 95%-interval van de gemiddelde netto R ligt onder +0,5R |
| C3 | Het echte resultaat (gemiddelde netto R) ligt niet boven percentiel 95 van Null A |

Valt C3, dan is het systeem dood volgens stap 5: niet repareren, niet optimaliseren, geen andere MACD-instellingen of stopregels proberen. Onder 100 trades per paar staat in het rapport "onvoldoende trades" voor dat paar; de beide paren samen zijn dan beslissend.

## 7. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades per paar, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A en Null B, resultaat per jaar, aandeel van de beste 5% trades in het totaal, de drie kostenniveaus, en de mediane stopafstand in pips tegenover de kosten.

## 8. Volgende stap

1. Erwin keurt dit document goed of past het aan. Daarna ligt het vast.
2. Meetscript `macd_control.py` schrijven en eerst draaien op synthetische random-walk-data (M15, 4 jaar, twee paren). Daar moet het oordeel "dood" uitkomen. Pas dan de echte data.
3. Map `Documents\trading` koppelen voor de M15-exports.
