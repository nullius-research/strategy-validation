# Setupdefinitie

Vul dit in als code, niet als beschrijving. Als een computer het niet kan
uitrekenen, kan control.py het niet toetsen en bestaat de setup niet.

## Actieve regel: volume breakout, long only

    naam:       volume breakout
    universum:  alles in config/watchlist.md
    signaal:    close > max(high[-1 : -lookback])
                EN volume > vol_mult * gemiddelde(volume[-1 : -lookback])
    richting:   long
    entry:      open van de VOLGENDE bar
    stop:       entry - atr_mult * ATR14(tot en met de signaalbar)
    target:     2R
    max hold:   20 bars
    cooldown:   5 bars tussen twee signalen per ticker

    lookback:   20
    vol_mult:   1.5
    atr_mult:   2.0

Gegenereerd door validation/signals.py, niet door een agent. Geen enkel
taalmodel raakt historische data aan, want het model weet wat er na die datum
gebeurde en dat is lookahead die je niet kunt zien.

## Administratie, verplicht

    vrijheidsgraden:     4  (lookback, vol_mult, atr_mult, cooldown)
    plus uitvoering:     2  (target_r, max_hold)
    totaal:              6
    geteste varianten:   1  (volume breakout 20/1.5/2.0, verworpen)
    datum eerste test:   2026-08-13

Elke keer dat je een parameter aanpast na het zien van een resultaat, gaat
"geteste varianten" met een omhoog. Bij twintig varianten heb je twintig keer
gegokt en betekent een percentiel van 95 niets meer. Log het in
journal/varianten.md, ook de verworpen.
