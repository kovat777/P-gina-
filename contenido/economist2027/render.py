"""Renderiza el video vertical (1080x1920) sobre la portada de The Economist 2027.

Uso: python3 render.py <portada.png> <salida.mp4> <carpeta_temporal> <voz_piper_sin_ext>
Requiere: ffmpeg, piper-tts (voz es_MX-ald-medium), Pillow, numpy.
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
# ruta al modelo Piper sin extensión, p. ej. .../es_MX-ald-medium
VOICE = sys.argv[4]
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
    # voz neuronal Piper (es_MX-ald), pausada; sin cambiar el tono para no deformarla
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE + ".onnx",
                    "-c", VOICE + ".onnx.json", "--length-scale", "1.15",
                    "--sentence-silence", "0.35", "-f", path],
                   input=say_text(text).encode(), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # solo un poco de cuerpo en graves y una reverberación muy suave
    out = path.replace(".wav", "_n.wav")
    fx = ("highpass=f=70,equalizer=f=180:t=q:w=1.2:g=2.5,"
          "aecho=0.9:0.9:45:0.10,volume=0.9")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1",
                    "-af", fx, "-ar", str(SR), out], check=True)
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
GAP, HEAD, TAIL = 0.42, 0.7, 0.8
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

# banda sonora de suspenso (generada, sin derechos):
# dron grave disonante + latido de corazón + tono agudo inquietante + golpe en cada escena
tt = np.arange(len(voice)) / SR
rng = np.random.default_rng(7)
TWO_PI = 2 * np.pi

# Todo en frecuencias que un parlante de celular reproduce sin distorsión (>= 90 Hz)
# y con envolventes suaves (sin ataques bruscos que produzcan chasquidos).
def smooth_env(x, attack, decay):
    return np.where(x < 0, 0, np.minimum(1, x / attack) * np.exp(-np.clip(x - attack, 0, None) * decay))


# pad oscuro en re menor con una segunda menor que crea tensión, entrando y saliendo lento
drone = np.zeros_like(voice)
for f0, g in ((146.83, 1.0), (174.61, 0.55), (220.0, 0.45), (155.56, 0.18)):
    for det in (-0.6, 0.6):
        drone += g * np.sin(TWO_PI * (f0 + det) * tt)
drone *= 0.55 + 0.45 * np.sin(TWO_PI * tt / 12) ** 2
drone /= np.max(np.abs(drone))

# latido lento (lub-dub, ~56 ppm) en tono audible y redondeado
beat = np.zeros_like(voice)
ph = tt % (60 / 56)
for off, amp in ((0.0, 1.0), (0.24, 0.6)):
    beat += amp * smooth_env(ph - off, 0.012, 14) * np.sin(TWO_PI * 95 * tt)

# "whoosh" suave al cambiar de escena: ruido filtrado que crece y se apaga
hits = np.zeros_like(voice)
starts = np.cumsum([0] + [d for _, _, d in timeline[:-1]])
kern = np.ones(40) / 40
for s in starts:
    i0 = int(max(0, s - 0.6) * SR)
    n = min(int(1.6 * SR), len(hits) - i0)
    x = np.arange(n) / SR
    noise = np.convolve(rng.standard_normal(n), kern, mode="same")
    env = np.sin(np.pi * np.clip(x / 1.6, 0, 1)) ** 2
    hits[i0:i0 + n] += noise * env / (np.max(np.abs(noise)) + 1e-9)

music = drone * 0.05 + beat * 0.07 + hits * 0.05
fade = np.minimum(1, np.minimum(tt / 2, (total_s - tt) / 4))
mix = voice / max(1e-6, np.max(np.abs(voice))) * 0.8 + music * fade
mix = mix / max(1.0, np.max(np.abs(mix)) / 0.89)  # sin recortes
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
