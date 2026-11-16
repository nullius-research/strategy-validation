# Hypothese: gespreide instap met MACD en 200 EMA op Bitcoin 30 minuten (test L)

Datum: 15 november 2026 · Bron: video van een tradingkanaal over een "87% win rate"-strategie (bron met naam privé) · Status: **versie 1.0, goedgekeurd op 15 november 2026 zonder wijziging (de standaardkeuzes). De regel is nog niet op koersdata gedraaid. De Bitcoin-data is dezelfde export als bij test J; daar is hij voor een andere regel gebruikt. Voor deze test zijn alleen het aantal regels en de eerste en laatste tijd bekeken.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de eerste echte run verandert er niets; een nieuwe versie krijgt een nieuwe datum.

## 1. De claim

[geverifieerd, transcript gelezen 15 nov 2026] Bitcoin op 30 minuten, "the last four years" vóór de video van 28 september 2024, handmatig getest. Trendfilter: de 200 EMA van 4 uur, in de versie van de maker die "verdwijnt" in een zijwaartse markt. Long: prijs boven die EMA, de MACD-lijn kruist boven de signaallijn en die kruising ligt onder de nullijn. Short gespiegeld. Stop achter de 200 EMA. Twee varianten, elk 100 trades:

| Variant | Regel | Getallen in de video |
|---|---|---|
| Zonder spreiden | Eén positie, doel 0,5R, 3% risico | Winrate "approximately 73%", "around 28% profit", breakeven "around 67%" |
| Gespreid | Tot drie instappen van 1% risico in dezelfde setup, steeds lager (long), stop op dezelfde plek; doel 0,25R na de eerste en tweede instap, 0,5R na de derde, gerekend vanaf de gemiddelde instapprijs | Winrate 87%, breakeven "between 67% and 80%", edge "around 10%", totale winst iets lager dan zonder spreiden |

## 2. Toetsbare claims

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Gespreid: winrate 87% | Winrate per setup met 95%-interval (Wilson) |
| C2 | Zonder spreiden: winrate 73% | Winrate per trade met 95%-interval (Wilson) |
| C3 | Zonder spreiden is winstgevend | Gemiddeld netto R per trade, 95%-interval (bootstrap per week) |
| C4 | Gespreid is winstgevend | Gemiddeld netto resultaat per setup in procent van de rekening (1% per instap), 95%-interval (bootstrap per week) |
| C5 | De regel kiest betere momenten dan toeval | Gemiddeld netto resultaat tegen Null A, apart voor gespreid (C5a) en zonder spreiden (C5b) |

Niet getoetst, wel gemeld: het rekeningrendement van 28% (de volgorde van zijn 100 trades is onbekend) en de bewering dat spreiden de winrate verhoogt "niet alleen door het lagere doel". Dat laatste meten we wel (paragraaf 9: dezelfde instappen met één positie en doel 0,25R).

## 3. Zwakke plekken, vooraf benoemd

1. [aanname, beredeneerd] Bij een doel van 0,25R en een stop van 1R geeft willekeurig instappen zonder kosten al een winrate rond 80%; bij 0,5R rond 67%. Een hoge winrate is hier dus vooral een gevolg van het kleine doel. De controlegroep laat zien wat toeval geeft met precies dezelfde doelen.
2. [geverifieerd] Twee keer 100 trades in vier jaar. Bij 100 trades loopt het 95%-interval rond 87% van ongeveer 79% tot 92%, rond 73% van ongeveer 64% tot 81%.
3. [aanname] Vier jaar op 30 minuten levert met deze regel waarschijnlijk veel meer dan 100 signalen op. De maker nam mogelijk niet elk signaal; welke wel, staat niet in de bron. Wij nemen elk signaal.
4. [aanname] "Too close to the previous entry" is niet gedefinieerd. Onze keuze staat in 4.6, met alternatieven als gevoeligheid.
5. [aanname] "Below the 200 EMA" noemt geen afstand. Wij leggen de stop precies op de EMA-waarde bij de eerste instap en houden hem daar.
6. [aanname] De EMA van 4 uur op een grafiek van 30 minuten: TradingView kan op historische bars de waarde van een nog niet afgesloten bar van 4 uur tonen. Wij gebruiken alleen de laatste afgesloten bar van 4 uur. Dat is strenger dan wat de maker mogelijk zag.
7. [geverifieerd] De bron zegt "Bitcoin USD" zonder beurs. Wij gebruiken BTCUSDT van Binance (test J). Prijsverloop vrijwel gelijk, kosten en kleine verschillen in de koers niet.

