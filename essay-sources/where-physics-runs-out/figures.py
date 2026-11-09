# Draws the diagrams in img/ for this essay:  python essay-sources/where-physics-runs-out/figures.py
# Needs numpy, scipy, matplotlib and pillow.
import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Polygon, FancyBboxPatch, Wedge
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
os.makedirs(OUT, exist_ok=True)

INK = "#1b1f2a"; MUTED = "#6b7080"; GRID = "#d9dce3"
ORANGE = "#e8772e"; GOLD = "#f2b544"; BLUE = "#2f6bd8"; PURPLE = "#7b4fd0"
TEAL = "#16927f"; RED = "#cf3f36"; SPACE = "#0b0e17"; PAPER = "#ffffff"

plt.rcParams.update({
    "font.family": "Segoe UI", "font.size": 10, "text.color": INK,
    "axes.edgecolor": "#9aa0ad", "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "svg.fonttype": "none", "axes.titleweight": "bold", "axes.titlesize": 11,
    "mathtext.fontset": "dejavusans",
})

def save(fig, name, png=False):
    if png:
        fig.savefig(os.path.join(OUT, name + ".png"), dpi=220, bbox_inches="tight", pad_inches=0.05, facecolor=fig.get_facecolor())
    else:
        fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight", pad_inches=0.05, facecolor=fig.get_facecolor())
    plt.close(fig)

def arrow(ax, p, q, color=INK, lw=1.4, style="-|>", ms=12, **kw):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, **kw))

# ---------------------------------------------------------------- cover art
def black_hole_image(N=1400, incl=0.22, glow=True):
    """Stylised render: shadow, photon ring, thin disk with Doppler beaming, lensed far side of disk."""
    y, x = np.mgrid[-1:1:N*1j, -1.6:1.6:int(N*1.6)*1j]
    img = np.zeros(x.shape + (3,))
    r_sh = 0.26
    rr = np.hypot(x, y)
    # front disk: ellipse projection
    ry = y / incl
    rd = np.hypot(x, ry)
    disk = (rd > 0.36) & (rd < 1.35)
    prof = np.where(disk, (0.36 / np.maximum(rd, 1e-3)) ** 1.6, 0) * np.clip((rd - 0.36) / 0.05, 0, 1)
    beam = 1 + 0.75 * (-x / np.maximum(rd, 1e-3))            # approaching side (left) brighter
    front = (y < 0) | (rr > r_sh * 1.05)
    disk_I = prof * beam * front
    # lensed far side: an arc wrapping over the shadow
    ang = np.arctan2(y, x)
    lens_r = 0.30 + 0.10 * np.abs(np.cos(ang)) ** 2
    lensed = np.exp(-((rr - lens_r - 0.07) / 0.06) ** 2) * (y > -0.02) * (1 + 0.5 * (-x / np.maximum(rr, 1e-3)))
    lensed_under = np.exp(-((rr - 0.30) / 0.025) ** 2) * (y < 0) * 0.5
    ring = np.exp(-((rr - r_sh * 1.07) / 0.010) ** 2) * 1.4
    I = disk_I * 1.2 + lensed * 0.9 + lensed_under + ring
    I = I + gaussian_filter(I, 18) * 0.9 + gaussian_filter(I, 60) * 0.6
    I = I * (rr > r_sh) + gaussian_filter(I * (rr > r_sh), 2) * (rr <= r_sh) * 0.15
    I = I / np.percentile(I, 99.7)
    c1 = np.array([1.0, 0.86, 0.62]); c2 = np.array([0.95, 0.42, 0.12]); c3 = np.array([0.35, 0.06, 0.04])
    t = np.clip(I, 0, 1.6)[..., None]
    col = np.where(t > 0.6, c2 + (c1 - c2) * np.clip((t - 0.6) / 0.6, 0, 1), c3 + (c2 - c3) * np.clip(t / 0.6, 0, 1))
    img = col * np.clip(t, 0, 1) ** 0.85
    # stars
    rng = np.random.default_rng(3)
    bg = np.zeros(x.shape)
    idx = rng.integers(0, x.size, 900)
    bg.flat[idx] = rng.random(900) ** 3
    bg = gaussian_filter(bg, 0.8) * 4 * (I[..., ] < 0.05)
    img = img + np.clip(bg, 0, 1)[..., None] * np.array([0.8, 0.85, 1.0])
    base = np.array([11, 14, 23]) / 255
    img = np.clip(img + base, 0, 1)
    return img

def fig_cover():
    img = black_hole_image()
    fig = plt.figure(figsize=(8, 5), facecolor=SPACE)
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img, origin="lower", interpolation="bilinear"); ax.axis("off")
    save(fig, "cover", png=True)

# ---------------------------------------------------------------- two theories
def fig_two_theories():
    fig, ax = plt.subplots(figsize=(7.2, 3.6)); ax.set_xlim(0, 10); ax.set_ylim(-0.9, 4.6); ax.axis("off"); ax.set_aspect("equal")
    ax.add_patch(Circle((3.4, 2.3), 2.05, color=BLUE, alpha=0.10, lw=0))
    ax.add_patch(Circle((3.4, 2.3), 2.05, fill=False, ec=BLUE, lw=2))
    ax.add_patch(Circle((6.6, 2.3), 2.05, color=PURPLE, alpha=0.10, lw=0))
    ax.add_patch(Circle((6.6, 2.3), 2.05, fill=False, ec=PURPLE, lw=2))
    ax.text(2.75, 3.45, "General relativity", ha="center", weight="bold", color=BLUE, fontsize=11.5)
    ax.text(2.75, 3.05, "the very big & heavy", ha="center", color=MUTED, fontsize=9)
    for i, s in enumerate(["planets & orbits", "GPS clocks", "bending light", "grav. waves"]):
        ax.text(2.75, 2.45 - i * 0.38, s, ha="center", fontsize=9.5)
    ax.text(7.25, 3.45, "Quantum mechanics", ha="center", weight="bold", color=PURPLE, fontsize=11.5)
    ax.text(7.25, 3.05, "the very small", ha="center", color=MUTED, fontsize=9)
    for i, s in enumerate(["atoms & electrons", "lasers & chips", "the Sun's fusion", "particle physics"]):
        ax.text(7.25, 2.45 - i * 0.38, s, ha="center", fontsize=9.5)
    ax.add_patch(Circle((5, 2.3), 0.62, color=INK))
    ax.text(5, 2.42, "?", ha="center", va="center", color="white", fontsize=22, weight="bold")
    ax.text(5, -0.75, "Very big AND very small at once:\nthe centre of a black hole, the Big Bang", ha="center", fontsize=9.5, weight="bold")
    arrow(ax, (5, -0.05), (5, 1.6), color=INK, lw=1.2)
    save(fig, "two_theories")

