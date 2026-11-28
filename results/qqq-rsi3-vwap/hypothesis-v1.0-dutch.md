# Hypothese: RSI(3) + EMA(100) + rollende VWAP op QQQ (test T)

Datum: 28 november 2026 · Bron: Substack-post, video en Instagram-post van een website voor strategie-onderzoek · Status: **versie 1.0, vooraf vastgelegd en goedgekeurd door Nullius op 28 november 2026 (K1 tot en met K5 allemaal A). Nog geen QQQ-koersdata geopend.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de eerste echte run verandert er niets; een nieuwe versie krijgt een nieuwe datum.

## 1. De claim

[geverifieerd, bronnen gelezen 28 nov 2026] Regels, op het dagslot van QQQ, alle drie tegelijk:
- RSI(3) onder 22;
- de 100-daagse EMA hoger dan vijf handelsdagen eerder (de EMA vergeleken met zichzelf, het slot mag onder de EMA liggen);
- het slot minstens 1% onder de 10-daagse rollende VWAP, berekend op "daily typical price and volume" (video).

Kopen op de open van de volgende sessie. Substack: "Starting the session after entry, sell at the close when RSI(3) is above 55." Video: "exit after RSI recovers above 55". Eén positie tegelijk. Geen stop, geen target. Periode in beide bronnen: 1999 tot september 2026. De video zegt dat de resultaten zonder commissie en slippage zijn.

Er zijn twee versies van de uitkomst:

| Versie | Bron | Trades | Winrate | Profit factor | RSI(3) alleen | Max. drawdown |
|---|---|---|---|---|---|---|
| A | video, 9 okt 2026 | 215 | 78,6% | 3,94 | PF 2,27 | ca. $10.943 bij vaste $100.000 per trade |
| B | Substack, 12 nov 2026 (gewijzigd 19 nov) | 215 | niet genoemd | 3,54 "before costs" | PF 2,19 | niet genoemd |

Video, deelperiodes: PF 5,62 (1999-2008), 3,29 (2009-2017), 3,47 (2018 tot sep 2026). Video: RSI + EMA zonder VWAP PF 3,08 [geverifieerd, transcript].

## 2. Toetsbare claims

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Profit factor 3,94 (A) of 3,54 (B) | Profit factor netto, met 95%-interval (bootstrap per trade) |
| C2 | Winrate 78,6% (A) | Winrate met 95%-interval (Wilson) |
| C3 | Max. drawdown ca. $10.943 bij vaste $100.000 per trade (A) | Beschrijvend: grootste daling van de som van gesloten trades, $100.000 per trade |
| C4 | Alle drie deelperiodes PF boven 3 (A) | Beschrijvend: elke periode heeft minder dan 100 trades |
| C5 | De drie voorwaarden kiezen betere instapdagen dan toeval in dezelfde trend (impliciet: "a temporary pullback inside a stronger backdrop") | Gemiddeld netto rendement per trade tegen Null A |
| C6 | EMA en VWAP maken RSI(3) beter dan RSI(3) alleen ("the filters did what we wanted them to do") | Gemiddeld netto rendement per trade tegen Null B: evenveel trades, willekeurig gekozen uit de RSI(3)-signalen zonder filters |

## 3. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De bron toont de hele QQQ-geschiedenis tot sep 2026. Er is geen QQQ-periode die de bron niet kon zien, behalve okt en nov 2026 (te kort). Reproductie bewijst daarom weinig; C5 en C6 (tegen de controlegroepen) beslissen.
2. [geverifieerd] Twee profit factors (3,94 en 3,54) en twee RSI-basislijnen (2,27 en 2,19) bij hetzelfde aantal trades. Mogelijk een andere RSI-variant of uitstapdag tussen de versies [aanname]. Wij toetsen beide getallen; de regels zijn gelijk.
3. [geverifieerd, rekenkunde] Bij 215 trades loopt het 95%-interval rond 78,6% van ongeveer 72,6% tot 83,6%. C2 valt pas als de gemeten winrate onder ongeveer 73,2% ligt.
4. [aanname, beredeneerd] Een uitstap zonder stop op een index met opwaartse drift geeft ook bij willekeurige instap een hoge winrate. Hoge winrate alleen zegt weinig.
5. [geverifieerd, logboek] Vierde long-only mean-reversiontest op een Amerikaanse index, na Buy the Dip, E (RSI(2)-pullback) en I (Triple RSI), alle drie niet gefalsifieerd. De uitkomsten zijn niet onafhankelijk; QQQ en SPY bewegen grotendeels samen.
6. [aanname] Elke deelperiode heeft ongeveer 70 trades: onvoldoende voor een eigen oordeel, alleen beschrijvend.
7. [geverifieerd, beschrijving] Een ander kanaal draaide de regels al na (PF 4,00 zonder kosten, vanaf 2016 PF 2,20 op 85 trades). Dat is een reproductie, geen controle tegen toeval.

