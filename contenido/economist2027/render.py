"""Renderiza el video vertical (1080x1920) sobre la portada de The Economist 2027.

Uso: python3 render.py <portada.png> <salida.mp4> <carpeta_temporal> <voz>
<voz> = modelo Piper sin extensión, o carpeta con audios ya generados <escena*10+frase>.wav
(la versión publicada usa la voz "Juan" de Higgsfield, modelo seed_audio).
Requiere: ffmpeg, piper-tts (voz es_MX-ald-medium), Pillow, numpy.

Estilo dinámico: cámara en mano, zoom en cada frase, paneo por la portada,
transiciones con destello y glitch, fondo animado desenfocado, títulos que se
escriben solos y subtítulos palabra por palabra. Cada escena se renderiza en
paralelo y al final se unen con el audio.
"""
import math
import os
import random
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from escenas import ESCENAS, PRONUNCIA  # noqa: E402

COVER, OUT, TMP, VOICE = sys.argv[1:5]
os.makedirs(TMP, exist_ok=True)

W, H, FPS, SR = 1080, 1920, 30, 22050
RED = (227, 18, 11)
BG = (10, 10, 10)
PANEL = 960
PX, PY = 60, 430      # posición del panel
UP = 4                # pre-escalado de la portada
PAD = 220             # margen alrededor de la portada (para zooms amplios)
BPM = 56              # latido (igual que la música)

F = "/usr/share/fonts/truetype/"
f_title = ImageFont.truetype(F + "liberation/LiberationSerif-Bold.ttf", 80)
f_tag = ImageFont.truetype(F + "dejavu/DejaVuSans-Bold.ttf", 30)
f_sub = ImageFont.truetype(F + "dejavu/DejaVuSans-Bold.ttf", 48)
f_ref = ImageFont.truetype(F + "dejavu/DejaVuSans.ttf", 25)
f_small = ImageFont.truetype(F + "dejavu/DejaVuSansMono.ttf", 24)
f_brand = ImageFont.truetype(F + "liberation/LiberationSerif-Bold.ttf", 34)


# ====================== VOZ ======================
def say_text(s):
    for k, v in PRONUNCIA.items():
        s = s.replace(k, v)
    return s


def tts(text, path, key=None):
    out = path.replace(".wav", "_n.wav")
    if os.path.isdir(VOICE):  # voces ya generadas (p. ej. Higgsfield): <VOICE>/<key>.wav
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(VOICE, f"{key}.wav"),
                            "-ac", "1", "-af", "silenceremove=start_periods=1:start_threshold=-45dB,"
                            "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                            "highpass=f=60", "-ar", str(SR), out], check=True)
    if os.path.exists(out):  # la voz varía en cada síntesis: reutilizar la ya generada
        with wave.open(out) as w:
            return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    # voz neuronal Piper, sin cambiar el tono para no deformarla
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE + ".onnx",
                    "-c", VOICE + ".onnx.json", "--length-scale", "1.06",
                    "--sentence-silence", "0.25", "-f", path],
                   input=say_text(text).encode(), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fx = "highpass=f=70,equalizer=f=180:t=q:w=1.2:g=2.5,aecho=0.9:0.9:45:0.10,volume=0.9"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1",
                    "-af", fx, "-ar", str(SR), out], check=True)
    with wave.open(out) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return a.astype(np.float32) / 32768.0


# ====================== TEXTO ======================
def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


_meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))


def layout_words(text, y_top, box_h):
    """Posición de cada palabra del subtítulo, centrado."""
    lines = wrap(_meas, text, f_sub, W - 110)
    lh = 64
    y = y_top + (box_h - lh * len(lines)) // 2
    out = []
    sp = _meas.textlength(" ", font=f_sub)
    for ln in lines:
        ws = ln.split()
        tw = _meas.textlength(ln, font=f_sub)
        x = (W - tw) / 2
        for wd in ws:
            out.append((x, y, wd))
            x += _meas.textlength(wd, font=f_sub) + sp
        y += lh
    return out


