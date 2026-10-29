# V5 — Kaggle CV and Public Catalog Acquisition

This is an incremental enhancement to the **existing V4 source code**, not a trained-model deliverable. The source ZIP cannot include the Kaggle images, trained weights or external catalog snapshot. No model training/download or live storefront crawl was completed in the build environment (outbound HTTP was unavailable).

## Run on Windows (from V5 project root)

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install kaggle
# Configure Kaggle credentials via official Kaggle account settings; don't commit credentials
.\.venv\Scripts\python.exe scripts\setup_cv_datasets.py --dataset fashion
.\.venv\Scripts\python.exe scripts\prepare_fashion_cv.py
# Select CPU or NVIDIA CUDA compatible PyTorch wheels from https://pytorch.org/get-started/locally/
.\.venv\Scripts\python.exe -m pip install torch torchvision
.\.venv\Scripts\python.exe scripts\train_fashion_cv.py --epochs 3 --batch-size 16 --pretrained
```

`--pretrained` downloads ImageNet pretrained MobileNetV3 weights from the official torchvision provider. For true transfer learning, always pass `--pretrained`. If no internet is available for model weights, omission trains only the new head on random frozen features (not recommended). Run `nvidia-smi` to assess GPU; use `--device cpu` if necessary. The training script retains a **best-validation checkpoint** and evaluates once on separate held-out test images. The script's results are not claims about Cottonil SKUs.

For a validated fitted model, start backend and POST image to `/api/cv/fashion-predict` or inspect `/api/cv/status`. Untouched V4 RGB/HSV heuristic remains at `/api/cv/color-analysis`. This does NOT add fabric defect detection, visual similarity search, or calibrated color model.

## Cottonil public catalog (optional)

Public product listing inspected: https://cottonilegypt.com/collections/all. It displays public product titles, colors, and retail prices. The website's host must independently authorize automated fetching under its terms and `robots.txt`; this build **did not verify robots policy** due to lack of outbound connectivity. The included script is designed to stop when the robots check cannot be verified; it does not circumvent access restrictions.

```powershell
.\.venv\Scripts\python.exe scripts\cottonil_public_catalog.py --max-pages 2 --delay 2
```

If collection is blocked, **stop and seek an authorized feed/export from the site owner**. Never interpret public storefront pricing as verified internal sales or cost. Never attach public images to internal Cottonil SKU IDs without a documented explicit SKU mapping and content rights.

All external data goes under `data/cv/` and `data/external/cottonil/`; original 25 CSV files in `data/raw/` remain untouched. Do not put credential files, external assets, or trained models into a public repository without permission.

## Current state

Implemented and statically checked: Kaggle official CLI setup, deterministic stratified image split manifest (by product subcategory), MobileNetV3 classifier training/evaluation script, optional trained-model inference API, bounded robots-aware public JSON catalog metadata collector. **Not run against downloaded data**, due to this environment's network constraints. No claims of achieved model accuracy or successful scraping. Splitting by image ID limits duplicate-ID leakage but does not guarantee near-duplicate visual leakage. Audit duplicate/variant groups before production claims.