## 4. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**4.1 Markt en data.** QQQ dagkoersen (open, hoog, laag, slot, volume) van Yahoo Finance, vanaf de eerste handelsdag (10 maart 1999) tot de laatste afgesloten dag vóór de run. Prijsreeks volgens K5. Splitsingen zijn in de Yahoo-reeks verwerkt, ook in het volume. Ruwe download met SHA-256 in deze map.

**4.2 RSI(3).** Periode 3 op het slot, variant volgens K1.

**4.3 EMA(100).** Exponentieel gemiddelde van het slot, alpha 2/101, gestart met het eenvoudige gemiddelde van de eerste 100 slotkoersen. Voorwaarde: EMA(t) > EMA(t-5).

**4.4 Rollende VWAP(10).** Typische prijs TP = (hoog + laag + slot) / 3. VWAP(t) = som van TP × volume over de laatste 10 handelsdagen tot en met t, gedeeld door de som van het volume over die dagen. Voorwaarde: slot(t) ≤ 0,99 × VWAP(t).

**4.5 Opwarmen.** Een signaal kan pas vanaf de eerste dag waarop EMA(t-5) bestaat (handelsdag 105). Zo blijft 1999 grotendeels in de test, zoals bij de bron.

**4.6 Signaal op dag t.** RSI(t) < 22, EMA(t) > EMA(t-5) en slot(t) ≤ 0,99 × VWAP(t).

**4.7 Instap.** Op de open van dag t+1.

**4.8 Uitstap.** Op het slot van de eerste controledag waarop RSI(3) boven 55 staat (een stand, geen kruising). Eerste controledag volgens K2. Geen stop, geen target, geen tijdslimiet. Open aan het eind van de data: sluiten op het laatste slot en apart melden.

**4.9 Eén positie tegelijk.** Een signaal tijdens een open trade vervalt. Een signaal op de uitstapdag zelf telt mee (instap de dag erna).

## 5. De drie vaste regels

**Kosten.** 2 basispunten round trip per trade, gelijk aan Buy the Dip, E en I. Gevoeligheid: 0, 2, 4 en 10 bp. De bron rekent zonder kosten; bij gemiddeld ruim 1% per trade [aanname] verschuift 2 bp de PF nauwelijks.

**Volgorde.** Instap op de open, uitstap op het slot. De regel kent geen stop of target binnen de dag, dus het pad binnen de dag beslist niets [geverifieerd, regels]. Wel gemeten per trade: het laagste dagdal tegen de instapprijs, omdat zonder stop het risico daar zit.

**Controlegroepen.** 10.000 runs, seed 38. Eerst de controle bekijken, dan de regel.
- **Null A, beslissend voor C5:** willekeurige signaaldagen uit de vijver van K3, instap op de volgende open, evenveel trades als de regel, één positie tegelijk. Elke nep-trade krijgt de looptijd van een echte trade (de echte looptijden, geschud). Toetst of RSI en VWAP betere dagen kiezen dan een willekeurige dag, met dezelfde tijd in de markt.
- **Null B, beslissend voor C6:** willekeurige dagen uit de dagen met RSI(3) < 22 (zonder EMA- en VWAP-filter), instap op de volgende open, eigen uitstapregel (4.8), evenveel trades als de regel, één positie tegelijk. Toetst of de twee filters meer doen dan het aantal trades verkleinen.

## 6. Ruiscontrole vóór de echte data (vast)

24 nepmarkten van 6.950 handelsdagen (ongeveer 27,6 jaar), willekeurige wandeling met dagrendementen zonder geheugen, drift 0,04% en volatiliteit 1,8% per dag [aanname: ruwweg QQQ]. Open = vorig slot × (1 + N(0; 0,4%)); hoog en laag = hoogste en laagste van open en slot, × (1 ± |N(0; 0,6%)|); volume lognormaal en onafhankelijk van de prijs. Seed 7.