# ---------------------------------------------------------------- curved grid
def fig_grid():
    fig = plt.figure(figsize=(7.4, 3.0))
    ax = fig.add_axes([-0.25, -0.45, 1.5, 1.9], projection="3d")
    R = np.linspace(0.35, 3.2, 40); T = np.linspace(0, 2 * np.pi, 72)
    RR, TT = np.meshgrid(R, T)
    Z = -1.0 / RR
    X, Y = RR * np.cos(TT), RR * np.sin(TT)
    ax.plot_wireframe(X, Y, Z, rstride=3, cstride=3, color=BLUE, lw=0.5, alpha=0.65)
    # orbit
    th = np.linspace(0, 2 * np.pi, 200); ro = 1.6
    ax.plot(ro * np.cos(th), ro * np.sin(th), -1 / ro + 0.03, color=ORANGE, lw=2)
    ax.scatter([ro * np.cos(0.6)], [ro * np.sin(0.6)], [-1 / ro + 0.08], color=ORANGE, s=60, depthshade=False)
    ax.scatter([0], [0], [-2.6], color=INK, s=140, depthshade=False)
    ax.set_zlim(-2.9, 0.1); ax.view_init(elev=24, azim=-60); ax.set_box_aspect((1, 1, 0.45)); ax.axis("off")
    fn = os.path.join(OUT, "grid.png"); fig.savefig(fn, dpi=220); plt.close(fig)
    from PIL import Image, ImageChops
    im = Image.open(fn).convert("RGB"); bg = Image.new("RGB", im.size, (255, 255, 255))
    bb = ImageChops.difference(im, bg).getbbox(); im.crop((bb[0] - 20, bb[1] - 20, bb[2] + 20, bb[3] + 20)).save(fn)

# ---------------------------------------------------------------- stellar fates
def fig_fates():
    fig, ax = plt.subplots(figsize=(7.4, 3.3)); ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis("off")
    # star
    for r, a in [(0.95, 0.15), (0.8, 0.3), (0.65, 1)]:
        ax.add_patch(Circle((1.2, 2.2), r, color=GOLD, alpha=a, lw=0))
    ax.text(1.2, 2.2, "Star", ha="center", va="center", weight="bold")
    ax.text(1.2, 0.9, "fusion pressure\nholds up\nagainst gravity", ha="center", fontsize=8.5, color=MUTED)
    ax.text(3.3, 2.75, "fuel runs out\ncore collapses", ha="center", fontsize=8.5, color=MUTED)
    rows = [(3.65, "White dwarf", "core < 1.4 Suns", "held up by electron pressure", "#e8eefc", 0.32, INK),
            (2.2, "Neutron star", "core ~1.4–3 Suns", "held up by neutron pressure", "#c9d6f2", 0.22, INK),
            (0.75, "Black hole", "core > ~3 Suns", "nothing known can stop collapse", INK, 0.26, INK)]
    for yv, name, mass, why, fc, r, ec in rows:
        arrow(ax, (2.35, 2.2), (4.55, yv), color=MUTED, lw=1.2)
        ax.add_patch(Circle((5.0, yv), r, fc=fc, ec=ec, lw=1.2))
        if name == "Black hole":
            ax.add_patch(Circle((5.0, yv), r + 0.12, fill=False, ec=ORANGE, lw=2.2, alpha=0.9))
        ax.text(5.55, yv + 0.12, name, weight="bold", va="center", fontsize=10.5)
        ax.text(5.55, yv - 0.24, f"{mass}  ·  {why}", va="center", fontsize=8.8, color=MUTED)
    save(fig, "fates")

