# Hypothese: RSI(2)-pullback op de S&P 500 (test E)

Datum: 8 november 2026 · Bron: een artikel van een tradingauteur (21 feb 2007); bron met naam staat in de privéprojectbestanden · Status: **versie 1.0, vooraf vastgelegd en goedgekeurd op 8 november 2026 (Null A beslissend, P0 via het browserpaneel, Wilder-RSI), nog geen koersdata bekeken**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder wordt vastgelegd vóór de eerste run. Na de run wordt niets aangepast. Blijkt een keuze onhoudbaar, dan komt er een nieuwe versie met een nieuwe datum, en blijft deze uitkomst gewoon staan.

## 1. Wat de bron belooft

[geverifieerd, artikel] Regels: S&P 500 boven zijn 200-daags SMA; RSI(2) op dag 1 onder 65, op dag 2 lager dan dag 1, op dag 3 lager dan dag 2; kopen op de slotkoers van dag 3; verkopen als RSI(2) boven 75 sluit. Alleen long. Geen stop.

[geverifieerd] Toetsbare claims:

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | 84,31% van de trades is winstgevend (86 van 102, 1995 tot en met 2006) | Winrate met 95%-interval |
| C2 | De regel verdient geld: 1.013,90 punten in 12 jaar | Gemiddeld netto rendement per trade in procent, met interval |
| C3 | De instap (drie dalende RSI-dagen in een stijgende markt) kiest betere dagen dan toeval | Echt resultaat tegen de controlegroep |

## 2. Wat dit ontwerp sterk maakt, en zwakke plekken vooraf

1. [geverifieerd] De claim heeft een vaste einddatum: 31 december 2006. Alles daarna kon de bron niet zien. De beslissende meting is daarom 1 januari 2007 tot en met de laatste beschikbare dag: een echte meting buiten de periode van de bron.
2. [geverifieerd, Wilson-interval] Ook als 84,31% de echte winrate is, ligt het 95%-interval over 102 trades tussen 76,0% en 90,1%. Een lagere winrate in een andere periode is dus pas betekenisvol als hij onder 76% zakt.
3. [aanname] Een uitstap zonder stop op een index met opwaartse drift geeft vaak een hoge winrate, ook bij willekeurige instap: wie lang genoeg wacht, ziet meestal een stijgende dag. Een hoge winrate alleen zegt daarom weinig; C3 beslist.
4. [aanname] De regel lijkt op Buy the Dip (test van 2 nov, niet gefalsifieerd): beide kopen een korte daling in een index. De uitkomsten zijn niet onafhankelijk van elkaar.
5. [geverifieerd] De bron zegt niets over kosten. Op een index-ETF of future zijn de kosten per round trip klein vergeleken met een gemiddelde trade [aanname, wordt gemeten].

## 3. Mechanische vertaling (vast)

Alle punten hieronder zijn **[aanname]**: keuzes om de tekst naar regels te vertalen.

**3.1 Markt en data.** S&P 500-koersindex (^GSPC), dagslotkoersen van Yahoo Finance, dezelfde bron als Buy the Dip (3 jan 2000 tot 30 okt 2026, nog niet geopend voor deze test). Voor de replicatie van 1995 tot 2006 is een langere reeks nodig, vanaf 1994 (zie 5).

**3.2 RSI(2).** Wilder-RSI met periode 2 op de slotkoers (afwaardering met alpha 1/2, de standaardberekening in de meeste platforms). Opwarmperiode: de eerste 250 dagen tellen niet mee.

**3.3 SMA 200.** Eenvoudig gemiddelde van de laatste 200 slotkoersen, tot en met de signaaldag.

**3.4 Signaal op dag t (= dag 3).** slot(t) > SMA200(t), en RSI(t-2) < 65, en RSI(t-1) < RSI(t-2), en RSI(t) < RSI(t-1). Het filter geldt op dag 3, de dag van instap [aanname: de bron zegt niet op welke dag].

**3.5 Instap.** Op de slotkoers van dag t.

**3.6 Uitstap.** Op de slotkoers van de eerste dag na de instap waarop RSI(2) boven 75 sluit. Geen stop, geen tijdslimiet. Open aan het eind van de data: sluiten op de laatste slotkoers en apart melden.

