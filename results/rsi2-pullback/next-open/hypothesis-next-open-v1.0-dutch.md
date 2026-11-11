# Hypothese: RSI(2)-pullback, uitvoering op de opening (test E2)

Datum: 11 november 2026 · Aanleiding: reactie van een lezer onder artikel 9 (8 nov 2026) · Basis: test E, `hypothese-rsi2-pullback.md` v1.0 (8 nov 2026) · Status: **versie 1.0, 11 november 2026, goedgekeurd (controlegroep A: trekking gelijk aan test E), nog geen openingskoersen bekeken**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de run wordt niets aangepast. Test E (v1.0) blijft staan zoals gepubliceerd; dit is een aparte test, geen vervanging.

## 1. Waarom deze test

[geverifieerd, artikel 9] Test E koopt en verkoopt precies op de slotkoers van de signaaldag. Dat kan een lezer in de praktijk bijna niet: het signaal is pas bekend als de markt dicht is. Artikel 9 noemt dat zelf al een idealisering.

[geverifieerd, reactie lezer 8 nov] De lezer stelt voor: dezelfde regel uitvoeren op de opening van de volgende dag, de controlegroep op dezelfde manier laten handelen, en het resultaat naast de bevroren replicatie zetten in plaats van die te vervangen.

Deze test meet dus één ding: **overleeft de regel als je hem uitvoert zoals een lezer dat kan?** Het is geen parametervariant: regels, drempels, filter en periode zijn gelijk aan test E. Alleen het moment van kopen en verkopen verschuift.

## 2. Toetsbare claims (gelijk aan test E)

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | 84,31% van de trades is winstgevend | Winrate met 95%-interval |
| C2 | De regel verdient geld | Gemiddeld netto rendement per trade met interval |
| C3 | De instap kiest betere dagen dan toeval binnen het trendfilter | Echt resultaat tegen Null A, beide op de opening uitgevoerd |

## 3. Zwakke plekken, vooraf benoemd

1. [aanname] Een groot deel van een korte terugveer na een daling kan al in de nacht gebeuren, tussen slot en opening. Dan mist de uitvoering op de opening een deel van de winst. Dat is precies wat deze test meet; de richting van de uitkomst is onbekend.
2. [aanname] Ook de uitstap verschuift: de regel verkoopt pas de ochtend na de dag waarop RSI(2) boven 75 sloot. Een gat omhoog of omlaag in de nacht telt mee.
3. [aanname] Openingskoersen van een index zijn geen verhandelbare prijzen: een index-ETF of future opent op een iets andere koers. Dit blijft een benadering, maar wel een die een lezer kan nadoen.
4. [aanname] Yahoo-openingskoersen van oudere jaren zijn soms gelijk aan het slot van de dag ervoor (geen echte opening). Zie de datacontrole in 5.

## 4. Mechanische vertaling (vast)

Alles uit test E v1.0, paragraaf 3, blijft gelijk (Wilder-RSI(2), SMA 200 op slotkoersen, signaal op dag t met het filter op dag t, één positie tegelijk, opwarmperiode 250 dagen), met deze twee wijzigingen **[aanname]**:

**4.1 Instap.** Op de openingskoers van dag t+1, de eerste handelsdag na het signaal.

**4.2 Uitstap.** RSI(2) sluit boven 75 op dag j (eerste dag ná de signaaldag t). Verkoop op de openingskoers van dag j+1. Geen stop, geen tijdslimiet. Open aan het eind van de data: sluiten op de laatste slotkoers en apart melden.

**4.3 Volgende signaal.** Een nieuw signaal telt pas vanaf de dag ná de verkoopdag j+1 (dag j+1 zelf heeft een verkoop op de opening; een signaal op het slot van j+1 mag, want de positie is dan dicht) [aanname].

## 5. Data (vast)

- ^GSPC dagdata met openings- én slotkoersen, Yahoo Finance, dezelfde bron als test E. Bestaat de huidige reeks alleen uit slotkoersen, dan opnieuw ophalen via dezelfde route (browser) [aanname: de Yahoo-reeks bevat een kolom open].
- Datacontrole vóór de run, alleen op de koersen, niet op uitkomsten: aandeel dagen met open precies gelijk aan het vorige slot, en open buiten de dagrange (onder het laagste of boven het hoogste). Ligt in P1 meer dan 5% van de dagen op open = vorig slot, dan wordt dat gemeld en loopt de test toch, met die kanttekening.
- De slotkoersen moeten gelijk zijn aan de reeks van test E. Wijken ze af, dan eerst uitzoeken [controle].