# ---------------------------------------------------------------- anatomy
def fig_anatomy():
    fig, ax = plt.subplots(figsize=(7.6, 4.4), facecolor=SPACE); ax.set_facecolor(SPACE)
    ax.set_xlim(-6.2, 6.2); ax.set_ylim(-3.2, 3.6); ax.set_aspect("equal"); ax.axis("off")
    rs = 1.0
    # jets
    for s in (1, -1):
        ax.add_patch(Polygon([[-0.12, 0.3 * s], [0.12, 0.3 * s], [0.55, 3.4 * s], [-0.55, 3.4 * s]], color="#7fb3ff", alpha=0.22, lw=0))
        ax.add_patch(Polygon([[-0.05, 0.3 * s], [0.05, 0.3 * s], [0.22, 3.4 * s], [-0.22, 3.4 * s]], color="#bcd6ff", alpha=0.45, lw=0))
    # disk (edge-on-ish ellipse bands)
    for rin, rout, c, a in [(3.0, 5.6, ORANGE, 0.25), (3.0, 4.6, ORANGE, 0.45), (3.0, 3.8, GOLD, 0.8)]:
        for s in (1, -1):
            xs = np.linspace(rin, rout, 2) * s
            ax.add_patch(Ellipse((0, 0), 2 * rout, 0.55 * rout / 3, color=c, alpha=a * 0.6, lw=0))
    ax.add_patch(Ellipse((0, 0), 2 * 3.0, 0.5, color=SPACE, lw=0))
    # photon sphere
    ax.add_patch(Circle((0, 0), 1.5 * rs, fill=False, ec="#f5d08a", lw=1.2, ls=(0, (4, 3))))
    # horizon
    ax.add_patch(Circle((0, 0), rs, color="black", ec="#ff9a4d", lw=2))
    ax.add_patch(Circle((0, 0), 0.06, color="white"))
    # front part of disk over the hole
    ax.add_patch(Polygon([[-3.0, 0], [3.0, 0], [3.0, -0.24], [-3.0, -0.24]], color=SPACE, alpha=0))
    W = "#e9ecf3"
    def lab(xy, txt, xyt, sub=None, ha="left"):
        ax.annotate(txt, xy=xy, xytext=xyt, color=W, fontsize=10, weight="bold", ha=ha,
                    arrowprops=dict(arrowstyle="-", color="#8b93a7", lw=0.9, relpos=((1 if xyt[0] < 0 else 0), 0.5)))
        if sub:
            ax.text(xyt[0], xyt[1] + (0.38 if (xyt[0] < 0 and xyt[1] > -2) else -0.38), sub, color="#a5adc0", fontsize=8.2, ha=ha)
    lab((0.04, -0.04), "Singularity", (-6.0, -2.75), "where the classical maths fails", "left")
    lab((-0.72, 0.7), "Event horizon", (-6.0, 1.9), "point of no return (r = 2GM/c²)", "left")
    lab((1.06, 1.06), "Photon sphere", (2.6, 2.3), "light can circle here (1.5×)", "left")
    lab((4.4, 0.0), "Accretion disk", (3.4, -1.5), "hot gas glowing OUTSIDE", "left")
    lab((0.3, 2.6), "Jet", (1.4, 3.3), "plasma + magnetic fields", "left")
    lab((-3.0, -0.05), "Innermost stable orbit", (-6.0, -1.55), "gas spirals in past here (3×)", "left")
    save(fig, "anatomy")

# ---------------------------------------------------------------- light cones (Eddington–Finkelstein)
def fig_lightcones():
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    rs = 1.0
    ax.axvspan(0, rs, color=INK, alpha=0.07, lw=0)
    ax.axvline(rs, color=ORANGE, lw=2)
    ax.plot([0, 0], [0, 6.2], color=RED, lw=3)
    zz = np.linspace(0, 6.2, 60); ax.plot(0.03 * np.sin(zz * 12), zz, color=RED, lw=1.5)
    for r in [0.35, 0.65, 1.0, 1.45, 2.1, 3.0, 4.0]:
        for t0 in [1.55]:
            L = 0.6
            # ingoing ray: dt/dr = -1 ; outgoing: dt/dr = (1+rs/r)/(1-rs/r)
            p_in = np.array([-1, 1]) / np.sqrt(2) * L
            if abs(r - rs) < 1e-6:
                p_out = np.array([0, 1]) * L * 0.8
            else:
                k = (1 + rs / r) / (1 - rs / r)
                v = np.array([1, k]) if k > 0 else np.array([-1, -k])
                p_out = v / np.linalg.norm(v) * L * 0.85
            o = np.array([r, t0])
            col = BLUE if r > rs else (ORANGE if r == rs else PURPLE)
            ax.add_patch(Polygon([o, o + p_in, o + p_out], color=col, alpha=0.25, lw=0))
            ax.plot(*zip(o + p_in, o, o + p_out), color=col, lw=1.4)
            ax.plot(*o, "o", color=col, ms=3)
    ax.set_xlim(-0.15, 4.6); ax.set_ylim(0.5, 2.6); ax.set_aspect("equal")
    ax.set_xlabel("distance from centre  (in units of the horizon radius)")
    ax.set_ylabel("time  →")
    ax.set_yticks([]); ax.set_xticks([0, 1, 2, 3, 4])
    ax.text(0.06, 2.42, "singularity", color=RED, fontsize=9, weight="bold")
    ax.text(1.06, 2.42, "event horizon", color=ORANGE, fontsize=9, weight="bold")
    ax.text(1.9, 0.62, "OUTSIDE: some futures point outward", color=BLUE, fontsize=9)
    ax.text(0.07, 0.58, "INSIDE: every\nfuture points in", color=PURPLE, fontsize=9)
    save(fig, "lightcones")

