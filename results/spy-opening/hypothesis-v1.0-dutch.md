# Hypothese: SPY kopen op de opening (test G2, bijclaim bij test G)

Datum: 13 november 2026 · Aanleiding: bijclaim in bron 3 van test G (`Test\box-theory\claim-bron.md`) · Status: **versie 1.0, 13 november 2026. Databron A gekozen (13 nov). Goedgekeurd op 13 nov 2026 ("akkoord G2"). Geen koersdata geopend.**

Legenda: **[geverifieerd]** = zelf gecontroleerd of berekend · **[aanname]** = niet zelf gecontroleerd, of een keuze in de meting

Spelregel: alles hieronder ligt vast vóór de eerste run. Na de eerste echte run verandert er niets; een nieuwe versie krijgt een nieuwe datum.

## 1. De claim

[geverifieerd, transcript gelezen op 11 nov 2026, vastgelegd in `claim-bron.md`, tijdcode 23:20-23:54] Een tradingvideo van 19 september 2026 zegt: "over the last 15 years, if you just bought the SPY" op de opening en verkocht, dan stond je na een uur in 51% van de gevallen op winst, na twee uur in 53%, en aan het eind van de dag in 54%.

[geverifieerd, 13 nov 2026] De video en het hele kanaal zijn niet meer te bekijken: YouTube meldt dat het account is beëindigd. Het citaat hierboven is dus niet meer na te lezen bij de bron. Alleen de vier woorden tussen aanhalingstekens zijn letterlijk genoteerd; de rest is onze samenvatting van 11 nov.

## 2. Toetsbare claims

| # | Claim | Toetsbaar als |
|---|---|---|
| C1 | Na 1 uur staat SPY in 51% van de dagen hoger dan de opening | Aandeel dagen hoger, met 95%-interval |
| C2 | Na 2 uur: 53% | Idem |
| C3 | Bij het slot: 54% | Idem |
| C4 | De opening is een goed moment om te kopen (impliciet: "if you just bought the SPY") | Gemiddeld netto rendement van het venster, tegen hetzelfde venster vanaf een willekeurig tijdstip op dezelfde dag (Null A) |
| C5 | Kopen op de opening wint vaker dan het verliest | Ondergrens van het 95%-interval boven 50% (muntworp) |

C4 en C5 staan niet letterlijk in de video. Ze zijn onze vertaling van wat de claim suggereert [aanname]. In de publicatie staan ze apart van C1 tot C3.

## 3. Zwakke plekken, vooraf benoemd

1. [geverifieerd] De bron is offline; de exacte formulering en de rekenwijze van de maker zijn niet meer te controleren.
2. [aanname] "Op winst" kan betekenen: koers hoger dan de opening (zonder kosten), of hoger na kosten. Wij meten het eerste als de claim, het tweede als aanvulling.
3. [aanname] Een stijgende markt geeft vanzelf iets meer dan de helft stijgende dagen. Een getal boven 50% zegt dus weinig over de opening zelf; daarom C4.
4. [aanname] "15 jaar" vanaf de video: 19 sep 2011 tot en met 18 sep 2026. De maker kan een iets andere periode hebben gebruikt.
5. Afhankelijk van de databron (paragraaf 5): bij optie A worden C1, C2 en C4 gemeten op een CFD op de S&P 500, niet op SPY, en pas vanaf 2017.

## 4. Mechanische vertaling (vast)

**4.1 Opening.** De eerste minuut van de beurssessie, 9:30 New Yorkse tijd. Bij minuutdata uit MT5 (servertijd): bepaald zoals in test G, uit de grootste sprong in tickvolume rond 16:30 servertijd, met een speling van 60 minuten eerder of later voor weken met verschil in zomertijd. Een dag telt alleen mee als de sessie minstens 90% van de 390 minuutbars heeft. Openingskoers = de open van die eerste minuutbar.

**4.2 Meetmomenten.** Koers na 1 uur = slot van de 60e minuutbar van de sessie (10:30). Na 2 uur = slot van de 120e (11:30). Slot = slot van de laatste sessiebar (16:00), of bij dagdata de officiële slotkoers. Op dagen met een verkorte sessie (13:00) telt het slot van die dag; 1 en 2 uur blijven gelijk.

**4.3 Hoger.** Koers op het meetmoment strikt hoger dan de openingskoers. Gelijk telt als niet hoger; het aandeel gelijke dagen wordt apart gemeld.

**4.4 Rendement.** (koers op meetmoment / openingskoers) min 1. Netto: min de kosten uit 6.

## 5. Data (vast: optie A, gekozen op 13 nov 2026)

| | A. Yahoo SPY dag + MT5 US500 M1 | B. Betaalde SPY-minuutdata | C. Alleen het slot |
|---|---|---|---|
| C3 (slot) | SPY-dagdata Yahoo, 19 sep 2011 tot 18 sep 2026, exact de claimperiode | SPY, 15 jaar | SPY-dagdata Yahoo, 15 jaar |
| C1, C2, C4 | US500 M1 (IC Markets, al op de laptop), echte minuutdata vanaf 21 mrt 2017. CFD, geen SPY | SPY, 15 jaar | Niet getoetst, gemeld als niet toetsbaar |
| Kosten | Gratis, data deels al aanwezig | Aankoop, bron en prijs nog uitzoeken | Gratis |
| Voorstel Claude | **Ja**: snel, met de beperking in elke publicatie | Alleen als de meting op de CFD twijfel laat | |

