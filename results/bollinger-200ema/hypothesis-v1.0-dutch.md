# Hypothese: Bollinger Bands + 200 EMA (test D)

Datum: 7 november 2026 · Bron: een video van een testkanaal (2020) en een open-source script van een derde dat die strategie uitwerkt (2020); bron met naam staat in de privéprojectbestanden · Status: **versie 1.0, vooraf vastgelegd en goedgekeurd op 7 november 2026, nog geen echte data bekeken**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, transcript en script] De regels zoals de bronnen ze geven:
- Trendfilter: 200 EMA. Boven de 200 EMA alleen kopen, eronder alleen verkopen.
- Bollinger Bands: 20 perioden, 2 standaarddeviaties rond een SMA (lengte 20 alleen in het script).
- Long: prijs boven de 200 EMA, prijs raakt de onderste band.
- Short: prijs onder de 200 EMA, prijs raakt de bovenste band.
- Stop: niet genoemd, in de video met de hand gezet.
- Target: 1,5 keer het risico.
- Getest op EURUSD, 15 minuten, 100 trades, handmatig.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Winrate 52% bij 1,5R | Winrate met 95%-interval |
| C2 | $1.000 werd $1.622,60 na 100 trades, samen met 52% bij 1,5R ongeveer +30R, dus ongeveer +0,30R per trade [geverifieerd, rekensom: 52 x 1,5R - 48 x 1R = +30R] | Gemiddelde netto R per trade |
| C3 | De combinatie Bollinger + 200 EMA kiest betere momenten dan toeval | Echt resultaat tegen de controlegroep |

[geverifieerd] Niet toetsbaar en buiten deze meting: de aanbeveling om de strategie te combineren met price action, steun en weerstand of vraag- en aanbodzones. Dat is discretionair.

## 2. Zwakke plekken die al vóór de test zichtbaar zijn

1. [geverifieerd, rekenkundig] Bij een target van 1,5R is het break-evenpunt een winrate van 40% vóór kosten. Op een random walk zonder drift is 40% ook de verwachte winrate. De claim van 52% ligt 12 procentpunt hoger.
2. [geverifieerd, binomiaal] Bij een echte winrate van 40% is de kans op 52 of meer winnaars in 100 trades 1,0%. Bij een echte winrate van 52% is het 95%-interval over 100 trades ongeveer 42% tot 62%.
3. [geverifieerd] De stop is in de bron een handmatige keuze per trade. Elke vaste stop is mijn vertaling. Dat geldt ook voor het instapmoment. Beide staan hieronder vast.
4. [geverifieerd] Het script en de video komen van verschillende makers. Het script is een interpretatie van de video door een derde [geverifieerd, scriptbeschrijving]. Waar ze verschillen, volgt deze test het script, omdat dat de enige mechanische versie is.
5. [aanname] De periode van de bron is onbekend; in beeld staat vermoedelijk mei 2020. Deze test meet een andere periode.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen. Gekozen vóór het openen van de data, op 7 november 2026: stop A (swing) en instap X (slot van de signaalbar).

**3.1 Instrumenten en tijd.** Hoofdtest: EURUSD op 15 minuten, het paar en tijdframe uit de bron. Periode: alles wat de export bevat. Aanvullend, apart gerapporteerd en niet beslissend: dezelfde regels op de andere paren uit dezelfde M15-exports.

**3.2 Indicatoren.** Op de slotkoers, berekend tot en met de signaalbar:
- EMA 200.
- Middenlijn SMA 20; banden op plus en min 2,0 keer de standaarddeviatie van de laatste 20 slotkoersen (populatie-standaarddeviatie, zoals in het bronscript) [aanname over de definitie in het bronscript].

**3.3 Signaal op bar t, exact zoals de scriptcode.**
- Long: low(t) > EMA200(t) en low(t) < onderband(t) en niet low(t-1) < onderband(t-1).
- Short: high(t) < EMA200(t) en high(t) > bovenband(t) en niet high(t-1) > bovenband(t-1).