# ---------------------------------------------------------------- time dilation
def fig_redshift():
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    r = np.linspace(1.0005, 8, 600)
    rate = np.sqrt(1 - 1 / r)
    ax.fill_between(r, rate, color=BLUE, alpha=0.10, lw=0)
    ax.plot(r, rate, color=BLUE, lw=2.4)
    ax.axvline(1, color=ORANGE, lw=2); ax.text(1.06, 0.92, "horizon", color=ORANGE, weight="bold", fontsize=9)
    for rv, t in [(1.33, "a quarter as fast"), (2.0, "71% speed"), (5.0, "89% speed")]:
        y = np.sqrt(1 - 1 / rv)
        ax.plot(rv, y, "o", color=INK, ms=5)
        ax.annotate(t, (rv, y), (rv + 0.35, y - 0.17), fontsize=8.8, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.axhline(1, color=GRID, lw=1, ls="--"); ax.text(6.5, 1.03, "a far-away clock", fontsize=8.8, color=MUTED)
    ax.set_xlim(0.6, 8); ax.set_ylim(0, 1.12)
    ax.set_xlabel("where a clock hovers  (distance ÷ horizon radius)")
    ax.set_ylabel("tick rate seen\nfrom far away")
    save(fig, "redshift")

# ---------------------------------------------------------------- Penrose diagram of collapse
def fig_penrose():
    fig, ax = plt.subplots(figsize=(3.3, 3.4)); ax.set_aspect("equal"); ax.axis("off")
    # exterior region: i0 at (2,0), scri+ from (1,1) to (2,0)? Use simple layout
    # coordinates: r=0 line (left) x=0 from y=-2 to y=0 for the star centre, singularity y=2 from x=0..2
    sing_y = 2.0
    ax.add_patch(Polygon([[0, -2], [0, sing_y], [2, sing_y], [4, 0], [0, -4 + 2 * 0]], color=BLUE, alpha=0.05, lw=0))
    ax.add_patch(Polygon([[0, 0], [0, sing_y], [2, sing_y]], color=INK, alpha=0.10, lw=0))  # interior
    # star (collapsing) region
    xs = np.linspace(-2, 0.7, 50)
    star_edge_x = 0.9 - 0.55 * (xs + 2) / 2.7
    ax.fill_betweenx(xs, 0, 0.9 - 0.25 * ((xs + 2) / 2.7) ** 2 * 3.0, color=GOLD, alpha=0.35, lw=0)
    # horizon
    ax.plot([0, 2], [0, sing_y], color=ORANGE, lw=2.2)
    # singularity
    xx = np.linspace(0.4, 2, 200); ax.plot(xx, sing_y + 0.05 * np.sin(xx * 40), color=RED, lw=2)
    # scri+ and boundary
    ax.plot([2, 4], [sing_y, 0], color=MUTED, lw=1.2, ls="--")
    ax.plot([4, 0.6], [0, -3.4], color=MUTED, lw=1.2, ls="--")
    ax.plot([0, 0], [-2.0, sing_y], color=MUTED, lw=1)
    # infaller worldline
    t = np.linspace(0, 1, 50)
    wx = 2.9 - 1.9 * t ** 1.4; wy = -1.4 + 3.35 * t
    ax.plot(wx, wy, color=PURPLE, lw=2.2)
    ax.plot(wx[-1], wy[-1], "o", color=PURPLE, ms=6)
    # escaping light from outside & trapped light inside
    arrow(ax, (2.55, -0.35), (3.35, 0.45), color=BLUE, lw=1.4)
    arrow(ax, (1.35, 1.75), (1.6, 1.98), color=PURPLE, lw=1.4, ms=9)
    ax.text(3.0, -0.55, "light\nescapes", fontsize=8.5, color=BLUE)
    ax.text(0.45, 2.15, "singularity\n(a moment in time)", fontsize=8, color=RED, ha="left", weight="bold")
    ax.text(0.42, 0.62, "horizon", color=ORANGE, fontsize=9, rotation=45, weight="bold")
    ax.text(0.18, 1.15, "inside", fontsize=9, color=INK)
    ax.text(1.05, -1.05, "outside\nuniverse", fontsize=9, color=INK)
    ax.text(0.12, -1.6, "collapsing\nstar", fontsize=8.5, color="#8a5a00")
    ax.text(2.55, -1.75, "you", fontsize=9, color=PURPLE, weight="bold")
    ax.set_xlim(-0.2, 4.3); ax.set_ylim(-2.1, 2.95)
    save(fig, "penrose")

# ---------------------------------------------------------------- tidal forces
def fig_tidal():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.3), gridspec_kw=dict(width_ratios=[1, 1.1]))
    a1.set_xlim(0.0, 5.2); a1.set_ylim(0.6, 3.6); a1.axis("off"); a1.set_aspect("equal")
    a1.add_patch(Circle((0.55, 2), 0.45, color=INK))
    for i, (x, L) in enumerate([(2.2, 1.0), (3.6, 0.65), (4.9, 0.42)]):
        pass
    # body as stretched capsule
    def body(cx, sx, sy):
        a1.add_patch(Ellipse((cx, 2), 1.2 * sx, 0.5 * sy, color=TEAL, alpha=0.85))
    body(3.2, 1.0, 1.0)
    a1.add_patch(Ellipse((3.2, 2), 2.6, 0.32, fill=False, ec=TEAL, ls="--", lw=1.2))
    for x0, L, c in [(2.55, 1.15, RED), (3.85, 0.55, RED)]:
        pass
    arrow(a1, (2.55, 2), (1.45, 2), color=RED, lw=2.4)    # feet pulled hard
    arrow(a1, (3.85, 2), (4.45, 2), color=BLUE, lw=2.0)   # head pulled less -> relatively away
    arrow(a1, (3.2, 2.9), (3.2, 2.35), color=PURPLE, lw=1.6, ms=10)
    arrow(a1, (3.2, 1.1), (3.2, 1.65), color=PURPLE, lw=1.6, ms=10)
    a1.text(1.95, 2.25, "feet: pulled\nharder", fontsize=8, ha="center", color=RED, va="bottom")
    a1.text(4.4, 2.25, "head: pulled\nless", fontsize=8, ha="center", color=BLUE, va="bottom")
    a1.text(3.2, 3.0, "squeezed sideways", fontsize=8, ha="center", color=PURPLE, va="bottom")
    a1.text(0.55, 1.3, "black\nhole", ha="center", fontsize=8.5, va="top")
    a1.set_title("Spaghettification", loc="left")
    # chart
    G = 6.674e-11; c = 2.998e8; Ms = 1.989e30; L = 2.0
    M = np.logspace(0, 10, 200)
    da = L * c ** 6 / (4 * G ** 2 * (M * Ms) ** 2) / 9.81
    a2.loglog(M, da, color=INK, lw=2.2)
    a2.axhspan(1e-8, 10, color=TEAL, alpha=0.08, lw=0); a2.axhline(10, color=TEAL, lw=1.2, ls="--")
    a2.text(1.5, 1e-6, "survivable (< 10 g)", color=TEAL, fontsize=8.5)
    a2.axhspan(10, 1e12, color=RED, alpha=0.05, lw=0)
    for m, n, dy in [(10, "10-Sun black hole", 3), (4.3e6, "Sgr A* (our galaxy)", 8), (6.5e9, "M87*", 8)]:
        y = L * c ** 6 / (4 * G ** 2 * (m * Ms) ** 2) / 9.81
        a2.plot(m, y, "o", color=ORANGE, ms=6, zorder=5)
        a2.annotate(n, (m, y), (m * (0.06 if m > 1e9 else 2.5), y * dy), fontsize=8.5,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    a2.set_ylim(1e-8, 1e12); a2.set_xlim(1, 1e10)
    a2.set_xlabel("black hole mass (in Suns)"); a2.set_ylabel("head-to-feet stretch\nat the horizon (g)")
    a2.set_title("Bigger hole → gentler horizon", loc="left")
    fig.tight_layout(w_pad=1.5)
    save(fig, "tidal")

# ---------------------------------------------------------------- Kerr
def fig_kerr():
    fig, ax = plt.subplots(figsize=(7.4, 3.6)); ax.set_aspect("equal"); ax.axis("off")
    a = 0.95; M = 1.0
    rp = M + np.sqrt(M ** 2 - a ** 2); rm = M - np.sqrt(M ** 2 - a ** 2)
    th = np.linspace(0, 2 * np.pi, 400)
    rE = M + np.sqrt(M ** 2 - a ** 2 * np.cos(th) ** 2)
    sc = 1.6
    ax.fill(sc * rE * np.sin(th), sc * rE * np.cos(th), color=PURPLE, alpha=0.16, lw=0)
    ax.plot(sc * rE * np.sin(th), sc * rE * np.cos(th), color=PURPLE, lw=1.6)
    ax.add_patch(Circle((0, 0), sc * rp, color=INK))
    ax.add_patch(Circle((0, 0), sc * rm, fill=False, ec="#ffb36b", lw=1.1, ls=(0, (3, 2))))
    ax.plot([0, 0], [-3.0, 3.0], color=MUTED, lw=1, ls="--")
    arrow(ax, (-0.55, 2.75), (0.55, 2.75), color=MUTED, lw=1.3, style="-|>", connectionstyle="arc3,rad=-0.4")
    ax.text(0.7, 2.75, "spin axis", fontsize=8.5, color=MUTED, va="center")
    # swirl arrows (frame dragging)
    for rr, al in [(2.55, 0.9), (3.1, 0.6)]:
        for ang in [200, 340]:
            t0 = np.radians(ang); t1 = t0 + np.radians(40)
            p = (rr * np.cos(t0), 0.42 * rr * np.sin(t0)); q = (rr * np.cos(t1), 0.42 * rr * np.sin(t1))
            arrow(ax, p, q, color=BLUE, lw=1.4, alpha=al, connectionstyle="arc3,rad=0.25")
    ax.text(-4.9, -1.75, "space itself is\ndragged around", color=BLUE, fontsize=8.8)
    ax.annotate("Ergosphere: you cannot stand still,\nbut you can still escape", (sc * 1.7, 0.6), (3.6, 1.6), fontsize=8.8, color=PURPLE,
                arrowprops=dict(arrowstyle="-", color=PURPLE, lw=0.8))
    ax.annotate("Outer event horizon", (sc * rp * 0.7, -sc * rp * 0.7), (3.6, -1.6), fontsize=8.8,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("Inner horizon (unstable?)", (-sc * rm * 0.7, sc * rm * 0.7), (-5.3, 2.55), fontsize=8.8, color="#b0601d",
                arrowprops=dict(arrowstyle="-", color="#b0601d", lw=0.8))
    ax.set_xlim(-5.3, 6.6); ax.set_ylim(-3.1, 3.2)
    save(fig, "kerr")

def fig_penrose_process():
    fig, ax = plt.subplots(figsize=(2.6, 3.2)); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Circle((0, 0), 2.0, color=PURPLE, alpha=0.14, lw=0))
    ax.add_patch(Circle((0, 0), 2.0, fill=False, ec=PURPLE, lw=1.2))
    ax.add_patch(Circle((0, 0), 1.15, color=INK))
    p = (1.25, 0.95)
    arrow(ax, (3.2, 2.3), p, color=INK, lw=1.8)
    arrow(ax, p, (0.75, 0.55), color=RED, lw=1.8)
    arrow(ax, p, (3.4, -0.6), color=ORANGE, lw=2.8)
    ax.plot(*p, "*", color=GOLD, ms=13, mec=INK, mew=0.5)
    ax.text(2.4, 2.45, "1. in", fontsize=8.5)
    ax.text(-2.1, -2.35, "2. one piece falls in\n    with \"negative\" energy", fontsize=8.5, color=RED, va="top")
    ax.text(-2.1, -3.25, "3. the other leaves with\n    MORE energy than it brought", fontsize=8.5, color="#b0561d", va="top")
    ax.set_xlim(-2.2, 3.6); ax.set_ylim(-4.3, 2.8)
    save(fig, "penrose_process")

# ---------------------------------------------------------------- curvature blow-up
def fig_curvature():
    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    G = 6.674e-11; c = 2.998e8; Ms = 1.989e30
    r = np.logspace(-26, 11, 600)
    lp = 1.616e-35; KP = 1 / lp ** 4
    for m, name, col in [(10, "10-Sun black hole", RED), (4.3e6, "Sgr A*", BLUE)]:
        K = 48 * G ** 2 * (m * Ms) ** 2 / (c ** 4 * r ** 6)
        rs = 2 * G * m * Ms / c ** 2
        ax.loglog(r, K, color=col, lw=2.2, label=name + "  (dot = its horizon)")
        Ks = 48 * G ** 2 * (m * Ms) ** 2 / (c ** 4 * rs ** 6)
        ax.plot(rs, Ks, "o", color=col, ms=6)

    ax.axhspan(KP, 1e180, color=PURPLE, alpha=0.12, lw=0)
    ax.axhline(KP, color=PURPLE, lw=1.4, ls="--")
    ax.text(5e10, KP * 1e7, "Planck-scale curvature: quantum gravity needed —\ngeneral relativity can no longer be trusted", color=PURPLE, fontsize=8.8, weight="bold")
    ax.set_ylim(1e-50, 1e175); ax.set_xlim(1e-26, 1e11)
    ax.set_xlabel("distance from the centre (metres)"); ax.set_ylabel("curvature  (tidal strength)")
    ax.set_yticks([1e-30, 1e0, 1e30, 1e60, 1e90, 1e120, 1e150])
    ax.invert_xaxis()
    ax.text(1e-12, 1e-45, "falling inward →", fontsize=8.8, color=MUTED)
    ax.legend(frameon=False, loc="center left", fontsize=8.8)
    save(fig, "curvature")

# ---------------------------------------------------------------- mass-size map
def fig_scales():
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    G = 6.674e-11; c = 2.998e8; h = 6.626e-34; hbar = 1.055e-34
    m = np.logspace(-40, 56, 300)
    rbh = 2 * G * m / c ** 2
    lam = hbar / (m * c)
    ax.loglog(m, rbh, color=INK, lw=2.4)
    ax.loglog(m, lam, color=PURPLE, lw=2.4)
    ax.fill_between(m, 1e-40, rbh, color=INK, alpha=0.08, lw=0)
    ax.fill_between(m, 1e-40, lam, color=PURPLE, alpha=0.08, lw=0)
    mp = np.sqrt(hbar * c / G); lp = np.sqrt(hbar * G / c ** 3)
    ax.add_patch(Ellipse((np.log10(mp), np.log10(lp)), 9, 9, transform=ax.transData, alpha=0))
    ax.plot(mp, lp, "o", ms=26, color=RED, alpha=0.18)
    ax.plot(mp, lp, "o", ms=7, color=RED)
    ax.annotate("Planck scale\nboth theories needed at once", (mp, lp), (1e-3, 1e-37), fontsize=8.8, color=RED, weight="bold",
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
    objs = [(9.1e-31, 2.8e-15, "electron", "right", 0.1, 1), (1.67e-27, 0.85e-15, "proton", "left", 8, 0.05), (1.7e-27, 5e-11, "atom", "left", 1, 1e2),
            (70, 1.0, "human", "left", 1e1, 1), (6e24, 6.4e6, "Earth", "right", 0.05, 1), (2e30, 7e8, "Sun", "right", 0.05, 30),
            (2.8e30, 1.2e4, "neutron star", "right", 0.05, 1),
            (8.6e36, 1.27e10, "Sgr A*", "right", 0.05, 30), (1.5e53, 4.4e26, "observable universe", "right", 0.05, 1)]
    for mm, rr, n, ha, dx, dy in objs:
        ax.plot(mm, rr, "o", color=BLUE, ms=5)
        ax.text(mm * dx, rr * dy, n, fontsize=8.3, color=INK, ha=ha, va="center")
    # labels running along the two lines
    def along(x0, slope, text, col, off):
        p1 = ax.transData.transform((x0, 2 * G * x0 / c ** 2 if slope > 0 else hbar / (x0 * c)))
        x1 = x0 * 10
        p2 = ax.transData.transform((x1, 2 * G * x1 / c ** 2 if slope > 0 else hbar / (x1 * c)))
        ang = np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0]))
        y0 = 2 * G * x0 / c ** 2 if slope > 0 else hbar / (x0 * c)
        ax.text(x0, y0 * off, text, rotation=ang, rotation_mode="anchor", fontsize=8.3, color=col, weight="bold", ha="left", va="center")
    ax.set_xlim(1e-40, 1e56); ax.set_ylim(1e-40, 1e30)
    ax.text(1e16, 1e-22, "BLACK HOLE LINE (black)\nsqueeze anything below it\nand it collapses", fontsize=8.3, color=INK, weight="bold")
    ax.text(1e-39, 1e-36, "QUANTUM LINE"+chr(10)+"below it:"+chr(10)+"things turn fuzzy", fontsize=8.3, color=PURPLE, weight="bold")
    # arrow: collapse heads down into quantum zone
    arrow(ax, (3e44, 4e17), (3e44, 1e-30), color=RED, lw=1.8)
    ax.text(1e45, 1e-12, "General relativity says\na black hole's matter keeps\nshrinking toward zero size,\ninto territory it cannot\ndescribe", fontsize=8.3, color=RED)
    ax.set_xlim(1e-40, 1e56); ax.set_ylim(1e-40, 1e30)
    ax.set_xlabel("mass (kg)"); ax.set_ylabel("size (m)")
    save(fig, "scales")