# ====================== CURVAS ======================
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.4):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    return 1 - (1 - clamp(t)) ** 3


def scene_audio(path, lines):
    """Carga el audio de una escena y estima dónde empieza y termina cada frase,
    eligiendo las pausas de la voz más cercanas al reparto proporcional por letras."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-af", "highpass=f=50", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    hop = int(0.02 * SR)
    rms = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, mode="same"))[::hop]
    thr = max(rms.max() * 0.06, 1e-4)
    voiced = np.where(rms > thr)[0]
    i0, i1 = max(0, voiced[0] - 3), min(len(rms), voiced[-1] + 6)
    a = a[i0 * hop:i1 * hop]
    rms = rms[i0:i1]
    total = len(a) / SR
    # pausas (>= 0.14 s por debajo del umbral)
    gaps, k = [], 0
    while k < len(rms):
        if rms[k] <= thr:
            j = k
            while j < len(rms) and rms[j] <= thr:
                j += 1
            if (j - k) * 0.02 >= 0.14 and k > 0 and j < len(rms):
                gaps.append((k * 0.02, j * 0.02))
            k = j
        else:
            k += 1
    lens = [len(x) for x in lines]
    cum = np.cumsum(lens)[:-1] / sum(lens) * total
    bounds, last = [], 0.0
    for target in cum:
        cands = [g for g in gaps if g[0] > last + 0.3]
        if cands:
            g = min(cands, key=lambda g: abs((g[0] + g[1]) / 2 - target))
            if abs((g[0] + g[1]) / 2 - target) > 2.5:
                g = (target, target)
        else:
            g = (target, target)
        bounds.append(g)
        last = g[1]
    spans, start = [], 0.0
    for g in bounds:
        spans.append((start, g[0]))
        start = g[1]
    spans.append((start, total))
    return a, spans


# ====================== AUDIO Y LÍNEA DE TIEMPO ======================
GAP, HEAD, TAIL = 0.3, 0.55, 0.5


def build_audio():
    timeline, voice_parts = [], []
    for i, sc in enumerate(ESCENAS):
        t = HEAD
        chunks = []
        seg = [np.zeros(int(HEAD * SR), np.float32)]
        scene_file = os.path.join(VOICE, f"s{i:02d}.mp3") if os.path.isdir(VOICE) else ""
        if scene_file and os.path.exists(scene_file):
            # un audio por escena (ElevenLabs): las frases se ubican en las pausas de la voz
            a, spans = scene_audio(scene_file, sc["lines"])
            for (s0, s1), line in zip(spans, sc["lines"]):
                chunks.append((t + s0, t + s1, t + s1, line))
            seg += [a]
            t += len(a) / SR
            if chunks:
                chunks[-1] = (*chunks[-1][:2], t + TAIL * 0.8, chunks[-1][3])
            seg.append(np.zeros(int(TAIL * SR), np.float32))
            dur = round((t + TAIL) * FPS) / FPS
            part = np.concatenate(seg)
            n = int(round(dur * SR))
            voice_parts.append(np.pad(part, (0, max(0, n - len(part))))[:n])
            timeline.append((chunks, dur))
            print(f"voz {i:02d} {sc['tag']}: {dur:.1f}s", flush=True)
            continue
        for j, line in enumerate(sc["lines"]):
            a = tts(line, os.path.join(TMP, f"v{i:02d}_{j}.wav"), i * 10 + j)
            d = len(a) / SR
            chunks.append((t, t + d, t + d + GAP, line))
            seg += [a, np.zeros(int(GAP * SR), np.float32)]
            t += d + GAP
        seg.append(np.zeros(int(TAIL * SR), np.float32))
        dur = round((t + TAIL) * FPS) / FPS          # duración exacta en cuadros
        part = np.concatenate(seg)
        n = int(round(dur * SR))
        part = np.pad(part, (0, max(0, n - len(part))))[:n]
        voice_parts.append(part)
        timeline.append((chunks, dur))
        print(f"voz {i:02d} {sc['tag']}: {dur:.1f}s", flush=True)
    voice = np.concatenate(voice_parts)
    total = len(voice) / SR

    tt = np.arange(len(voice)) / SR
    rng = np.random.default_rng(7)
    TWO_PI = 2 * np.pi

    def smooth_env(x, attack, decay):
        return np.where(x < 0, 0, np.minimum(1, x / attack) * np.exp(-np.clip(x - attack, 0, None) * decay))

    # pad oscuro en re menor con una segunda menor (tensión), todo >= 90 Hz
    drone = np.zeros_like(voice)
    for f0, g in ((146.83, 1.0), (174.61, 0.55), (220.0, 0.45), (155.56, 0.18)):
        for det in (-0.6, 0.6):
            drone += g * np.sin(TWO_PI * (f0 + det) * tt)
    drone *= 0.55 + 0.45 * np.sin(TWO_PI * tt / 12) ** 2
    drone /= np.max(np.abs(drone))
    # latido lento
    beat = np.zeros_like(voice)
    ph = tt % (60 / BPM)
    for off, amp in ((0.0, 1.0), (0.24, 0.6)):
        beat += amp * smooth_env(ph - off, 0.012, 14) * np.sin(TWO_PI * 95 * tt)
    # whoosh en cada cambio de escena y tic suave en cada frase
    hits = np.zeros_like(voice)
    kern = np.ones(40) / 40
    starts = np.cumsum([0] + [d for _, d in timeline[:-1]])
    for s in starts:
        i0 = int(max(0, s - 0.5) * SR)
        n = min(int(1.3 * SR), len(hits) - i0)
        x = np.arange(n) / SR
        noise = np.convolve(rng.standard_normal(n), kern, mode="same")
        env = np.sin(np.pi * np.clip(x / 1.3, 0, 1)) ** 2
        hits[i0:i0 + n] += noise * env / (np.max(np.abs(noise)) + 1e-9)
    ticks = np.zeros_like(voice)
    for s, (chunks, _) in zip(starts, timeline):
        for a, *_ in chunks[1:]:
            i0 = int((s + a - 0.05) * SR)
            n = min(int(0.25 * SR), len(ticks) - i0)
            x = np.arange(n) / SR
            ticks[i0:i0 + n] += smooth_env(x, 0.004, 30) * np.sin(TWO_PI * 1320 * x) * 0.5
    music = drone * 0.05 + beat * 0.07 + hits * 0.055 + ticks * 0.03
    fade = np.minimum(1, np.minimum(tt / 2, (total - tt) / 4))
    mix = voice / max(1e-6, np.max(np.abs(voice))) * 0.8 + music * fade
    mix = mix / max(1.0, np.max(np.abs(mix)) / 0.89)
    with wave.open(os.path.join(TMP, "mix.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return timeline, list(starts), total


# ====================== IMÁGENES BASE ======================
cov = Image.open(COVER).convert("RGB")
padded = Image.new("RGB", (cov.width + 2 * PAD, cov.height + 2 * PAD), (246, 246, 246))
padded.paste(cov, (PAD, PAD))
big = padded.resize((padded.width * UP, padded.height * UP), Image.LANCZOS)
big = big.filter(ImageFilter.UnsharpMask(radius=3, percent=90, threshold=2))
# fondo: portada desenfocada y oscurecida, teñida de rojo
bgsrc = padded.resize((padded.width * 2, padded.height * 2), Image.BILINEAR)
bgsrc = bgsrc.filter(ImageFilter.GaussianBlur(18))
bgsrc = Image.blend(bgsrc, Image.new("RGB", bgsrc.size, (40, 4, 4)), 0.55)
bgsrc = Image.eval(bgsrc, lambda v: int(v * 0.55))

# degradados para que el texto se lea sobre el fondo
shade = Image.new("L", (1, H))
for y in range(H):
    top = clamp(1 - y / 430) * 235
    bot = clamp((y - 1330) / 300) * 235
    shade.putpixel((0, y), int(max(top, bot, 70)))
shade = shade.resize((W, H))
SHADE = Image.merge("RGBA", (*[Image.new("L", (W, H), 6)] * 3, shade))


def cam_box(sc, chunks, dur, t, seed):
    """Caja (x, y, lado) en coordenadas de la portada para el tiempo t."""
    b0, b1 = sc["box"]
    e = ease(t / dur)
    x = b0[0] + (b1[0] - b0[0]) * e
    y = b0[1] + (b1[1] - b0[1]) * e
    s = b0[2] + (b1[2] - b0[2]) * e
    # en cada frase: golpe de zoom + leve reencuadre hacia otro punto
    rnd = random.Random(seed)
    zoom, dx, dy = 1.0, 0.0, 0.0
    for k, (a, _, _, _) in enumerate(chunks):
        ox, oy = rnd.uniform(-0.09, 0.09), rnd.uniform(-0.09, 0.09)
        if t >= a - 0.1:
            p = ease_out_cubic((t - a + 0.1) / 0.45)
            dx, dy = dx + (ox - dx) * p, dy + (oy - dy) * p
            kick = math.exp(-max(0, t - a) * 2.2) * clamp((t - a + 0.1) / 0.12)
            zoom = 1 - 0.09 * kick
    # cámara en mano (suma de senos)
    hx = math.sin(t * 1.3 + seed) * 0.012 + math.sin(t * 2.9 + 2 * seed) * 0.006
    hy = math.cos(t * 1.1 + seed) * 0.012 + math.sin(t * 3.7 + seed) * 0.005
    s2 = s * zoom
    cx = x + s / 2 + (dx + hx) * s
    cy = y + s / 2 + (dy + hy) * s
    return cx - s2 / 2, cy - s2 / 2, s2


def panel_img(box, angle, extra=1.0):
    x, y, s = box
    s *= extra
    m = s * 0.08  # margen para rotar sin esquinas vacías
    src = tuple(v * UP for v in (x + PAD - m, y + PAD - m, x + PAD + s + m, y + PAD + s + m))
    side = int(PANEL * (1 + 0.16))
    if min(src) < 0 or src[2] > big.width or src[3] > big.height:
        im = big.crop(tuple(int(v) for v in src)).resize((side, side), Image.BICUBIC)
    else:
        im = big.resize((side, side), Image.BICUBIC, box=src)
    if abs(angle) > 0.01:
        im = im.rotate(angle, Image.BICUBIC)
    o = (side - PANEL) // 2
    return im.crop((o, o, o + PANEL, o + PANEL))


def background(box, t):
    x, y, s = box
    cx, cy = (x + PAD + s / 2) * 2, (y + PAD + s / 2) * 2
    hh = s * 2 * 2.6 * (1 + 0.05 * math.sin(t * 0.4))
    ww = hh * W / H
    cx += math.sin(t * 0.5) * ww * 0.05
    b = tuple(int(v) for v in (cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2))
    return bgsrc.crop(b).resize((W // 2, H // 2), Image.BILINEAR).resize((W, H), Image.BILINEAR)


def glitch(im, amt):
    r, g, b = im.split()
    r = ImageChops.offset(r, int(amt), 0)
    b = ImageChops.offset(b, -int(amt), int(amt * 0.3))
    out = Image.merge("RGB", (r, g, b))
    # franjas desplazadas
    rnd = random.Random(int(amt * 1000))
    for _ in range(5):
        y0 = rnd.randint(0, H - 60)
        hgt = rnd.randint(8, 50)
        strip = out.crop((0, y0, W, y0 + hgt))
        out.paste(strip, (rnd.randint(-60, 60), y0))
    return out


def brackets(d, x0, y0, x1, y1, L, col, w=5):
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(x, y), (x + sx * L, y)], fill=col, width=w)
        d.line([(x, y), (x, y + sy * L)], fill=col, width=w)


# ====================== RENDER DE UNA ESCENA ======================
TIMELINE, STARTS, TOTAL = None, None, None


def render_scene(i):
    sc = ESCENAS[i]
    chunks, dur = TIMELINE[i]
    start = STARTS[i]
    n = len(ESCENAS)
    nf = int(round(dur * FPS))
    seed = i * 7 + 3
    layouts = [layout_words(txt, PY + PANEL + 30, 300) for (_, _, _, txt) in chunks]
    # tiempos de cada palabra, proporcionales a sus letras
    word_times = []
    for (a, b, _, txt), lay in zip(chunks, layouts):
        lens = [len(w) + 1 for _, _, w in lay]
        tot = sum(lens)
        acc, ts = 0, []
        for L in lens:
            ts.append(a + (b - a) * acc / tot)
            acc += L
        word_times.append(ts)
    title_lines = sc["title"].split("\n")
    title_chars = sum(len(t) for t in title_lines)
    ref_lines = wrap(_meas, "Fuente: " + sc["refs"], f_ref, W - 120)[:3]

    seg = os.path.join(TMP, f"seg{i:02d}.mp4")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-vf", "noise=alls=5:allf=t,vignette=PI/4.5",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", seg,
    ], stdin=subprocess.PIPE)

    for f in range(nf):
        t = f / FPS
        gt = start + t
        box = cam_box(sc, chunks, dur, t, seed)
        # latido: 0..1
        bp = (gt % (60 / BPM)) / (60 / BPM)
        heart = math.exp(-bp * 9) + 0.6 * math.exp(-max(0, bp - 0.22) * 9) * (bp > 0.22)

        # entrada y salida de escena
        tin = t / 0.55
        tout = (dur - t) / 0.35
        slide = (1 - ease_out_back(tin)) * (W + 40) if tin < 1 else 0
        exit_zoom = 1 + (1 - clamp(tout)) * 0.35
        angle = math.sin(t * 0.9 + seed) * 1.1 + (1 - clamp(tin)) * 6

        fr = background(box, gt)
        fr.paste(SHADE, (0, 0), SHADE)
        d = ImageDraw.Draw(fr)

        # panel con borde rojo que late
        pan = panel_img(box, angle, 1 / exit_zoom)
        bx = int(PX + slide)
        bw = int(6 + 4 * heart)
        d.rectangle([bx - bw, PY - bw, bx + PANEL + bw - 1, PY + PANEL + bw - 1], fill=RED)
        fr.paste(pan, (bx, PY))
        L = int(70 + 14 * heart)
        brackets(d, bx + 22, PY + 22, bx + PANEL - 23, PY + PANEL - 23, L, (255, 255, 255), 5)
        # retícula central que respira
        cxp, cyp = bx + PANEL // 2, PY + PANEL // 2
        r = 38 + 10 * heart
        d.ellipse([cxp - r, cyp - r, cxp + r, cyp + r], outline=RED, width=3)
        d.line([cxp - r - 18, cyp, cxp - r + 10, cyp], fill=RED, width=3)
        d.line([cxp + r - 10, cyp, cxp + r + 18, cyp], fill=RED, width=3)

        # cabecera
        d.rectangle([60, 58, 210, 110], fill=RED)
        d.text((72, 64), "2027", font=f_brand, fill=(255, 255, 255))
        if int(gt * 2) % 2 == 0:
            d.ellipse([232, 76, 250, 94], fill=RED)
        d.text((262, 70), "EXPEDIENTE: THE ECONOMIST", font=f_small, fill=(215, 215, 215))
        mm, ss = divmod(gt, 60)
        tc = f"{int(mm):02d}:{ss:05.2f}"
        d.text((W - 60 - d.textlength(tc, font=f_small), 70), tc, font=f_small, fill=(150, 150, 150))

        # etiqueta y título que se escriben solos
        nchar = int(clamp((t - 0.15) / 0.035, 0, len(sc["tag"])))
        d.text((60, 148), sc["tag"][:nchar] + ("▌" if nchar < len(sc["tag"]) else ""),
               font=f_tag, fill=RED)
        d.text((W - 60 - d.textlength(f"{i + 1:02d}/{n:02d}", font=f_small), 152),
               f"{i + 1:02d}/{n:02d}", font=f_small, fill=(150, 150, 150))
        shown = int(clamp((t - 0.25) / 0.03, 0, title_chars))
        ty = 196
        for k, ln in enumerate(title_lines):
            part = ln[:max(0, shown)]
            shown -= len(ln)
            off = (1 - ease_out_cubic((t - 0.25 - k * 0.15) / 0.5)) * -80
            d.text((60 + off, ty), part, font=f_title, fill=(255, 255, 255))
            ty += 92

        # subtítulos palabra por palabra
        for (a, b, c, txt), lay, wts in zip(chunks, layouts, word_times):
            if a - 0.05 <= t < c:
                cur = max([k for k, wt in enumerate(wts) if wt <= t] or [0])
                for k, ((x, y, wd), wt) in enumerate(zip(lay, wts)):
                    if wt > t + 0.02:
                        break
                    pop = ease_out_back((t - wt) / 0.18)
                    yy = y + (1 - pop) * 22
                    if k == cur and t < b:
                        tw = d.textlength(wd, font=f_sub)
                        d.rectangle([x - 8, yy - 2, x + tw + 8, yy + 58], fill=RED)
                    d.text((x, yy), wd, font=f_sub, fill=(255, 255, 255),
                           stroke_width=2, stroke_fill=(0, 0, 0))
                break

        # referencias
        ra = clamp((t - 0.8) / 0.5)
        if ra > 0:
            col = tuple(int(c * ra) for c in (165, 165, 165))
            d.line([60, 1752, 60 + int((W - 120) * ra), 1752], fill=(90, 90, 90), width=2)
            yy = 1766
            for ln in ref_lines:
                d.text((60, yy), ln, font=f_ref, fill=col)
                yy += 32

        # barra de progreso
        d.rectangle([0, H - 12, int(W * gt / TOTAL), H], fill=RED)

        # transición: destello rojo + glitch al entrar, oscurecer al salir
        if t < 0.2:
            fr = glitch(fr, (0.2 - t) * 120)
            fr = Image.blend(fr, Image.new("RGB", (W, H), RED), (0.2 - t) / 0.2 * 0.45)
        if tout < 1:
            fr = Image.blend(Image.new("RGB", (W, H), BG), fr, 0.35 + 0.65 * clamp(tout))
        ff.stdin.write(fr.tobytes())

    ff.stdin.close()
    ff.wait()
    print(f"escena {i + 1}/{n} lista", flush=True)
    return seg


def _init(tl, st, tot):
    global TIMELINE, STARTS, TOTAL
    TIMELINE, STARTS, TOTAL = tl, st, tot


if __name__ == "__main__":
    tl, st, tot = build_audio()
    _init(tl, st, tot)
    # escenas largas primero para repartir mejor la carga
    order = sorted(range(len(ESCENAS)), key=lambda k: -tl[k][1])
    if os.environ.get("ONLY") == "auto":  # solo escenas que faltan o no cuadran con el audio
        def frames(k):
            r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                                "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0",
                                os.path.join(TMP, f"seg{k:02d}.mp4")], capture_output=True, text=True)
            return r.stdout.strip()
        order = [k for k in order if frames(k) != str(int(round(tl[k][1] * FPS)))]
        print("re-render:", order, flush=True)
    elif os.environ.get("ONLY"):  # volver a renderizar solo algunas escenas
        order = [int(k) for k in os.environ["ONLY"].split(",")]
    with Pool(os.cpu_count(), initializer=_init, initargs=(tl, st, tot)) as pool:
        pool.map(render_scene, order, chunksize=1)
    lst = os.path.join(TMP, "lista.txt")
    with open(lst, "w") as fh:
        for i in range(len(ESCENAS)):
            fh.write(f"file 'seg{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", os.path.join(TMP, "mix.wav"),
                    "-vf", "hqdn3d=3:2:5:5,noise=alls=4:allf=t", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("OK", OUT, f"{tot:.1f}s")