## 4. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de video naar regels te vertalen.

**4.1 Markt en data.** BTCUSDT spot 30 minuten van Binance, `BTCUSDT_30m_binance.csv` uit test J (137.887 bars, eerste bar 1 januari 2019 00:00 UTC, laatste 15 november 2026 08:30 UTC, SHA-256 8ed44f29...). Bars van 4 uur worden gemaakt uit acht bars van 30 minuten, beginnend op 00:00, 04:00, 08:00, 12:00, 16:00 en 20:00 UTC, de indeling van Binance en TradingView.

**4.2 Trendfilter (kleur-EMA op 4 uur).** EMA(200) op het slot van de bars van 4 uur. Exact de openbare code van de maker, op de bars van 4 uur: groen als het slot nu en 5, 10, 15, 20, 30, 40 en 50 bars terug elk boven de EMA van die bar lag; rood als ze elk eronder lagen; anders geen kleur. Voor een bar van 30 minuten geldt de kleur en de EMA-waarde van de laatste afgesloten bar van 4 uur.

**4.3 MACD.** MACD(12, 26, 9) op het slot van 30 minuten, de standaard, zoals in test A.

**4.4 Signaal op bar t (30 minuten).**
- Long: MACD(t-1) ≤ signaal(t-1) en MACD(t) > signaal(t), MACD(t) < 0 en signaal(t) < 0, kleur-EMA groen, slot(t) boven de EMA van 4 uur.
- Short: MACD(t-1) ≥ signaal(t-1) en MACD(t) < signaal(t), MACD(t) > 0 en signaal(t) > 0, kleur-EMA rood, slot(t) onder de EMA van 4 uur.

**4.5 Variant Z, zonder spreiden.** Instap op het slot van de signaalbar. Stop: de EMA van 4 uur op dat moment (4.2), vast tot de uitstap. R = afstand van instap tot stop. Doel: instap plus 0,5R. Eén positie tegelijk; signalen tijdens een open positie vervallen.

**4.6 Variant G, gespreid.** Een setup begint bij een signaal als er geen positie openstaat. Instap 1 op het slot, stop S = de EMA van 4 uur op dat moment, vast voor de hele setup. Zolang de positie openstaat, wordt een nieuw signaal in dezelfde richting instap 2, en daarna instap 3, als:
- de instapprijs minstens 10% van de afstand (instap 1 tot S) lager ligt dan de vorige instap (short: hoger);
- de instapprijs nog boven S ligt (short: eronder).
Elke instap riskeert 1% van de rekening tot S, dus grootte_i = 1% / (instap_i - S). Gemiddelde instapprijs = naar grootte gewogen gemiddelde. Doel na k instappen: gemiddelde plus m_k maal (gemiddelde - S), met m_1 = m_2 = 0,25 en m_3 = 0,5 (short gespiegeld). Na de derde instap komen er geen meer bij. De setup eindigt op het doel of op S; daarna mag een nieuwe setup beginnen vanaf de volgende bar.

**4.7 Minimale stop.** Is de afstand van instap 1 tot S kleiner dan 0,5% van de instapprijs, dan geen trade of setup (de kosten zouden alles bepalen). Signalen met het slot aan de verkeerde kant van S bestaan niet door 4.4.

**4.8 Uitstap en einde van de data.** Geen tijdslimiet. Wat aan het eind van de data openstaat, sluit op het laatste slot, apart gemeld.

## 5. De drie vaste regels

**Kosten.** 0,06% per kant (0,05% takerfee plus 0,01% slippage), per instap en per uitstap van elk deel, zoals test J. Verrekend in R (variant Z) en in procent van de rekening (variant G). Gevoeligheid: 0, 0,12% en 0,20% per round trip. Geen hefboom, geen funding.

**Volgorde.** Bar voor bar op 30 minuten. Per bar eerst de stop, dan het doel; raakt één bar beide, dan telt hij als stop. Opent een bar al voorbij de stop of het doel, dan uit op de open. Een instap of bijkoop gebeurt op het slot; het nieuwe doel geldt vanaf de volgende bar. Op de bar waarop een setup eindigt, begint geen nieuwe.