# ---------------------------------------------------------------- Hawking temperature
def fig_hawking():
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    Ms = 1.989e30
    M = np.logspace(8, 41, 300)  # kg
    T = 6.17e-8 * Ms / M
    ax.loglog(M, T, color=ORANGE, lw=2.4)
    ax.axhline(2.725, color=BLUE, lw=1.3, ls="--")
    ax.text(1e27, 0.012, "cosmic microwave background, 2.7 K (space's own glow)", color=BLUE, fontsize=8.6)
    ax.axhspan(2.725, 1e20, xmax=1, color=ORANGE, alpha=0.05, lw=0)
    ax.text(1e18, 1e8, "hotter than space:\nshrinks & eventually\nexplodes in a flash", color="#a04c12", fontsize=8.6)
    ax.text(1e9, 1e-13, "colder than space:\nabsorbs more than\nit radiates (today)", color=BLUE, fontsize=8.6)
    for m, n, ox, oy in [(7.35e22, "Moon's mass", 0.004, 1e-4), (6e24, "Earth's mass", 0.004, 1e-4), (2e31, "10 Suns", 0.004, 1e-4), (8.6e36, "Sgr A*", 30, 1e4)]:
        t = 6.17e-8 * Ms / m
        ax.plot(m, t, "o", color=INK, ms=5)
        ax.annotate(n, (m, t), (m * ox, t * oy), fontsize=8.4, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7))
    ax.set_xlabel("black hole mass (kg)"); ax.set_ylabel("Hawking temperature (K)")
    ax.set_ylim(1e-16, 1e17); ax.set_xlim(1e8, 1e41)
    save(fig, "hawking")