Grens, gelijk aan eerdere tests: percentiel tegen Null A en tegen Null B elk gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95. Zakt de controle, dan eerst het script herstellen, vóór de echte data.

## 7. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | 10 mrt 1999 tot en met de laatste afgesloten dag | **Beslissend** voor C1, C2, C5, C6 |
| P0 | 10 mrt 1999 tot en met 30 sep 2026 | Reproductie: 215 trades, 78,6%, PF 3,94 of 3,54, drawdown ca. $10.943? Niet beslissend |
| P2 | 1999-2008, 2009-2017, 2018 tot 30 sep 2026 | C4 en verdeling. Onder 100 trades: onvoldoende |
| P4 | 1 okt 2026 tot de laatste dag | Na de bron. Beschrijvend, zeer weinig trades |
| P3 | SPY, 29 jan 1993 tot de laatste dag (volgens K4) | Andere markt, zelfde regels. Aanvullend, niet beslissend |

## 8. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd in P1 als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de netto PF ligt onder 3,94 (A); apart gemeld tegen 3,54 (B) |
| C2 | De bovengrens van het 95%-interval van de winrate ligt onder 78,6% |
| C3, C4 | Niet falsifieerbaar in deze meting; alleen naast de claim gezet |
| C5 | Het gemiddelde netto rendement per trade ligt niet boven percentiel 95 van Null A |
| C6 | Het gemiddelde netto rendement per trade ligt niet boven percentiel 95 van Null B |

Na de run: geen andere RSI-periodes, drempels, EMA- of VWAP-lengtes, filters of uitstappen. Blijft een claim staan, dan "niet gefalsifieerd in deze meting", niet "werkt".

## 9. Keuzes (vastgelegd 28 nov 2026: alle vijf A)

| Keuze | A (gekozen) | B |
|---|---|---|
| K1 RSI-variant | Wilder (afvlakking 1/3), de standaard in Amibroker; de bron noemt Cutler alleen bij strategie 2 [aanname] | Cutler (eenvoudig gemiddelde van winst en verlies over 3 dagen) |
| K2 Eerste controledag uitstap | Slot van de dag ná de instapdag (letterlijk "Starting the session after entry") | Al het slot van de instapdag zelf |
| K3 Vijver Null A | Dagen waarop de EMA-voorwaarde geldt: toetst RSI en VWAP binnen dezelfde trend (zoals test I) | Alle handelsdagen: toetst het hele pakket, trendfilter inbegrepen |
| K4 SPY als extra markt (P3) | Ja, aanvullend; SPY met open, hoog, laag, slot en volume staat al in `Test\triple-rsi\spy_raw.json` (8.507 dagen, alleen metadata bekeken) [geverifieerd]; voor de run opnieuw ophalen tot de laatste dag | Nee |
| K5 Prijsreeks | Slot zonder dividend (close), zoals E en I; adjclose als gevoeligheid | Adjclose beslissend |

De andere variant van K1 en K2 rapporteer ik als gevoeligheid naast P0, zodat zichtbaar wordt welke variant de bron het dichtst benadert. Beslissend blijft de gekozen variant in P1.

## 10. Wat ik rapporteer, ongeacht de uitkomst

De trechter: handelsdagen, dagen met RSI(3) < 22, met EMA-voorwaarde, met VWAP-voorwaarde, signalen, vervallen tijdens een open trade, trades. Per periode: trades, winrate (95%), gemiddeld netto rendement (95%), PF (95%), slechtste trade, laagste dagdal, gemiddelde looptijd, tijd in de markt, drawdown bij $100.000 per trade, en kopen en vasthouden over dezelfde periode. Percentielen tegen Null A en Null B. Kostengevoeligheid, adjclose, de varianten van K1 en K2. De ruiscontrole.

## 11. Volgende stap

1. Gedaan 28 nov: K1 tot en met K5 A, versie 1.0 vast, SHA-256 in het meetlog, Engelse versie voor GitHub.
2. Script `qqq_rsi3_vwap_control.py` op basis van test I (`triple_rsi_control.py`), eerst de ruiscontrole uit 6.
3. QQQ-data ophalen via Chrome of het paneel (Yahoo), datacontrole (alleen metadata), dan run 01.
4. Code en data op GitHub vóór publicatie.
