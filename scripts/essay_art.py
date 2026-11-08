"""Generated artwork used by the designed essays in essay-sources/.

    python scripts/essay_art.py

Writes Mandelbrot / Julia renders for the fractal essay and Turing (Gray-Scott)
reaction-diffusion patterns for the patterns-in-nature essay.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "essay-sources"


def palette(t, stops):
    """Map t in [0,1] through a list of (pos, (r,g,b)) colour stops."""
    pos = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], float)
    out = np.empty(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, pos, cols[:, c])
    return out.clip(0, 255).astype(np.uint8)


SPACE = [(0, (4, 10, 24)), (.15, (10, 40, 70)), (.35, (20, 120, 140)), (.55, (120, 220, 210)),
         (.7, (250, 240, 200)), (.85, (240, 140, 60)), (1, (120, 30, 60))]


def escape(z, c, it):
    n = np.zeros(z.shape); alive = np.ones(z.shape, bool)
    for i in range(it):
        z[alive] = z[alive] ** 2 + (c[alive] if np.ndim(c) else c)
        esc = alive & (np.abs(z) > 4)
        n[esc] = i + 1 - np.log2(np.log(np.abs(z[esc])))
        alive &= ~esc
    return n, alive


def mandelbrot(path, w, h, cx, cy, span, it=400, inside=(2, 6, 16)):
    x = np.linspace(cx - span, cx + span, w); y = np.linspace(cy - span * h / w, cy + span * h / w, h)
    c = x[None, :] + 1j * y[:, None]
    n, alive = escape(np.zeros_like(c), c, it)
    t = (np.sqrt(n / it) * 2.2) % 1.0
    img = palette(t, SPACE); img[alive] = inside
    Image.fromarray(img).save(path, quality=92)


def julia(path, w, h, c, span=1.6, it=300):
    x = np.linspace(-span, span, w); y = np.linspace(-span * h / w, span * h / w, h)
    z = x[None, :] + 1j * y[:, None]
    n, alive = escape(z, c, it)
    t = (np.sqrt(n / it) * 1.6) % 1.0
    img = palette(t, [(0, (6, 8, 30)), (.3, (60, 20, 110)), (.55, (200, 60, 160)), (.75, (255, 190, 120)), (1, (255, 250, 230))])
    img[alive] = (6, 8, 30)
    Image.fromarray(img).save(path, quality=92)


def lap(a):
    return np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1) - 4 * a


def gray_scott(path, n, f, k, steps, colours, seed=3):
    rng = np.random.default_rng(seed)
    u = np.ones((n, n)); v = np.zeros((n, n))
    for _ in range(int(n * n / 900)):
        x, y = rng.integers(5, n - 5, 2); u[x-3:x+3, y-3:y+3] = .5; v[x-3:x+3, y-3:y+3] = .25
    v += rng.random((n, n)) * .02
    for _ in range(steps):
        uvv = u * v * v
        u += .16 * lap(u) - uvv + f * (1 - u)
        v += .08 * lap(v) + uvv - (f + k) * v
    t = (v - v.min()) / (v.max() - v.min() + 1e-9)
    Image.fromarray(palette(t, colours)).resize((n * 3, n * 3), Image.BICUBIC).save(path, quality=92)


if __name__ == "__main__":
    F = ROOT / "planet-of-fractal-geometry" / "img"
    mandelbrot(F / "gen-mandelbrot-cover.jpg", 1700, 2400, -0.745, 0.11, 0.035, it=700)
    mandelbrot(F / "gen-mandelbrot-map.jpg", 1600, 1100, -0.6, 0.0, 1.55, it=300)
    julia(F / "gen-julia.jpg", 1400, 900, complex(-0.8, 0.156))
    P = ROOT / "patterns-in-nature" / "img"
    LEO = [(0, (238, 196, 120)), (.45, (214, 150, 70)), (.62, (120, 70, 30)), (1, (30, 20, 12))]
    gray_scott(P / "gen-spots.jpg", 260, .035, .065, 9000, LEO)
    gray_scott(P / "gen-stripes.jpg", 260, .042, .059, 9000, [(0, (245, 240, 228)), (.5, (150, 140, 120)), (1, (20, 20, 22))])
    gray_scott(P / "gen-maze.jpg", 260, .029, .057, 9000, [(0, (230, 236, 210)), (.5, (110, 140, 70)), (1, (30, 50, 25))])
    gray_scott(P / "gen-cover.jpg", 360, .0367, .0649, 12000, LEO, seed=11)
    print("done")