def fig_pair():
    fig, ax = plt.subplots(figsize=(2.7, 2.6)); ax.axis("off"); ax.set_xlim(0, 4); ax.set_ylim(0, 3.4)
    ax.add_patch(Polygon([[0, 0], [1.6, 0], [1.6, 3.4], [0, 3.4]], color=INK))
    ax.plot([1.6, 1.6], [0, 3.4], color=ORANGE, lw=2.5)
    ax.text(0.8, 0.2, "inside", color="white", ha="center", fontsize=8.5)
    ax.text(1.68, 3.15, "horizon", color=ORANGE, fontsize=8.5, weight="bold")
    t = np.linspace(0, 1, 60)
    ax.plot(1.75 + 0.15 * np.sin(t * 12), 0.9 + t * 0.9, color=GOLD, lw=1.4)
    arrow(ax, (1.8, 1.8), (1.2, 2.5), color=RED, lw=1.6)
    arrow(ax, (1.8, 1.8), (3.5, 2.9), color=GOLD, lw=2.2)
    ax.text(2.3, 1.0, "a pair of particles\nborrowed from\nempty space", fontsize=8, color=MUTED)
    ax.text(2.75, 2.0, "escapes as\nradiation", fontsize=8, color="#a8780e", va="bottom")
    ax.text(0.15, 2.65, "partner\nfalls in", fontsize=8, color="#ff8c80")
    save(fig, "pair")

