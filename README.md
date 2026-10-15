# Teste-pillow

Retoque de foto com Pillow + OpenCV + NumPy (sem IA generativa).

- `input/selfie_original.png` – foto original.
- `scripts/retocar_selfie.py` – remove as alças da mochila e arruma a gola da camiseta.
- `output/selfie_editada.png` / `.jpg` – resultado.

```bash
pip install pillow opencv-python-headless numpy
python3 scripts/retocar_selfie.py input/selfie_original.png output/selfie_editada.png
```