**3.7 Eén positie tegelijk.** Een nieuw signaal tijdens een open trade vervalt.

## 4. De drie vaste regels

**Kosten.** 2 basispunten round trip per trade, gelijk aan Buy the Dip [geverifieerd, README buy-the-dip]. Gevoeligheid: 0, 2 en 4 bp.

**Volgorde.** Instap en uitstap op slotkoersen; de regel kent geen stop of target binnen de dag, dus het pad binnen de dag doet niet mee [geverifieerd, regels]. Gemeten wordt ook de diepste tussentijdse daling per trade (op slotkoersen), omdat zonder stop het risico daar zit.

**Controlegroep.** 10.000 runs, seed 23.
- **Null A, beslissend:** willekeurige instapdag uit de dagen waarop het slot boven de SMA200 ligt (zelfde filter als de regel), zelfde uitstapregel (RSI(2) boven 75), zelfde aantal trades, één positie tegelijk. Toetst of de drie dalende RSI-dagen iets toevoegen bovenop het trendfilter.
- **Null B, aanvullend:** willekeurige instapdag zonder filter, zelfde uitstapregel. Gelijk aan Null A van Buy the Dip, zodat de twee tests vergelijkbaar zijn.

[aanname, gekozen op 8 nov] Null A met filter is strenger dan de nulmeting van Buy the Dip. Met Null B als beslissend zou de regel ook krediet krijgen voor het trendfilter, dat al decennia bekend is.

## 5. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P0 | 1 jan 1995 tot 31 dec 2006 | Replicatie: komen we in de buurt van 102 trades en 84,31%? Controle van de berekening, niet beslissend |
| P1 | 1 jan 2007 tot en met de laatste dag | **Beslissend**: buiten de periode van de bron |
| P2 | per jaar binnen P1 | Verdeling over de jaren, niet beslissend |

Aanvullend en niet beslissend: dezelfde regels op de Nasdaq 100 (^NDX) in P1.

[geverifieerd, README buy-the-dip] De bestaande Yahoo-reeks begint op 3 januari 2000. Voor P0 is ^GSPC vanaf januari 1994 nodig (200 dagen opwarmen plus RSI); die haal ik op dezelfde manier op als bij Buy the Dip. Lukt dat niet, dan vervalt P0 en blijft P1 beslissend.

## 6. Wanneer is het idee dood (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1 | De bovengrens van het 95%-interval van de winrate in P1 ligt onder 84,31% |
| C2 | De bovengrens van het 95%-interval van het gemiddelde netto rendement per trade in P1 ligt onder 0 |
| C3 | Het gemiddelde netto rendement per trade in P1 ligt niet boven percentiel 95 van Null A |

Valt C3, dan is het idee dood: niet repareren, niet optimaliseren, geen andere RSI-drempels, filters of uitstapregels proberen. Onder 100 trades in P1: "onvoldoende trades".

Blijft C3 staan, dan rapporteer ik het als "niet gefalsifieerd", met de beperkingen, en niet als "werkt".

## 7. Wat ik rapporteer, ongeacht de uitkomst

Aantal trades, winrate met interval, gemiddeld netto rendement per trade met bootstrap-interval, profit factor, percentiel tegen Null A en Null B, resultaat per jaar, gemiddelde en langste duur, grootste verliezer, diepste tussentijdse daling per trade, som van de beste 5% trades naast het totaal, de drie kostenniveaus, en het rendement van kopen en vasthouden in dezelfde periode ter vergelijking (geen controlegroep).

## 8. Volgende stap

1. Goedgekeurd op 8 november 2026. SHA-256 van het origineel staat in het privémeetlog.
2. Meetscript `rsi2_control.py` schrijven en eerst draaien op 24 synthetische reeksen (random walk met dezelfde drift en volatiliteit als een index, gekozen vóór het zien van ^GSPC: 7% per jaar, 18% volatiliteit [aanname]). Daar moet de regel gemiddeld niet beter uitkomen dan Null A, en moeten de percentielen gelijkmatig verdeeld zijn. Pas dan de echte data.