Bij optie A ook een controle op de CFD als vervanger: op de dagen die beide reeksen hebben (2017 tot 2026), het aandeel hoger bij het slot op US500 naast dat op SPY. Wijken die meer dan 2 procentpunt af, dan wordt dat gemeld bij C1 en C2 [aanname: grens gekozen vóór de data].

Datacontrole vóór de run, alleen op koersen en metadata, niet op uitkomsten:
- SPY: aantal handelsdagen per jaar (verwacht ongeveer 252), dagen met open gelijk aan het vorige slot, open buiten de dagrange. Ligt meer dan 2% van de dagen op open = vorig slot, dan melden.
- US500: aandeel dagen waarop de opening gevonden is, aandeel geldige sessies, verdeling van de gevonden openingsminuut (16:30, 15:30, 17:30 servertijd).

## 6. De drie vaste regels

**Kosten.** SPY: 2 basispunten per round trip [aanname: spread van ongeveer 1 cent plus wat slippage]. US500: de spread uit de SPREAD-kolom op de openingsbar, plus 1 basispunt slippage [aanname]. Gevoeligheid 0, 2 en 4 bp. C1 tot C3 worden gemeten zonder kosten, zoals de claim; het aandeel na kosten staat ernaast.

**Volgorde.** Geen stop en geen target: de positie loopt van de opening tot het meetmoment. Per dag ook de diepste tussentijdse daling in dat venster (alleen bij minuutdata), ter informatie.

**Controlegroep.**
- C4, Null A (beslissend): voor elk venster (1 uur, 2 uur) op dezelfde dagen een willekeurige startminuut binnen de sessie, met hetzelfde venster en dezelfde kosten, zodat het venster binnen de sessie valt (start tussen 9:30 en 15:00 voor 1 uur, tussen 9:30 en 14:00 voor 2 uur). De opening zelf mag ook getrokken worden. 10.000 runs, seed 29. Gemeten: gemiddeld netto rendement per dag. Percentiel van de echte waarde in de verdeling.
- C5: muntworp, 50%.
- Voor het slot bestaat geen zinnige Null A binnen de dag (het venster begint altijd op de opening). Het slot wordt daarom alleen tegen 50% gezet (C5), en de claimwaarde tegen de meting (C3).

## 7. Ruiscontrole vóór de echte data (vast)

24 synthetische reeksen van 2.300 dagen met 390 minuutbars, zonder trend en zonder openingseffect, beweeglijkheid per minuut zo gekozen dat de dagbeweging rond 1,1% ligt [aanname]. Seed 7.

Grens, gelijk aan de audit van 10 nov: percentiel van C4 tegen Null A gemiddeld tussen 35 en 65, hooguit 3 van 24 boven 95. Aandeel hoger bij 1 uur, 2 uur en slot gemiddeld tussen 49 en 51%.

Extra controle op gevoeligheid (gemeld, niet beslissend): dezelfde 24 reeksen met een kunstmatige stijging van 0,05% in het eerste uur. Verwacht: percentiel boven 95 in de meeste sets. Haalt de controle dat in minder dan 20 van 24, dan staat in de publicatie dat de test kleine openingseffecten kan missen.

## 8. Periodes (vast)

| Run | Periode | Rol |
|---|---|---|
| P1 | 19 sep 2011 tot en met 18 sep 2026 (claimperiode), bij minuutdata vanaf de eerste volledige dag na 21 mrt 2017 | **Beslissend** |
| P2 | per jaar binnen P1 | Verdeling, niet beslissend |
| P3 | 19 sep 2026 tot de laatste dag | Na de claim. Minder dan 100 dagen: gemeld als onvoldoende |

## 9. Wanneer is de claim gefalsifieerd (vooraf)

| Claim | Gefalsifieerd als |
|---|---|
| C1, C2, C3 | De claimwaarde (51, 53, 54%) ligt buiten het 95%-interval (Wilson) van het gemeten aandeel. De richting wordt gemeld: een hoger gemeten aandeel spreekt de claim ook tegen, maar de boodschap anders |
| C4 | Het gemiddelde netto rendement van het venster ligt niet boven percentiel 95 van Null A |
| C5 | De ondergrens van het 95%-interval ligt op of onder 50% |

Na de run: geen andere tijdstippen, vensters of kostenniveaus proberen. Blijft een claim staan, dan rapporteren als "niet gefalsifieerd in deze meting", niet als "werkt".

## 10. Wat ik rapporteer, ongeacht de uitkomst

Per meetmoment: aantal dagen, aandeel hoger (95%-interval), aandeel gelijk, gemiddeld rendement bruto en netto, percentiel tegen Null A (1 en 2 uur). De jaartabel. Bij optie A de vergelijking US500 tegen SPY bij het slot. De ruiscontrole en de gevoeligheidscontrole. De kanttekening dat de bron offline is.

## 11. Volgende stap

1. Keuze van de databron (A, B of C) en goedkeuring van de hypothese. SHA-256 in het meetlog.
2. Script `spy_open_control.py`, eerst de ruiscontrole uit 7.
3. SPY-dagdata ophalen via het browserpaneel (Yahoo chart-API, zoals bij test E), datacontrole uit 5, dan de run.
4. Code en data op GitHub vóór publicatie.
