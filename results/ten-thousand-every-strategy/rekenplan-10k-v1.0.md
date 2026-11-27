# Rekenplan video B · $10.000 in elke geteste strategie

Versie 1.0 · 26 november 2026 · Nullius Research · Status: **vastgelegd 26 nov 2026 na akkoord van de redactie. Nog geen dollarbedrag berekend.**
Alleen de datums van de tradelijsten zijn bekeken (welke jaren erin zitten), geen resultaten [geverifieerd].

## 1. Wat dit is, en wat niet

- Een **herberekening van trades die al gemeten en gepubliceerd zijn**, omgezet naar dollars op één gelijke manier. Geen nieuwe test, geen nieuwe regels, geen nieuwe controlegroep.
- Doel: per strategie laten zien wat er van een rekening van $10.000 over zou zijn, en alles samen.
- Bedragen zijn **hypothetisch** en worden in beeld en tekst zo gelabeld ("HYPOTHETICAL ACCOUNT"). Het is geen rendementsbelofte en geen ranglijst om te volgen.

## 2. Vaste keuzes (26 nov 2026)

| Punt | Keuze |
|---|---|
| Inleg | $10.000 per strategie, elke strategie een eigen rekening |
| Inzet bij tests met een stop (resultaat in R) | Vast $100 risico per trade (1% van de start), niet herbeleggen. Eindbedrag = $10.000 + $100 × som van de netto R |
| Inzet bij tests zonder stop (resultaat in % of punten) | Positie van $10.000 per trade, niet herbeleggen. Winst = $10.000 × netto rendement van de trade |
| Periode | Per test de oorspronkelijke beslissende periode, zoals gepubliceerd (26 nov; eerder voorstel 2020-2026 vervallen) |
| Kosten | Zoals in de gepubliceerde beslissende uitkomst van elke test |

## 3. Bestanden en eenheden per test (vastgelegd vóór de berekening)

Audit (keuze A, de redactie): G, H, K, N en O met de gecorrigeerde trades uit `results/audit-opening-2026-11-21/new/`.
Reproductiecontrole: het script rekent eerst per test het aantal trades en het gemiddelde in de eigen eenheid na en zet dat naast het gepubliceerde getal. Wijkt dat af, dan stopt het script voor die test en zoeken we de oorzaak vóór er dollars worden getoond.

| Test | Bestand (in `results/`) | Selectie | Eenheid → dollars |
|---|---|---|---|
| A · MACD + 200 EMA | macd-200ema/macd_trades.csv | EURUSD + EURJPY, kolom NET_1.2 | R × $100 |
| B · Stochastic + RSI + MACD | stoch-rsi-macd/srm_trades.csv | alleen EURUSD (beslissend), NET_1.2 | R × $100 |
| C · MACD + ATR | macd-atr/macdatr_trades.csv | periode T, signaal "MACD Line ZC" (21 paren) | R × $100 |
| D · Bollinger + 200 EMA | bollinger-200ema/bb200_trades_eurusd.csv | NET_1.2 | R × $100 |
| E · RSI(2)-pullback | rsi2-pullback/trades_P1_sp500.csv | alle | $10.000 × net_return |
| F · MA 9/21 goud | ma-9-21-gold/trades_P1_decisive.csv | R_NET | R × $100 |
| G · Box Theory | audit new/G_P1/trades.csv | net_r | R × $100 |
| H · 5-min ORB | audit new/H_P1/trades.csv | net_r | R × $100 |
| I · Triple RSI | triple-rsi/trades_P1.csv | alle | $10.000 × net_return |
| K · UT Bot | audit new/K/trades_P1.csv | net_R | R × $100 |
| L · Gespreide instap (BTC) | structured-entry/trades_G_P1.csv | result_pct (geen hefboom) | $10.000 × result_pct |
| M · Supertrend + 200 EMA | supertrend-200ema/trades_m30.csv | NET_1.2 | R × $100 |
| N · 9 EMA + VWAP | audit new/N_us500/trades_US500.csv | net / entry | $10.000 × rendement |
| O · 9 EMA + VWAP prop firm | audit new/O_rth/trades_USTEC_rth_firm_a.csv | net / entry | $10.000 × rendement |
| P · S/R-breakout goud | sr-breakout/trades_P1_decisive.csv | R_NET | R × $100 |
| Q · Morning star goud | morning-star-gold/trades_P1_decisive.csv | R_NET | R × $100 |
| R · Noise-area momentum | noise-area-momentum/trades_ustec.csv | netto punten / entry (kosten zoals run 01) | $10.000 × rendement |
| S · Vorige-dag-sweep | prev-day-sweep/trades_ustec_p1.csv | R | R × $100 |
| LCE · supply-demand | supply-demand-levels/trades.csv | netto_R | R × $100 |
| Bollinger reversion (NT02) | bollinger-reversion/bb_multi_trades.csv | real_R (1,5 pip kosten) | R × $100 |
| Volume breakout | volume-breakout/trades.csv | r (na 10 bp) | R × $100 |
| Buy the Dip | buy-the-dip/trades.csv | instap vanaf 1 jan 2024, beide indices (67 trades, met de jaarwisseling-noot) | $10.000 × net_return_2bp |

Niet mee: G2 (geen tradelijst), Donchian en Aziatische range (geen tradelijst in deze vorm), test J (niet gepubliceerd). Tests onder 100 trades krijgen het label "too few trades" (E-varianten boven 100 wel mee, I met 89, LCE met 73 en Buy the Dip met 67 krijgen het label).

## 4. Keuze audit

Besloten: A, gecorrigeerde trades (26 nov 2026).

## 5. Controlegroep

Geen nieuwe controle. Naast elk bedrag staat het gepubliceerde percentiel tegen toeval, met de periode waarop dat percentiel slaat. Een bedrag boven $10.000 zegt op zich niet dat de regel beter is dan toeval; dat zeggen alleen de percentielen.

## 6. Wat we laten zien

Per strategie: trades in het venster, eindbedrag, laagste stand van de rekening, langste periode onder $10.000, gepubliceerd percentiel. Samen: $10.000 × aantal strategieën ingelegd, en wat er in totaal over is. Tests onder 100 trades in het venster krijgen het label "too few trades".

## 7. Regels

- Na de eerste berekening verandert dit plan niet. Een andere aanpak wordt een nieuwe versie met nieuwe datum.
- Elk bedrag in tekst en beeld wordt gecontroleerd tegen de uitvoer van het script.
- Geen namen van makers, kanalen of producten.
- Het script, deze plantekst en de uitvoer gaan naar strategy-validation vóór de video.
