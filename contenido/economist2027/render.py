"""Renderiza el video vertical (1080x1920) sobre la portada de The Economist 2027.

Uso: python3 render.py <portada.png> <salida.mp4> <carpeta_temporal>
Requiere: ffmpeg, espeak-ng con la voz MBROLA mx2, Pillow, numpy.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from escenas import ESCENAS, PRONUNCIA  # noqa: E402

COVER, OUT, TMP = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(TMP, exist_ok=True)

W, H, FPS, SR = 1080, 1920, 30, 22050
RED = (227, 18, 11)
BG = (14, 14, 14)
PANEL = 960
PANEL_Y = 420
UP = 4      # pre-escalado de la portada
PAD = 220   # margen blanco alrededor de la portada (para zooms amplios)

F = "/usr/share/fonts/truetype/"
f_title = ImageFont.truetype(F + "liberation/LiberationSerif-Bold.ttf", 78)
f_tag = ImageFont.truetype(F + "dejavu/DejaVuSans-Bold.ttf", 30)
f_sub = ImageFont.truetype(F + "dejavu/DejaVuSans-Bold.ttf", 44)
f_ref = ImageFont.truetype(F + "dejavu/DejaVuSans.ttf", 25)
f_brand = ImageFont.truetype(F + "liberation/LiberationSerif-Bold.ttf", 34)


# ---------- voz ----------
def say_text(s):
    for k, v in PRONUNCIA.items():
        s = s.replace(k, v)
    return s


def tts(text, path):
    subprocess.run(["espeak-ng", "-v", "mb-mx2", "-s", "168", "-p", "45",
                    "-w", path, say_text(text)], check=True,
                   stderr=subprocess.DEVNULL)
    # normaliza a mono 22050 Hz
    out = path.replace(".wav", "_n.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1",
                    "-ar", str(SR), out], check=True)
    with wave.open(out) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return a.astype(np.float32) / 32768.0


# ---------- texto ----------
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


def sub_layer(text):
    im = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = wrap(d, text, f_sub, W - 120)
    lh = 58
    y = (330 - lh * len(lines)) // 2
    for ln in lines:
        tw = d.textlength(ln, font=f_sub)
        d.text(((W - tw) / 2, y), ln, font=f_sub, fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0))
        y += lh
    return im


def base_frame(sc, idx, total):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # marca superior
    d.rectangle([60, 60, 60 + 150, 60 + 52], fill=RED)
    d.text((72, 66), "2027", font=f_brand, fill=(255, 255, 255))
    d.text((230, 72), "LA PORTADA DE THE ECONOMIST, DESCIFRADA", font=f_ref,
           fill=(200, 200, 200))
    # etiqueta + título
    d.text((60, 150), sc["tag"], font=f_tag, fill=RED)
    y = 196
    for ln in sc["title"].split("\n"):
        d.text((60, y), ln, font=f_title, fill=(255, 255, 255))
        y += 86
    # marco del panel
    d.rectangle([60 - 6, PANEL_Y - 6, 60 + PANEL + 5, PANEL_Y + PANEL + 5], fill=RED)
    # referencias
    d.line([60, 1745, W - 60, 1745], fill=(70, 70, 70), width=2)
    refl = wrap(d, "Fuente: " + sc["refs"], f_ref, W - 120)
    yy = 1762
    for ln in refl[:3]:
        d.text((60, yy), ln, font=f_ref, fill=(160, 160, 160))
        yy += 32
    d.text((W - 60 - d.textlength(f"{idx + 1}/{total}", font=f_ref), 150),
           f"{idx + 1}/{total}", font=f_ref, fill=(140, 140, 140))
    return im


# ---------- portada ----------
cov = Image.open(COVER).convert("RGB")
padded = Image.new("RGB", (cov.width + 2 * PAD, cov.height + 2 * PAD), (246, 246, 246))
padded.paste(cov, (PAD, PAD))
big = padded.resize((padded.width * UP, padded.height * UP), Image.LANCZOS)
big = big.filter(ImageFilter.UnsharpMask(radius=3, percent=90, threshold=2))


def ease(t):
    return t * t * (3 - 2 * t)


def panel_at(b0, b1, t):
    e = ease(t)
    x = b0[0] + (b1[0] - b0[0]) * e
    y = b0[1] + (b1[1] - b0[1]) * e
    s = b0[2] + (b1[2] - b0[2]) * e
    box = tuple(v * UP for v in ((x + PAD), (y + PAD), (x + PAD + s), (y + PAD + s)))
    return big.resize((PANEL, PANEL), Image.BICUBIC, box=box)


# ---------- audio por escena ----------
GAP, HEAD, TAIL = 0.22, 0.35, 0.55
timeline = []  # (escena, [(inicio, fin, texto)], duración)
voice_parts = []
for i, sc in enumerate(ESCENAS):
    t = HEAD
    chunks = []
    seg = [np.zeros(int(HEAD * SR), np.float32)]
    for j, line in enumerate(sc["lines"]):
        a = tts(line, os.path.join(TMP, f"v{i:02d}_{j}.wav"))
        d = len(a) / SR
        chunks.append((t, t + d + GAP, line))
        seg += [a, np.zeros(int(GAP * SR), np.float32)]
        t += d + GAP
    seg.append(np.zeros(int(TAIL * SR), np.float32))
    dur = t + TAIL
    voice_parts.append(np.concatenate(seg)[: int(dur * SR)])
    timeline.append((sc, chunks, dur))
    print(f"escena {i:02d} {sc['tag']}: {dur:.1f}s", flush=True)

voice = np.concatenate(voice_parts)
total_s = len(voice) / SR

# música de fondo: pad grave + pulso suave (generada, sin derechos)
tt = np.arange(len(voice)) / SR
chords = [(55.0, 82.41, 130.81), (49.0, 73.42, 116.54), (43.65, 65.41, 103.83), (46.25, 69.3, 110.0)]
music = np.zeros_like(voice)
for k, ch in enumerate(chords):
    mask = ((tt // 8).astype(int) % len(chords)) == k
    for f0 in ch:
        music += mask * (np.sin(2 * np.pi * f0 * tt) + 0.3 * np.sin(2 * np.pi * 2 * f0 * tt))
music *= 0.5 + 0.5 * np.sin(2 * np.pi * tt / 8 - np.pi / 2) ** 2
pulse = np.exp(-((tt % 1.0) * 9)) * np.sin(2 * np.pi * 41.2 * tt)
music = music / np.max(np.abs(music)) * 0.07 + pulse * 0.05
fade = np.minimum(1, np.minimum(tt / 2, (total_s - tt) / 3))
mix = voice / max(1e-6, np.max(np.abs(voice))) * 0.85 + music * fade
mix = np.clip(mix, -1, 1)
with wave.open(os.path.join(TMP, "mix.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---------- video ----------
ff = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", os.path.join(TMP, "mix.wav"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

elapsed = 0.0
n = len(timeline)
for i, (sc, chunks, dur) in enumerate(timeline):
    base = base_frame(sc, i, n)
    subs = [(a, b, sub_layer(txt)) for a, b, txt in chunks]
    nf = int(round(dur * FPS))
    for f in range(nf):
        t = f / FPS
        fr = base.copy()
        fr.paste(panel_at(sc["box"][0], sc["box"][1], t / dur), (60, PANEL_Y))
        for a, b, layer in subs:
            if a <= t < b:
                alpha = min(1.0, (t - a) * 6)
                if alpha < 1:
                    layer = layer.copy()
                    layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
                fr.paste(layer, (0, PANEL_Y + PANEL - 330 + 300 + 40), layer)
                break
        # barra de progreso
        p = (elapsed + t) / total_s
        d = ImageDraw.Draw(fr)
        d.rectangle([0, H - 10, int(W * p), H], fill=RED)
        # fundido de entrada por escena
        if f < 8:
            fr = Image.blend(Image.new("RGB", (W, H), BG), fr, (f + 1) / 8)
        ff.stdin.write(fr.tobytes())
    elapsed += dur
    print(f"render {i + 1}/{n}", flush=True)

ff.stdin.close()
ff.wait()
print("OK", OUT, f"{total_s:.1f}s")