# ---------------------------------------------------------------- entropy sphere
def fig_bits():
    fig, ax = plt.subplots(figsize=(3.6, 3.4)); ax.set_aspect("equal"); ax.axis("off")
    rng = np.random.default_rng(7)
    R = 1.0
    ax.add_patch(Circle((0, 0), R, color="#f3f5fa", ec=INK, lw=1.4))
    # grid of cells on visible hemisphere (orthographic)
    nlat, nlon = 12, 18
    for i in range(nlat):
        for j in range(nlon):
            la0, la1 = -np.pi / 2 + i * np.pi / nlat, -np.pi / 2 + (i + 1) * np.pi / nlat
            lo0, lo1 = -np.pi / 2 + j * np.pi / nlon, -np.pi / 2 + (j + 1) * np.pi / nlon
            pts = []
            for la, lo in [(la0, lo0), (la0, lo1), (la1, lo1), (la1, lo0)]:
                pts.append((R * np.cos(la) * np.sin(lo), R * np.sin(la)))
            bit = rng.random() > 0.5
            ax.add_patch(Polygon(pts, fc=(BLUE if bit else "white"), ec="#b8bfcd", lw=0.4, alpha=0.75 if bit else 1))
    ax.text(0, -1.28, "each patch ≈ one bit of information", ha="center", fontsize=8.6)
    ax.text(0, 1.12, "horizon surface", ha="center", fontsize=8.6, color=MUTED)
    ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.45, 1.3)
    save(fig, "bits")

# ---------------------------------------------------------------- information paradox flow
def fig_info():
    fig, ax = plt.subplots(figsize=(7.6, 2.5)); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 3.2)
    def box(x, w, title, sub, fc, tc=INK):
        ax.add_patch(FancyBboxPatch((x, 0.55), w, 2.1, boxstyle="round,pad=0.02,rounding_size=0.18", fc=fc, ec="none"))
        ax.text(x + w / 2, 2.25, title, ha="center", weight="bold", fontsize=10, color=tc)
        ax.text(x + w / 2, 0.65, sub, ha="center", fontsize=8.4, color=tc, va="bottom")
    box(0.0, 3.2, "1. A book falls in", "every word = detailed\nquantum information", "#e6edfb")
    box(4.4, 3.2, "2. Black hole", "described by just mass,\nspin and charge", INK, "white")
    box(8.8, 3.2, "3. Evaporates away", "only smooth,\nfeatureless heat", "#fdeee2")
    arrow(ax, (3.3, 1.6), (4.3, 1.6), lw=1.8); arrow(ax, (7.7, 1.6), (8.7, 1.6), lw=1.8)
    # book icon
    ax.add_patch(Polygon([[1.15, 1.35], [1.6, 1.25], [2.05, 1.35], [2.05, 1.95], [1.6, 1.85], [1.15, 1.95]], fc=BLUE, ec="white", lw=1))
    ax.plot([1.6, 1.6], [1.25, 1.85], color="white", lw=1)
    ax.add_patch(Circle((6.0, 1.6), 0.36, color="black", ec=ORANGE, lw=2))
    for k in range(9):
        a = k / 9 * 2 * np.pi
        ax.plot([10.4 + 0.2 * np.cos(a), 10.4 + 0.4 * np.cos(a)], [1.75 + 0.2 * np.sin(a), 1.75 + 0.4 * np.sin(a)], color=ORANGE, lw=1.6)
    ax.text(6.0, 2.95, "Where did the words go?", ha="center", fontsize=10.5, weight="bold", color=RED)
    save(fig, "info")

# ---------------------------------------------------------------- Page curve
def fig_page():
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    t = np.linspace(0, 1, 400)
    Sbh = (1 - t) ** (2 / 3)
    hawk = 1 - (1 - t) ** (2 / 3)
    hawk2 = hawk * 1.0
    page = np.minimum(hawk, Sbh)
    ax.plot(t, Sbh, color=MUTED, lw=1.6, ls="--", label="black hole's own entropy (shrinks as it evaporates)")
    ax.plot(t, hawk2, color=RED, lw=2.2, label="Hawking's 1975 answer: keeps rising → information lost")
    ax.plot(t, page, color=BLUE, lw=3.0, label="Page curve: rises then falls → information comes back out")
    tp = t[np.argmin(np.abs(hawk - Sbh))]
    ax.axvline(tp, color=INK, lw=0.8, ls=":")
    ax.text(tp + 0.01, 0.05, "Page time\n(about halfway)", fontsize=8.5)
    ax.set_xlabel("time  (from formation → complete evaporation)"); ax.set_ylabel("entanglement entropy\nof the radiation")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_ylim(0, 1.25); ax.set_xlim(0, 1)
    ax.legend(frameon=False, fontsize=8.4, loc="upper left")
    save(fig, "page")

