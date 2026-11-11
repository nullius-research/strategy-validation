# Hypothese: Box Theory, blind uitgevoerd (test G), versie 1.1

Datum: 11 november 2026 · Bron: een video van een tradingkanaal (mei 2025) en twee vervolgvideo's (mei en september 2026); bron met naam staat in `claim-bron.md` (privé) · Status: **versie 1.1, 11 november 2026, goedgekeurd (optie A). Vervangt v1.0 alleen in de nepmarkt van de ruiscontrole (5), omdat v1.0 de ruiscontrole niet haalde (uitkomst in `noise_24sets_v1.0_failed.txt`, oorzaak in `noise_granularity.txt`). Regel, controlegroep, kosten, periodes en drempels ongewijzigd. Nog geen uitkomsten op echte data bekeken; van de Nasdaq-export is alleen de metadata gecontroleerd**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst staan.

## 1. Wat de bron belooft

[geverifieerd, transcript] De regel zoals de bron hem voordoet:
- Box: de high en de low van de vorige dag, met een lijn ongeveer in het midden.
- Bij de bovenkant verkopen, bij de onderkant kopen, niet in het midden handelen.
- Stop: net boven de high van de dag (short), net onder de low (long).
- Target: het midden of de andere kant van de box, "2:1 to 3:1".
- Breekt de koers in de eerste 15 tot 20 minuten door de box, dan de box oprekken naar de nieuwe high of low. Ook oprekken naar een hogere high of lagere low van de premarket.
- Voorbeeld op de Nasdaq, 5 minuten. Volgens de bron werkt elk tijdframe.
- Zonder kaarsen of indicatoren: "blindly buy".

[geverifieerd, transcript] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | "three winners, one loser" bij blind kopen en verkopen op de box, dus 75% | Winrate met 95%-interval |
| C2 | De regel verdient geld ("for like $4,000") | Gemiddelde netto R per trade met interval |
| C3 | "that accurate by blindly buying and selling at premium levels": de randen van de box kiezen een betere richting dan toeval | Echt resultaat tegen de controlegroep |

[geverifieerd] Niet toetsbaar en buiten deze meting: "six-figure a month", "$10,000/month" (hangt af van inzet), en de aanvulling met kaarspatronen voor "elite"-niveau. De bron zegt zelf dat hij niet aanraadt om blind te handelen. Deze test meet de blinde versie die hij voordoet en "accurate" noemt. Dat staat in elke publicatie.

## 2. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De claim van 75% rust op 4 trades in één video. Bij een echte winrate van 30% is de kans op 3 of meer winnaars in 4 trades 8,4% [geverifieerd, binomiaal].
2. [geverifieerd, rekenkundig] Bij de vertaling hieronder (stop 0,2 en target 0,5 boxhoogte) is break-even een winrate van 0,2 / 0,7 = 28,6% vóór kosten. Op een random walk zonder drift is de kans om +0,5 te raken vóór -0,2 ook 28,6%. Een hoge winrate is bij deze verhouding dus niet te verwachten; 75% zou uitzonderlijk zijn.
3. [aanname] "Net boven de high van de dag" geeft op het moment van instap een stop van bijna nul. Een vaste minimale afstand is nodig, anders eten de kosten alles op (les uit de supply-demand-test). Die afstand is een keuze van ons.
4. [aanname] Het oprekken van de box na een doorbraak koppelt de bron aan een eerder niveau in de grafiek ("does it coincide with any value premium level in the past"). Dat is niet mechanisch. Wij rekken één keer op, op een vast moment.
5. [aanname] De bron handelt de Nasdaq-future. Wij gebruiken een CFD op de Nasdaq 100 van één broker. Prijsverloop is nagenoeg gelijk, kosten en tijden niet.

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Data.** Beslissend: Nasdaq 100 CFD (NAS100 of USTEC), M1, MT5-export van dezelfde broker als US500 (IC Markets EU, demo). Aanvullend en niet beslissend: US500 M1, 1 jan 2019 tot en met 30 okt 2026 (`US500_M1_2019-2026.csv`, al in huis). Tijden in servertijd; de reguliere sessie (9:30 tot 16:00 New York) bepaalt het script per dag uit de sprong in tickvolume bij de opening, zoals in de supply-demand-test.

**3.2 Box.** Per handelsdag d:
- Basis: de high en low van de vorige brokerdag (de daggrafiek, zoals de bron die gebruikt).
- Premarket: ligt de high of low van dag d vóór 9:30 buiten de basis, dan schuift die kant mee.
- Opening: om 9:45 (na 15 minuten sessie) schuift elke kant nog één keer mee naar de high of low van dag d tot dan.
- Daarna ligt de box vast tot het slot. Middenlijn M = (top + bodem) / 2. Boxhoogte H = top − bodem.

**3.3 Instap.** Tussen 9:45 en 15:30 New York:
- Short: de eerste M1-bar waarvan de high de top raakt. Instap op de top (limietorder).
- Long: de eerste M1-bar waarvan de low de bodem raakt. Instap op de bodem.
- Hoogstens één short en één long per dag, en één positie tegelijk. Raken beide kanten in dezelfde bar, dan geen trade in die bar.

**3.4 Stop.** 0,2 × H voorbij de rand: short stop = top + 0,2H, long stop = bodem − 0,2H. Is 0,2H kleiner dan 10 indexpunten (Nasdaq) of 2,5 punten (US500), dan geen trade die dag aan die kant.