## 6. De drie vaste regels

**Kosten.** 2 basispunten round trip, gevoeligheid 0, 2 en 4 bp. Gelijk aan test E.

**Volgorde.** Instap en uitstap op openingskoersen; geen stop of target binnen de dag. Gemeten wordt ook de diepste tussentijdse daling per trade op slotkoersen, vanaf de instapprijs.

**Controlegroep.** 10.000 runs, seed 23. Null A beslissend, Null B aanvullend, met dezelfde definities als test E, maar **op dezelfde uitvoering**: willekeurige signaaldag, instap op de opening van de dag erna, uitstap op de opening na de dag waarop RSI(2) boven 75 sluit.

Trekking van de controlegroep: **optie A gekozen** (11 nov 2026). Ter vastlegging de afweging:

| | A. Gelijk aan test E | B. Opeenvolgend, zoals test F v1.1 |
|---|---|---|
| Wat | Willekeurige volgorde, zonder overlap ("greedy"), precies als in test E | Wachttijd en volgorde zoals de regel zelf |
| Voordeel | Alleen de uitvoering verschilt van test E: de vergelijking is zuiver | Methodisch de nieuwste controle |
| Nadeel | Leunde bij test E tegen de regel (ruis gemiddeld 31,7) | Twee dingen tegelijk anders dan test E |
| Voorstel | **Ja**: de vraag van de lezer gaat alleen over de uitvoering | |

## 7. Ruiscontrole vóór de echte data (vast)

24 synthetische reeksen van 5.000 handelsdagen, 7% stijging per jaar en 18% beweeglijkheid (gelijk aan test E), elke dag opgesplitst in een nachtdeel (slot tot opening) en een dagdeel (opening tot slot). Het nachtdeel krijgt 30% van de variantie [aanname, gekozen vóór het zien van openingskoersen]. Seed 7.

Grens, gelijk aan de audit van 10 nov: gemiddeld percentiel tegen Null A tussen 35 en 65, hooguit 3 van 24 boven 95. Ligt het gemiddelde onder 35 (zoals bij test E, 31,7), dan leunt de controle tegen de regel: een positieve uitkomst blijft dan geldig, een negatieve wordt gemeld met die kanttekening.

## 8. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | 1 jan 2007 tot en met de laatste dag | **Beslissend**, gelijk aan test E |
| P2 | per jaar binnen P1 | Verdeling, niet beslissend |

Geen P0 (1995-2006): de openingskoersen van die jaren zijn minder betrouwbaar [aanname], en de replicatie van de bron is al gedaan in test E.

## 9. Wanneer is het idee dood (vooraf, gelijk aan test E)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate in P1 ligt onder 84,31% |
| C2 | De bovengrens van het 95%-interval van het gemiddelde netto rendement per trade ligt onder 0 |
| C3 | Het gemiddelde netto rendement per trade ligt niet boven percentiel 95 van Null A |

Valt C3: dan publiceren als "de gepubliceerde regel overleefde op het slot, de versie die een lezer kan uitvoeren niet". Beide uitkomsten blijven naast elkaar staan. Geen andere uitvoeringstijden (bijvoorbeeld slot van de dag erna) proberen.

Blijft C3 staan: rapporteren als "niet gefalsifieerd, ook op de opening", met de beperkingen, niet als "werkt".

## 10. Wat ik rapporteer, ongeacht de uitkomst

Alles uit test E paragraaf 7, plus naast elkaar: test E (slot) en E2 (opening) voor aantal trades, winrate, gemiddeld netto rendement, percentiel tegen Null A. En het gemiddelde nachtrendement op instapdagen en uitstapdagen van de regel, zodat zichtbaar is waar het verschil zit.

## 11. Volgende stap

1. Goedgekeurd op 11 november 2026 (optie A). SHA-256 in het meetlog.
2. Script `rsi2_next_open.py` op basis van `rsi2_control.py`; eerst de ruiscontrole uit 7.
3. Datacontrole uit 5 op de echte reeks, dan de run.
4. Code en data op GitHub vóór publicatie; antwoord onder de reactie van de lezer met de uitkomst, welke kant ook op.