**Controlegroep.** 10.000 runs, seed 41. Opeenvolgend proces door de tijd, met hetzelfde filter vanaf het begin (les uit test J en K).
- **Null A, beslissend:** de MACD-kruising wordt vervangen door een willekeurig signaal. Op elke bar van 30 minuten waarop het filter van 4.4 zonder de MACD-voorwaarden geldt (kleur-EMA groen en slot boven de EMA, of rood en eronder), vuurt een signaal met kans p in de richting van het filter. p is per periode zo gekozen dat het aantal signalen gelijk is aan dat van de regel. Daarna exact dezelfde regels: zelfde stop, minimale stop, bijkoopregels, doelen en kosten. Apart voor variant Z en variant G. Toetst wat de MACD-kruising onder of boven de nullijn toevoegt bovenop het trendfilter.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 6 jaar op 30 minuten, random walk zonder drift met 60% volatiliteit per jaar, opgebouwd uit stapjes van 1 minuut (open, hoog, laag, slot per 30 minuten), seed 7, 2.000 runs per set. Voor beide varianten.

Grens per variant: gemiddeld percentiel tegen Null A tussen 35 en 65, hooguit 3 van 24 boven 95.

## 7. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | Vanaf de eerste bar met een geldige kleur-EMA (200 plus 50 bars van 4 uur opwarmen, rond 11 februari 2019) tot en met de laatste volle dag in de data (14 november 2026) | **Beslissend** voor C1 tot en met C5 |
| P0 | 28 september 2020 tot en met 27 september 2024 | Reproductie van "the last four years". Komen we bij 73% en 87%? Niet beslissend |
| P2 | 28 september 2024 tot en met 14 november 2026 | Na de video. Aanvullend |
| P3 | Per jaar binnen P1, en long en short apart | Verdeling. Onder 100 trades of setups: onvoldoende |

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd in P1 als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate (G) ligt onder 87% |
| C2 | De bovengrens van het 95%-interval van de winrate (Z) ligt onder 73% |
| C3 | De bovengrens van het 95%-interval van het gemiddelde netto R (Z) ligt onder 0 |
| C4 | De bovengrens van het 95%-interval van het gemiddelde netto resultaat per setup (G) ligt onder 0 |
| C5a, C5b | Het gemiddelde netto resultaat ligt niet boven percentiel 95 van Null A |

Na de run: geen andere instellingen, stops, doelen, bijkoopregels of filters. Blijft een claim staan, dan "niet gefalsifieerd in deze meting", niet "werkt".

Gevoeligheid, vooraf vastgelegd en niet beslissend:
- bijkoopafstand: elke lagere prijs telt (0%), en 25% van de afstand instap 1 tot S;
- minimale stop: geen minimum, en 1,0%;
- gewone 200 EMA van 4 uur zonder kleurvoorwaarde;
- kosten 0, 0,12% en 0,20% per round trip.

## 9. Wat ik rapporteer, ongeacht de uitkomst

De trechter: bars na de opwarmperiode, bars met groene of rode kleur-EMA, MACD-kruisingen in de juiste richting, aan de juiste kant van de nullijn, vervallen door de minimale stop, vervallen tijdens een open positie (Z), bijkopen geweigerd door de afstandsregel (G), trades en setups. Verdeling van het aantal instappen per setup (1, 2 of 3).

Per periode en variant: aantal, winrate (95%), gemiddeld netto resultaat (95%), profit factor, mediane stopafstand in procent tegenover de kosten, breakeven-winrate na kosten, beste en slechtste uitkomst, langste reeks verliezen, gemiddelde looptijd. Percentielen tegen Null A.

Extra vergelijking (niet getoetst): dezelfde eerste instappen als variant G, maar met één positie en doel 0,25R. Zo is te zien hoeveel van de winrate door het kleine doel komt en hoeveel door het spreiden. De gevoeligheden. De ruiscontrole.

## 10. Volgende stap

1. Goedkeuring (of aanpassing). SHA-256 in het meetlog.
2. Script `structured_control.py`: eerst kleur-EMA, MACD en de bijkooprekening controleren tegen handberekening, dan de ruiscontrole uit 6.
3. Run in de cloud op de BTCUSDT-export van test J.
4. Code en data op GitHub vóór publicatie.