**3.4 Instap (X).** Op de eerste prijs na het slot van de signaalbar, dus de openingskoers van bar t+1. Het signaal staat pas vast als bar t gesloten is.

**3.5 Stop (A).** Long: laagste low van de laatste 10 bars tot en met t. Short: hoogste high van de laatste 10 bars tot en met t. Dezelfde regel als in test A (MACD + 200 EMA), zodat de reeks vergelijkbaar blijft. Op 15 minuten is dat 2,5 uur. Ligt de stop minder dan 5 pips van de instap (JPY-paren 0,05), dan geen trade.

**3.6 Target.** 1,5 keer de afstand van instap tot stop. Geen break-even, geen gedeeltelijke winst, geen tijdslimiet. Wat aan het eind van de data nog openstaat, wordt gesloten op de laatste slotkoers.

**3.7 Eén positie tegelijk per paar.** Staat er een trade open, dan vervallen nieuwe signalen op dat paar [geverifieerd, scriptbeschrijving].

## 4. De drie vaste regels

**Kosten.** 1,2 pip round trip per trade, de vaste aanname uit eerdere tests [geverifieerd, Overdracht Nullius Research]. Gevoeligheid: 0, 1,2 en 2,0 pip.

**Volgorde.** Het pad wordt bar voor bar doorlopen op M15. Raakt één bar zowel stop als target, dan telt hij als stop. Ook de instapbar t+1 zelf telt mee.

**Controlegroep.** 10.000 runs, seed 19. Bootstrap per handelsdag.
- **Null A, beslissend (muntworp):** dezelfde instapmomenten als de echte trades, richting willekeurig, zelfde stopafstand gespiegeld, zelfde 1,5R, zelfde kosten. Voor FX is dit de juiste nulmeting [geverifieerd, methode].
- **Null B, aanvullend (timing binnen de trend):** per echte trade een willekeurige bar op hetzelfde paar en in dezelfde maand waarop de low boven (long) of de high onder (short) de EMA200 lag, richting volgens de trend, zelfde stopregel als 3.5. Toetst of de bandaanraking iets toevoegt bovenop het trendfilter. Bekend uit tests A en B: Null B is op ruis scheef in het voordeel van de regel [geverifieerd, meetlogs A en B]. Een hoog percentiel tegen Null B telt daarom niet als bewijs.

## 5. Data

[geverifieerd, meetlogs A en B] De M15-exports bevatten EURUSD van augustus 2022 tot augustus 2026, van één broker, broker-offset 2. Voor deze test is nog niets geopend.

[geverifieerd, rekenkundig] Vier jaar is ongeveer 100.000 M15-bars. Hoeveel signalen dat geeft, is onbekend tot de synthetische controle [aanname].

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate op EURUSD ligt onder 52% |
| C2 | De bovengrens van het 95%-interval van de gemiddelde netto R op EURUSD ligt onder +0,30R |
| C3 | Het echte resultaat op EURUSD (gemiddelde netto R) ligt niet boven percentiel 95 van Null A |

Valt C3, dan is het idee dood volgens stap 5: niet repareren, niet optimaliseren, geen andere bandinstellingen, stopregels of tijdframes proberen. Onder 100 trades staat in het rapport "onvoldoende trades".

## 7. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A en Null B, resultaat per jaar, som van de beste 5% trades naast het totaal, de drie kostenniveaus, de mediane stopafstand in pips tegenover de kosten, en de langste reeks verliezen (de bron noemt vijf).

## 8. Volgende stap

1. Goedgekeurd op 7 november 2026, vóór de eerste run.
2. Meetscript `bb200_control.py` schrijven en eerst draaien op 24 synthetische random-walk-sets (M15, 4 jaar). Daar moet een winrate rond 40% en een gelijkmatige spreiding van de Null A-percentielen uitkomen. Pas dan de echte data.
