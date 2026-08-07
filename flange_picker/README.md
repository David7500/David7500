# flange_picker

Detekcija tankih prirobnic v zaboju iz **ene same kamere**, brez kalibracije in
brez znane delovne razdalje. Vrne rangirane kandidate za prijem z magnetnim
seskom v koordinatnem sistemu zaboja.

## Uporaba

```bash
python cli.py slika.png                 # JSON na stdout
python cli.py slika.png --debug         # + overlay slike za vsak korak v debug/
python cli.py slika.png --out poza.json --top 5

python -m flange_picker.synth out_dir -n 20     # generiraj sintetične scene
python -m flange_picker.evaluate -n 12          # izmeri RMSE na sintetičnem setu
```

Vse konstante in pragovi so v `config.yaml`; v kodi ni nobene hardcodirane
vrednosti. Za drug kos zamenjaj `flange.d_out_mm`, `flange.d_in_mm` in
`box.w_mm` / `box.h_mm`.

## Izhod

```json
{"frame": "box",
 "frame_reliable": true,
 "calibration": {"f_px": 1524.0, "confidence": 0.59, "method": "box_vanishing_points",
                 "frame_confidence": 1.0, "f_confidence": 0.19},
 "candidates": [
   {"x_mm": 334.6, "y_mm": 110.1, "z_mm": 1.2,
    "tilt_deg": 3.7, "azimuth_deg": 214.0, "normal": [0.06, -0.04, 0.998],
    "grasp_point_mm": [348.5, 110.4, 1.2],
    "occlusion_ratio": 1.0, "score": 0.89, "confidence": 0.82,
    "free_arc_deg": 360.0, "cup_fit_ratio": 0.8, "wall_margin_mm": 65.4,
    "paired": true, "ellipse_px": {...}, "notes": []}
 ],
 "warnings": [...], "rejected": [...], "diagnostics": {...}}
```

Prvi kandidat je najprimernejši za prijem. `grasp_point_mm` je točka za sesek —
leži na kolobarju med `D_in` in `D_out`, **ne** v geometrijskem središču, kjer
je luknja. `tilt_deg` / `azimuth_deg` povesta, kako naj robot nagne prijemalo.

Koordinatni sistem: izhodišče v vogalu dna zaboja, X vzdolž `box.w_mm`,
Y vzdolž `box.h_mm`, Z navzgor od dna.

## Zaupanje: dva ločena pojma

- `frame_confidence` — ali imamo koordinatni sistem zaboja. Od tega so odvisni
  X, Y, naklon in azimut.
- `f_confidence` — ali imamo absolutno merilo globine. Od tega je odvisna le
  višina Z nad dnom.

Ločena sta zato, ker napačna goriščna razdalja skoraj natanko skalira globino,
lateralnih koordinat pa ne pokvari (glej `ROADMAP.md`, ugotovitev K2).

**Pri strogo navpični kameri `f_px` iz scene ni določljiv** — to je fizikalna
lastnost, ne pomanjkljivost kode. Za absolutno višino podaj
`camera.working_distance_mm` (dovolj je ±5 %) ali nagni kamero za nekaj stopinj.

## Degradacija

Sistem nikoli ne odpove tiho:

| Stanje | Posledica |
|---|---|
| zaboj najden, `f` iz scene | polne koordinate |
| zaboj najden, `f` neznan | polne X, Y, naklon; Z skalirana z neznanim faktorjem, opozorilo |
| zaboj ni najden ali merilo ni skladno | `frame: "camera"`, samo relativno rangiranje, opozorilo |
| prazna/neberljiva slika | prazna lista kandidatov, opozorilo |

Vsak zavrnjen kandidat je naveden v `rejected` z razlogom.

## Moduli

| Datoteka | Vloga |
|---|---|
| `autocalib.py` | zaboj → homografija → `f_px` → koordinatni sistem |
| `preprocess.py` | CLAHE, bilateralni filter, maska odsevov |
| `edges.py` | Canny + subpikselska izostritev po gradientu |
| `ellipse.py` | direktni LSQ fit, polariteta roba, parjenje |
| `pose.py` | krog → poza, razreševanje dvoumnosti |
| `scoring.py` | rangiranje, prijemna točka |
| `pipeline.py` | orkestracija, JSON izhod, debug overlay-i |
| `synth.py` | generator sintetičnih scen z ground truth |
| `evaluate.py` | metrike na sintetičnem setu |

## Testi

```bash
python -m pytest flange_picker/tests -q
```

## Kaj namerno ni implementirano

- Popačenje leče (pri kakovostni optiki ~1 % napake).
- Korekcija za debelino kosa pri velikem naklonu.
- Stereo / ToF / globinske metode — pri debelini 1–2 mm je šum večji od signala.

Trenutne metrike in prednostni seznam so v `ROADMAP.md`.