**3.5 Target.** De middenlijn M. Dat is 0,5H van de instap, dus 2,5R vóór kosten, binnen de "2:1 to 3:1" van de bron.

**3.6 Uitstap.** Stop, target, of het slot van de sessie (16:00 New York) op de slotkoers van de laatste M1-bar.

## 4. De drie vaste regels

**Kosten.** Spread uit de SPREAD-kolom van de export, per instapbar, plus slippage van 1 punt per kant (Nasdaq) of 0,25 punt per kant (US500) [aanname]. Geen commissie [aanname, zoals US500 in de supply-demand-test]. Gevoeligheid: slippage 0, 1 en 2 keer.

**Volgorde.** Het pad wordt bar voor bar op M1 doorlopen. Raakt één bar zowel stop als target, dan telt hij als stop. Ook de instapbar zelf telt mee voor de stop (niet voor het target).

**Controlegroep.** 10.000 runs, seed 23. Bootstrap per handelsdag.
- **Null A, beslissend (muntworp):** dezelfde instapmomenten, prijzen en afstanden als de echte trades, richting willekeurig. Bij de omgekeerde richting liggen stop en target gespiegeld (stop 0,2H aan de andere kant, target 0,5H verder). Toetst of tegen de rand in handelen beter is dan met de rand mee.
- **Null B, aanvullend (plaats in de box):** per echte trade een willekeurige M1-bar op een willekeurige handelsdag in dezelfde maand, tussen 9:45 en 15:30, richting willekeurig, dezelfde stop- en targetafstand in boxhoogtes van die dag. Toetst of de rand iets toevoegt tegenover een willekeurige plek.

[geverifieerd, methode] Een muntworp is hier de juiste nulmeting: de regel handelt long en short, binnen één dag, waar de drift van de index klein is tegenover de beweging. Het aandeel long en short wordt gerapporteerd.

## 5. Ruiscontrole vóór de echte data (vast)

24 synthetische reeksen van 5 jaar M1, random walk zonder drift met de beweeglijkheid van een index (20% per jaar) en een sessiestructuur (handelsdagen, premarket, sessie), seed 7 [aanname, gekozen vóór het zien van de data]. **v1.1:** de nepkoers beweegt in 60 stapjes per minuut (v1.0: 5). Bij 5 stapjes schoot de nepkoers bij de eerste aanraking gemiddeld een paar punten over de rand, terwijl de instap op de rand wordt geboekt. Dat benadeelt de regel en bevoordeelt de spiegeltrade evenveel: regel min spiegel -0,059 R per trade bij 5 stapjes, -0,002 bij 60 (standaardfout 0,022) [geverifieerd, `noise_granularity.txt`].

Grens, gelijk aan de audit van 10 nov: gemiddeld percentiel tegen Null A tussen 35 en 65, hooguit 3 van 24 boven 95. Verwacht [geverifieerd, rekenkundig]: winrate rond 28,6% vóór kosten. Valt de ruiscontrole, dan eerst de controle herzien (nieuwe versie), pas daarna de echte data.

## 6. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | Nasdaq: 1 jan 2019 (of de eerste maand met gevulde SPREAD-kolom, als die later valt) tot en met de laatste volledige dag | **Beslissend** |
| P2 | Nasdaq: vanaf 22 mei 2025 (na de video) | Na de claim, niet beslissend |
| P3 | US500, 2019-2026 | Tweede markt, niet beslissend |
| P4 | per jaar | Verdeling, niet beslissend |

## 7. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate in P1 ligt onder 75% |
| C2 | De bovengrens van het 95%-interval van de gemiddelde netto R in P1 ligt onder 0 |
| C3 | De gemiddelde netto R in P1 ligt niet boven percentiel 95 van Null A |

Valt C3, dan is de regel dood: niet repareren, niet optimaliseren, geen andere stops, targets, tijden of boxdefinities proberen. Onder 100 trades in P1: "onvoldoende trades".

Blijft C3 staan, dan rapporteer ik het als "niet gefalsifieerd", met de beperkingen, en niet als "werkt".

## 8. Wat ik rapporteer, ongeacht de uitkomst

De trechter (handelsdagen, dagen met een raak van de top en van de bodem, trades na de minimale stop, trades na één positie tegelijk), aantal trades, winrate met interval, gemiddelde netto R met dagbootstrap (95%), profit factor, percentiel tegen Null A en Null B, aandeel long en short, resultaat per jaar, aandeel trades dat op het slot sluit, de drie kostenniveaus, mediane stopafstand in punten tegenover de kosten, langste reeks verliezen, en de som van de beste 5% trades naast het totaal.

## 9. Volgende stap

1. v1.0 goedgekeurd op 11 november 2026; ruiscontrole v1.0 gezakt; v1.1 goedgekeurd op 11 november 2026 (SHA-256 in de meetlog). De Engelse versie gaat mee.
2. Export van Nasdaq 100 M1 uit MT5. Datacontrole alleen op de metadata (bars per dag, SPREAD-kolom, tijden).
3. Meetscript `box_control.py`, eerst de ruiscontrole uit 5, dan de echte data.
4. Daarna, apart: de bijclaim over SPY na de opening (eigen hypothese).
