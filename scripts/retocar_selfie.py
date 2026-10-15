"""Retoque da selfie: remove as alcas da mochila e arruma a gola da camiseta.

Uso:
    python3 scripts/retocar_selfie.py input/selfie_original.png output/selfie_editada.png

Pipeline (Pillow + OpenCV + NumPy, sem IA generativa):
  1. Mascara das duas alcas: poligonos desenhados a mao, restritos ao componente
     conexo escuro da camiseta (nunca encosta no fundo nem na pele).
  2. Preenchimento: sombreamento interpolado so a partir de pixels da camiseta
     (convolucao normalizada multi-escala) + grao do tecido clonado de uma area limpa
     do peito.
  3. Gola: o lado direito do decote, que estava puxado/amassado contra o pescoco,
     recebe uma curva suave; a faixa que abre vira pele clonada do pescoco e a faixa
     canelada da gola e redesenhada ao longo da nova curva.
"""
import sys

import cv2
import numpy as np
from PIL import Image


def polygon_mask(shape, pts):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 255)
    return m


def blur(img, sigma):
    return cv2.GaussianBlur(img, (0, 0), sigma)


def normalized_fill(img, valid, sigmas=(4, 8, 16, 32, 64, 128)):
    """Interpola cor usando apenas pixels validos (sem vazar cor do fundo)."""
    v = valid.astype(np.float32)
    out = np.zeros_like(img)
    done = np.zeros(img.shape[:2], bool)
    for s in sigmas:
        w = blur(v, s)
        f = blur(img * v[..., None], s) / (w[..., None] + 1e-6)
        take = (~done) & (w > 0.08)
        out[take] = f[take]
        done |= take
    out[~done] = f[~done]
    return out


def largest_component_containing(mask, seed_xy):
    n, lab = cv2.connectedComponents(mask)
    k = lab[seed_xy[1], seed_xy[0]]
    return (lab == k).astype(np.uint8) * 255