# ---------------------------------------------------------------- what replaces the singularity
def fig_alternatives():
    fig, axs = plt.subplots(1, 4, figsize=(7.6, 2.2))
    titles = ["Classical GR", "Regular core", "Bounce", "Fuzzball"]
    subs = ["a point of\ninfinite density", "a tiny, dense but\nfinite centre", "collapse turns\naround (white hole?)", "no empty interior;\nstringy 'surface'"]
    for ax, ti, su in zip(axs, titles, subs):
        ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.3, 1.3); ax.set_ylim(-2.1, 1.35)
        ax.add_patch(Circle((0, 0), 1.0, fc="#eef1f7", ec=INK, lw=1.4))
        ax.text(0, 1.12, ti, ha="center", weight="bold", fontsize=9.5)
        ax.text(0, -1.2, su, ha="center", va="top", fontsize=8)
    axs[0].plot(0, 0, "o", color=RED, ms=5)
    for r, a in [(0.38, 0.25), (0.26, 0.5), (0.15, 1)]:
        axs[1].add_patch(Circle((0, 0), r, color=PURPLE, alpha=a, lw=0))
    arrow(axs[2], (-0.75, 0.55), (-0.12, 0.08), color=INK, lw=1.4, ms=9)
    arrow(axs[2], (0.12, 0.08), (0.75, 0.55), color=ORANGE, lw=1.4, ms=9)
    arrow(axs[2], (-0.75, -0.55), (-0.12, -0.08), color=INK, lw=1.4, ms=9)
    arrow(axs[2], (0.12, -0.08), (0.75, -0.55), color=ORANGE, lw=1.4, ms=9)
    rng = np.random.default_rng(2)
    th = np.linspace(0, 2 * np.pi, 300)
    rr = 0.95 + 0.06 * np.sin(th * 23) + 0.04 * np.sin(th * 37 + 1)
    axs[3].patches[0].set_facecolor("white")
    for k in range(5):
        r2 = rr * (1 - k * 0.12) + 0.03 * np.sin(th * (11 + k * 3))
        axs[3].plot(r2 * np.cos(th), r2 * np.sin(th), color=TEAL, lw=0.9, alpha=0.8)
    for ax in axs[1:]:
        ax.text(0, -1.98, "speculative", ha="center", fontsize=7.5, color=MUTED, style="italic")
    save(fig, "alternatives")

# ---------------------------------------------------------------- three windows
def fig_windows():
    fig = plt.figure(figsize=(7.6, 2.75))
    a1 = fig.add_axes([0.0, 0.08, 0.27, 0.8]); a2 = fig.add_axes([0.32, 0.18, 0.40, 0.7]); a3 = fig.add_axes([0.76, 0.08, 0.24, 0.8])
    # orbits
    a1.set_aspect("equal"); a1.axis("off")
    for (a, e, ang, col) in [(1.0, 0.88, 20, ORANGE), (0.8, 0.6, 100, BLUE), (1.2, 0.4, 230, TEAL)]:
        b = a * np.sqrt(1 - e ** 2); t = np.linspace(0, 2 * np.pi, 300)
        x = a * np.cos(t) - a * e; y = b * np.sin(t)
        A = np.radians(ang); X = x * np.cos(A) - y * np.sin(A); Y = x * np.sin(A) + y * np.cos(A)
        a1.plot(X, Y, color=col, lw=1.4)
        a1.plot(X[40], Y[40], "o", color=col, ms=4)
    a1.plot(0, 0, "*", color=INK, ms=11)
    a1.set_title("1. Stars orbiting Sgr A*", fontsize=9.5, loc="left")
    # chirp
    t = np.linspace(-1, 0.25, 3000)
    tc = 0.0
    tau = np.clip(tc - t, 1e-4, None)
    f = 6 * tau ** (-3 / 8); ph = np.cumsum(f) * (t[1] - t[0]) * 2 * np.pi * 2.2
    amp = tau ** (-1 / 4)
    h = np.where(t < tc, amp * np.cos(ph), amp[np.argmin(np.abs(t - tc + 1e-3))] * np.exp(-(t - tc) / 0.03) * np.cos(ph[np.argmin(np.abs(t - tc))] + (t - tc) * 2 * np.pi * 70))
    h = h / np.max(np.abs(h[t < -0.002]))
    a2.plot(t, np.clip(h, -1.4, 1.4), color=INK, lw=0.9)
    a2.axvspan(-1, -0.06, color=BLUE, alpha=0.06, lw=0); a2.axvspan(-0.06, 0.02, color=RED, alpha=0.08, lw=0); a2.axvspan(0.02, 0.25, color=TEAL, alpha=0.08, lw=0)
    a2.text(-0.6, -1.85, "inspiral", ha="center", fontsize=8.5, color=BLUE)
    a2.text(-0.07, -1.85, "merger", ha="center", fontsize=8.5, color=RED)
    a2.text(0.17, -1.85, "ringdown", ha="center", fontsize=8.5, color=TEAL)
    a2.set_ylim(-2.1, 1.6); a2.set_xlim(-1, 0.25); a2.axis("off")
    a2.set_title("2. Gravitational-wave \"chirp\"", fontsize=9.5, loc="left")
    # ring
    N = 300; y, x = np.mgrid[-1:1:N * 1j, -1:1:N * 1j]; r = np.hypot(x, y); ang = np.arctan2(y, x)
    I = np.exp(-((r - 0.48) / 0.11) ** 2) * (1 + 0.7 * np.sin(ang - 0.3) * -1)
    I = gaussian_filter(I, 6)
    a3.imshow(I, cmap="afmhot", origin="lower", extent=[-1, 1, -1, 1]); a3.axis("off")
    a3.set_title("3. Event Horizon Telescope", fontsize=9.5, loc="left")
    a3.text(0, -0.02, "shadow", color="#c9cdd8", ha="center", va="center", fontsize=8)
    save(fig, "windows")

if __name__ == "__main__":
    for f in [fig_cover, fig_two_theories, fig_grid, fig_fates, fig_anatomy, fig_lightcones, fig_redshift, fig_penrose,
              fig_tidal, fig_kerr, fig_penrose_process, fig_curvature, fig_scales, fig_hawking, fig_pair, fig_bits,
              fig_info, fig_page, fig_alternatives, fig_windows]:
        f(); print("ok", f.__name__)