def main(src, dst):
    rgb = np.array(Image.open(src).convert("RGB"))
    H, W, _ = rgb.shape
    img = rgb.astype(np.float32)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]

    skin = ((r > 120) & (r > g + 15) & (g > b) & (hsv[..., 2] > 110)).astype(np.uint8) * 255
    dark = ((hsv[..., 2] < 90) & (skin == 0)).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    shirt = largest_component_containing(dark, (350, 1300))
    shirt = cv2.morphologyEx(shirt, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    # ------------------------------------------------------------------ alcas
    strap_left = [(30, 1110), (70, 1090), (110, 1078), (150, 1068), (175, 1078), (200, 1098),
                  (225, 1135), (245, 1180), (258, 1230), (270, 1300), (282, 1380), (286, H), (0, H), (0, 1140)]
    strap_right = [(412, 1100), (445, 1092), (480, 1108), (515, 1140), (540, 1185), (552, 1240),
                   (550, 1320), (548, H), (462, H), (468, 1330), (462, 1250), (440, 1185), (412, 1140)]
    poly = cv2.bitwise_or(polygon_mask(rgb.shape, strap_left), polygon_mask(rgb.shape, strap_right))
    shirt_core = cv2.erode(shirt, np.ones((3, 3), np.uint8))           # longe da silhueta/fundo
    skin_wide = cv2.dilate(skin, np.ones((15, 15), np.uint8))          # longe da gola
    mask = cv2.bitwise_and(poly, shirt_core)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(skin_wide))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    mask = cv2.bitwise_and(mask, cv2.erode(shirt, np.ones((3, 3), np.uint8)))

    # baixa frequencia: so a partir de pixels da camiseta fora da mascara e longe da
    # borda (a franja da silhueta carrega cor do fundo). A crominancia e fixada na
    # cor media do peito para o remendo nao puxar para o roxo do chao.
    valid = (cv2.erode(shirt, np.ones((11, 11), np.uint8)) > 0) & (cv2.dilate(mask, np.ones((7, 7), np.uint8)) == 0)
    low = normalized_fill(blur(img, 3), valid)
    low = blur(low, 5)
    chest = img[1250:1440, 290:430].reshape(-1, 3).mean(0)
    low = low.mean(axis=2, keepdims=True) * (chest / chest.mean())

    # alta frequencia: grao do tecido clonado de area limpa do peito, com amplitude
    # proporcional ao brilho local
    tex_src = img[1250:1440, 290:430]
    tex = tex_src - blur(tex_src, 3)
    src_lum = tex_src.mean()
    th, tw = tex.shape[:2]
    # ladrilhos sobrepostos com borda suave (sem emendas nem simetria espelhada)
    rng = np.random.default_rng(7)
    T, OV = 96, 32
    ramp = np.minimum(np.arange(T) + 1, T - np.arange(T)).astype(np.float32)
    ramp = np.clip(ramp / OV, 0, 1)
    feather = (ramp[:, None] * ramp[None, :])[..., None]
    canvas = np.zeros_like(img)
    weight = np.zeros((H, W, 1), np.float32)
    for y0 in range(-OV, H, T - OV):
        for x0 in range(-OV, W, T - OV):
            sy, sx = rng.integers(0, th - T), rng.integers(0, tw - T)
            patch = tex[sy:sy + T, sx:sx + T]
            if rng.random() < 0.5:
                patch = patch[::-1]
            if rng.random() < 0.5:
                patch = patch[:, ::-1]
            ya, xa = max(y0, 0), max(x0, 0)
            yb, xb = min(y0 + T, H), min(x0 + T, W)
            py, px = ya - y0, xa - x0
            canvas[ya:yb, xa:xb] += patch[py:py + (yb - ya), px:px + (xb - xa)] * feather[py:py + (yb - ya), px:px + (xb - xa)]
            weight[ya:yb, xa:xb] += feather[py:py + (yb - ya), px:px + (xb - xa)]
    canvas /= np.maximum(weight, 1e-3)
    lum_gain = np.clip(low.mean(axis=2, keepdims=True) / src_lum, 0.8, 2.5)
    synth = low + canvas * lum_gain

    alpha = blur(mask.astype(np.float32) / 255.0, 3.5)[..., None]
    out = img * (1 - alpha) + synth * alpha

    # ------------------------------------------------------------------- gola
    neck = {}
    for x in range(130, 500):
        ys = np.where(skin[1000:1260, x] > 0)[0]
        if len(ys):
            neck[x] = int(ys.max()) + 1000

    # Nova curva do lado direito do decote: do fundo da gola (x=381) subindo em arco
    # ate encostar no contorno do pescoco perto de y=1096.
    y_start = float(neck[381])
    ctrl = [(381, y_start), (393, 1193), (404, 1178), (412, 1160), (417, 1142),
            (420, 1124), (421, 1108), (420, 1096)]
    cx = np.array([p[0] for p in ctrl], np.float32)
    cy = np.array([p[1] for p in ctrl], np.float32)
    ys_r = np.arange(int(y_start), 1095, -1).astype(np.float32)
    xs_r = np.interp(ys_r, cy[::-1], cx[::-1])
    xs_r = cv2.GaussianBlur(xs_r.reshape(1, -1), (0, 0), 3).ravel()

    # continua a curva para a esquerda com o decote original (para a faixa emendar)
    xs_l = np.arange(330, 381).astype(np.float32)
    ys_l = np.array([neck[int(x)] for x in xs_l], np.float32)
    curve = np.concatenate([np.stack([xs_l, ys_l], 1), np.stack([xs_r, ys_r], 1)])

    # regiao de trabalho (so lado direito da gola)
    region = np.zeros((H, W), np.uint8)
    cv2.rectangle(region, (350, 1096), (470, 1215), 255, -1)

    # "pele" = area a esquerda/acima da curva, fechada pelo contorno do pescoco
    poly_skin = np.concatenate([curve, [[xs_r[-1], 1040], [330, 1040]]]).astype(np.int32)
    inside = np.zeros((H, W), np.uint8)
    cv2.fillPoly(inside, [poly_skin], 255)
    dist_in = cv2.distanceTransform(inside, cv2.DIST_L2, 5)
    dist_out = cv2.distanceTransform(255 - inside, cv2.DIST_L2, 5)
    sd = np.where(inside > 0, -dist_in, dist_out)  # <0 pele, >0 camiseta

    # pele nova onde o decote abriu: substitui uma faixa de 14px junto a nova curva
    # (so no lado direito) pelo pescoco deslocado 26px para a esquerda, e escurece
    # progressivamente ate a borda para imitar o sombreamento natural do contorno.
    skin_band = (inside > 0) & (sd > -14) & (region > 0)
    skin_band[:, :384] = False
    shifted = np.roll(out, 26, axis=1)
    shade = 1.0 - 0.22 * np.exp(np.minimum(sd, 0) / 5.0)
    shifted = shifted * shade[..., None]
    a_skin = blur(skin_band.astype(np.float32), 2.0)[..., None] * (inside[..., None] > 0)
    out = out * (1 - a_skin) + shifted * a_skin
    need_skin = skin_band & (skin == 0)

    # cor base da camiseta ao redor (sem usar pele nem fundo)
    shirt_near = (sd > 6) & (shirt > 0)
    base = normalized_fill(blur(out, 2), shirt_near, sigmas=(6, 12, 24, 48))

    # perfil da faixa canelada medido na parte limpa de baixo da gola
    prof = np.zeros(20, np.float32)
    for x in range(290, 360):
        y0 = neck[x]
        prof += np.array([rgb[y0 + d, x].mean() for d in range(20)])
    prof /= 70
    plain = prof[15:].mean()
    delta = np.clip(prof - plain, -12, 12)
    delta[15:] = 0
    delta[0] = -12  # linha escura da costura junto a pele

    d_band = np.clip(sd, 0, 19.99)
    gain = np.interp(d_band.ravel(), np.arange(20), delta).reshape(H, W)
    band_img = base + gain[..., None] + canvas * 0.8
    was_shirt = cv2.dilate(shirt, np.ones((3, 3), np.uint8)) > 0
    band_alpha = ((sd > 0) & (sd < 15) & (region > 0) & (was_shirt | need_skin)).astype(np.float32)
    band_alpha = blur(band_alpha, 0.8)[..., None]
    out = out * (1 - band_alpha) + band_img * band_alpha

    # suaviza a transicao pele/camiseta na nova curva
    edge = np.exp(-(sd ** 2) / (2 * 1.1 ** 2)) * (region > 0) * (was_shirt | skin_band)
    out = out * (1 - edge[..., None]) + blur(out, 0.8) * edge[..., None]

    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
    dbg = rgb.copy()
    dbg[mask > 0] = (dbg[mask > 0] * 0.4 + np.array([255, 0, 0]) * 0.6).astype(np.uint8)
    dbg[need_skin] = (0, 255, 0)
    Image.fromarray(dbg).save(dst.rsplit(".", 1)[0] + "_mascaras.png")
    print("ok", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
