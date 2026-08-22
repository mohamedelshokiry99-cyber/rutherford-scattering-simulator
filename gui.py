"""
╔══════════════════════════════════════════════════════════════════════╗
║           RUTHERFORD SCATTERING — INTERACTIVE GUI  (v4 FINAL)      ║
║                                                                      ║
║  Layout (GridSpec 4×2):                                            ║
║                                                                      ║
║  ┌──────────────────────────┬──────────────────────────┐           ║
║  │                          │  Energy panel            │  rows 0-1  ║
║  │   TRAJECTORY             ├──────────────────────────┤           ║
║  │   (clean canvas)         │  θ vs b' validation      │           ║
║  ├──────────────────────────┼──────────────────────────┤           ║
║  │  SHOT STATUS             │  CONTROLS                │  row 2    ║
║  │  θ / r_min / E-error     │  Sliders + Buttons       │           ║
║  ├──────────────────────────┴──────────────────────────┤           ║
║  │  PHYSICS BAR  Z₁│Z₂│Eₖ│a│V_barrier│regime         │  row 3    ║
║  └──────────────────────────────────────────────────────┘           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import matplotlib
for _b in ['TkAgg', 'Qt5Agg', 'Qt6Agg', 'WxAgg']:
    try: matplotlib.use(_b); break
    except: pass

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Circle, FancyArrow
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgb
import warnings
warnings.filterwarnings('ignore')

from physics_engine import (
    Simulator, theta_from_b, r_min_dim,
    OUTCOME_LABELS, OUTCOME_COLORS, dimensionless_energy, NUCLEI
)

# ══════════════════════════════════════════════════════════════════════
#  STYLE CONSTANTS
# ══════════════════════════════════════════════════════════════════════
BG     = '#04040c'
FG     = '#b0c4de'
ACCENT = '#1a2a3a'
GOLD   = '#ffd700'
MAX_HIST = 30
TRAIL    = 85
SPEED    = 3
X0       = 22.0

plt.rcParams.update({
    'figure.facecolor': BG, 'axes.facecolor': BG,
    'text.color': FG, 'axes.labelcolor': FG,
    'xtick.color': '#445566', 'ytick.color': '#445566',
    'axes.edgecolor': ACCENT, 'grid.color': '#08090f', 'grid.alpha': 0.8,
})

# ══════════════════════════════════════════════════════════════════════
#  FIGURE & GRIDSPEC
# ══════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(19, 10.5), facecolor=BG)
try:
    fig.canvas.manager.set_window_title(
        'Rutherford Scattering — Interactive RK4 Simulator v4')
except Exception:
    pass

gs = GridSpec(
    4, 2,
    figure=fig,
    width_ratios=[2.0, 1.8],
    height_ratios=[2.3, 2.3, 1.55, 0.28],
    left=0.04, right=0.97,
    top=0.92, bottom=0.03,
    hspace=0.28, wspace=0.24
)

ax_traj   = fig.add_subplot(gs[0:2, 0])
ax_eng    = fig.add_subplot(gs[0,   1])
ax_val    = fig.add_subplot(gs[1,   1])
ax_status = fig.add_subplot(gs[2,   0])
ax_ctrl   = fig.add_subplot(gs[2,   1])
ax_phys   = fig.add_subplot(gs[3,   :])

# ══════════════════════════════════════════════════════════════════════
#  SINGLE GLOBAL TITLE ONLY
# ══════════════════════════════════════════════════════════════════════
fig.text(.5, .965, 'Rutherford Scattering — Interactive RK4 Simulator',
         ha='center', fontsize=13, fontweight='bold', color='#8899cc')

# ══════════════════════════════════════════════════════════════════════
#  TRAJECTORY PANEL
# ══════════════════════════════════════════════════════════════════════
XLIM, YLIM = 16.5, 12.5
ax_traj.set_facecolor(BG)
ax_traj.set_xlim(-XLIM, XLIM); ax_traj.set_ylim(-YLIM, YLIM)
ax_traj.set_aspect('equal')
ax_traj.set_xlabel("x  (units of  a)", fontsize=10, color='#5a6d89')
ax_traj.set_ylabel("y  (units of  a)", fontsize=10, color='#5a6d89')
ax_traj.set_title("α-particle trajectory", fontsize=10, color=FG, pad=8)
ax_traj.tick_params(colors='#1e2e40', labelsize=8)
ax_traj.grid(lw=0.4)
for sp in ax_traj.spines.values(): sp.set_edgecolor(ACCENT)

ax_traj.axvspan(-.10, .10, color='#251500', alpha=0.85, zorder=1)
ax_traj.text(.18, -YLIM+.4, 'target foil', color='#886622', fontsize=7, va='bottom')

ax_traj.add_patch(Circle((0,0), 14.0, fill=False,
    edgecolor='#182838', lw=1.2, ls='--', alpha=.7, zorder=2))
ax_traj.text(14*.68, 14*.73, 'detector', color='#1a3050', fontsize=7, rotation=46, ha='center')

for r_g,alp,col in [(7,.010,'#ffaa00'),(4.,.025,'#ffcc00'),
                     (2.2,.055,'#ffee44'),(1.,.16,'#fff8cc'),
                     (.44,.62,'#fffde5'),(.21,1.,'#ffffff')]:
    ax_traj.add_patch(Circle((0,0), r_g, color=col, alpha=alp, zorder=5))

pulse = Circle((0,0), 2.8, color=GOLD, alpha=0, fill=False, lw=2, zorder=6)
ax_traj.add_patch(pulse)

nuc_label = ax_traj.text(0, -.75, '', ha='center', va='top',
                          color=GOLD, fontsize=9, fontweight='bold', zorder=12)

nuc_barrier_circle = Circle((0,0), 1., fill=False, edgecolor='#cc2200',
                              lw=1., ls=':', alpha=0., zorder=6)
ax_traj.add_patch(nuc_barrier_circle)

ax_traj.annotate('', xy=(-XLIM+.2,0), xytext=(-XLIM+3,0),
    arrowprops=dict(arrowstyle='->', color='#3355aa', lw=2.2))
ax_traj.text(-XLIM+3.4, .7, 'α', color='#7788ee', fontsize=15, fontweight='bold')
ax_traj.text(-XLIM+3.3,-1.1,'source', color='#3355aa', fontsize=8)

b_arrow = FancyArrow(0,0,0,0, width=0.03, color='#446688', alpha=.5,
                      zorder=3, length_includes_head=True,
                      head_width=0.3, head_length=0.2)
ax_traj.add_patch(b_arrow)

preview_line, = ax_traj.plot([], [], '--', color='#446688', lw=1.2, alpha=.6, zorder=3)
preview_dot,  = ax_traj.plot([], [], 'o',  color='#446688', ms=5,   alpha=.5, zorder=4)

nuc_flash      = Circle((0,0), .3, color='#ff2200', alpha=0, fill=True,  zorder=11)
nuc_flash_ring = Circle((0,0), .3, color='#ff6600', alpha=0, fill=False, lw=2.5, zorder=12)
ax_traj.add_patch(nuc_flash); ax_traj.add_patch(nuc_flash_ring)
nuc_contact_dot, = ax_traj.plot([], [], 'x', color='#ff2200', ms=12, mew=2.5, zorder=13)

CMAP = LinearSegmentedColormap.from_list('r', ['#2299ff','#33ffcc','#ffcc00','#ff3300'])
anim_glow, = ax_traj.plot([], [], '.', ms=16, alpha=.18, zorder=8)
anim_core, = ax_traj.plot([], [], '.', ms=5,  alpha=.97, zorder=9)
anim_lc    = LineCollection([], lw=1.9, zorder=7)
ax_traj.add_collection(anim_lc)

for ypos, txt, cval in [
    (YLIM-.6, '← small b  (large θ, bounces back)', .04),
    (YLIM*0.35, '← b = a  →  θ = 90°',              .45),
    (.5,       '← large b  (small θ)',               .96),
]:
    ax_traj.text(XLIM-.3, ypos, txt, color=CMAP(cval),
                 fontsize=8.5, ha='right',
                 bbox=dict(fc=BG, ec='none', alpha=.85))

stat_text = ax_traj.text(.02, .015, '', transform=ax_traj.transAxes,
                          fontsize=7.5, va='bottom', color='#2a3f55',
                          family='monospace')

# ══════════════════════════════════════════════════════════════════════
#  ENERGY PANEL
# ══════════════════════════════════════════════════════════════════════
ax_eng.set_facecolor(BG)
ax_eng.set_title("Is  ½|v|² + 1/r  conserved?   (live RK4 state)",
                  fontsize=9, pad=5, color=FG)
ax_eng.set_xlabel("Step", fontsize=8); ax_eng.set_ylabel("E [dimensionless]", fontsize=8)
ax_eng.set_xlim(0,1); ax_eng.set_ylim(0., .65)
ax_eng.grid(lw=.4)
for sp in ax_eng.spines.values(): sp.set_edgecolor(ACCENT)

line_KE,    = ax_eng.plot([], [], '-', color='#ff6633', lw=1.4, label='KE = ½|v|²')
line_PE,    = ax_eng.plot([], [], '-', color='#33aaff', lw=1.4, label='PE = 1/r')
line_E_tot, = ax_eng.plot([], [], '-', color='#44ff88', lw=1.9, label='Total E (const)')
ax_eng.legend(fontsize=7.5, loc='upper right',
               facecolor='#08080f', edgecolor=ACCENT, framealpha=.95)
eng_text = ax_eng.text(.02, .06, '', transform=ax_eng.transAxes,
                        fontsize=8, color='#44ff88', family='monospace')

# ══════════════════════════════════════════════════════════════════════
#  VALIDATION PANEL
# ══════════════════════════════════════════════════════════════════════
ax_val.set_facecolor(BG)
ax_val.set_title("Does RK4 match  θ = 2·arctan(a/b)?   (Rutherford 1911)",
                  fontsize=9, pad=5, color=FG)
ax_val.set_xlabel("b' = b/a", fontsize=8); ax_val.set_ylabel("θ [°]", fontsize=8)
ax_val.set_xlim(0, 7); ax_val.set_ylim(-3, 185)
ax_val.grid(lw=.4)
for sp in ax_val.spines.values(): sp.set_edgecolor(ACCENT)

b_curve = np.linspace(.15, 7., 500)
ax_val.plot(b_curve, theta_from_b(b_curve), '-', color='#ff5555',
            lw=2., label='Analytical  θ=2·arctan(a/b)', zorder=4)
ax_val.axhline(90,  color='#fff', lw=.5, ls='--', alpha=.18)
ax_val.axvline(1.0, color='#fff', lw=.5, ls='--', alpha=.18)
ax_val.text(1.06, 94, "b=a → θ=90°", color='#7788aa', fontsize=7.5)
ax_val.legend(fontsize=7.5, loc='upper right',
               facecolor='#08080f', edgecolor=ACCENT, framealpha=.95)

val_dot,   = ax_val.plot([], [], 'o', ms=9, zorder=6)
val_vline  = ax_val.axvline(x=1, color='#446688', lw=.8, ls=':', alpha=0.)
val_hline  = ax_val.axhline(y=0, color='#446688', lw=.8, ls=':', alpha=0.)
val_scatter, = ax_val.plot([], [], 'o', ms=4, color='#4488ff', alpha=.45, zorder=5)
val_scatter_x, val_scatter_y = [], []

val_rms_text = ax_val.text(.03, .08, 'Fire a particle to validate →',
                            transform=ax_val.transAxes, fontsize=7.5,
                            color='#77ff99', family='monospace',
                            bbox=dict(boxstyle='round,pad=.3',
                                      fc='#04080a', ec='#1a3a22', lw=1))

# ══════════════════════════════════════════════════════════════════════
#  SHOT STATUS PANEL
# ══════════════════════════════════════════════════════════════════════
ax_status.set_facecolor('#040810')
ax_status.set_xticks([]); ax_status.set_yticks([])
for sp in ax_status.spines.values(): sp.set_edgecolor('#1a2a3a')
ax_status.text(.02, .97, 'SHOT STATUS', transform=ax_status.transAxes,
               fontsize=8, color='#2a4060', fontweight='bold', va='top')

status_outcome = ax_status.text(.02, .82, 'Fire a particle to see results →',
                                 transform=ax_status.transAxes,
                                 fontsize=10.5, fontweight='bold', va='top',
                                 linespacing=1.5, color='#445566')

status_details = ax_status.text(.02, .42, '',
                                 transform=ax_status.transAxes,
                                 fontsize=8.5, va='top', family='monospace',
                                 color='#7a9bbc', linespacing=1.7)

# ══════════════════════════════════════════════════════════════════════
#  PHYSICS BAR
# ══════════════════════════════════════════════════════════════════════
ax_phys.set_facecolor('#030308'); ax_phys.axis('off')
for sp in ax_phys.spines.values(): sp.set_edgecolor('#0e1520')
phys_bar = ax_phys.text(.5, .5, '', transform=ax_phys.transAxes,
                         ha='center', va='center', fontsize=9,
                         color='#4a5a78', family='monospace')

# ══════════════════════════════════════════════════════════════════════
#  CONTROL WIDGETS
# ══════════════════════════════════════════════════════════════════════
ax_ctrl.set_visible(False)
cp = ax_ctrl.get_position()
CL, CB, CW, CH = cp.x0, cp.y0, cp.width, cp.height

PAD = 0.006
SH  = CH * 0.165
BH  = CH * 0.22

def _sl_ax(row):
    return fig.add_axes([CL+PAD, CB+CH-(row+1)*(SH+PAD)-PAD, CW-2*PAD, SH])

def _btn_ax(col, n=4):
    bw = (CW - (n+1)*PAD) / n
    return fig.add_axes([CL+PAD+col*(bw+PAD), CB+PAD, bw, BH])

sl_b = Slider(_sl_ax(0), "b'  (impact param)", -6., 6.,  valinit=1.5,  color='#2244aa')
sl_E = Slider(_sl_ax(1), "Eₖ  [MeV]",          1., 80., valinit=5.0,  color='#aa4422')
sl_target = Slider(_sl_ax(2), "Target nucleus", 0, len(NUCLEI)-1, valinit=7,
                    valstep=1, color='#226644')
sl_target.valtext.set_text(NUCLEI[7][0])

btn_fire   = Button(_btn_ax(0), '🔥 FIRE',   color='#1a0a00', hovercolor='#331100')
btn_shower = Button(_btn_ax(1), '🌧 SHOWER', color='#001a0a', hovercolor='#003311')
btn_clear  = Button(_btn_ax(2), '🗑 CLEAR',  color='#0a001a', hovercolor='#220033')
btn_pause  = Button(_btn_ax(3), '⏸ PAUSE',  color='#001a1a', hovercolor='#003333')
for btn in [btn_fire, btn_shower, btn_clear, btn_pause]:
    btn.label.set_color(FG); btn.label.set_fontsize(10)

ax_ctrl_lbl = fig.add_axes([CL, CB+CH-PAD, CW, PAD*3])
ax_ctrl_lbl.axis('off')
ax_ctrl_lbl.text(.5, .5, 'CONTROLS', ha='center', va='center',
                  fontsize=8, color='#2a4060', fontweight='bold')

# ══════════════════════════════════════════════════════════════════════
#  SIMULATOR
# ══════════════════════════════════════════════════════════════════════
_sym0, _Z0, _A0 = NUCLEI[7]
sim = Simulator(Z1=2, Z2=_Z0, E_MeV=5.0, A_target=_A0)

state = {
    'mode':         'idle',
    'traj_result':  None,
    'anim_frame':   0,
    'history':      [],
    'energy_steps': [],
    'flash_active': False,
    'flash_frame':  0,
    'flash_pos':    (0., 0.),
    'shower_mode':  False,
}

hist_lines = []


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════
def _controls_active(active):
    """Enable/disable sliders. active=True → enabled."""
    try:
        sl_b.active = active
        sl_E.active = active
        sl_target.active = active
    except Exception:
        pass


def _get_target_symbol():
    sym = next((n[0] for n in NUCLEI if n[1]==sim.Z2 and n[2]==sim.A_target), f'Z{sim.Z2}')
    return sym


def update_nucleus_label():
    sym = _get_target_symbol()
    nuc_label.set_text(f'{sym}\nZ={sim.Z2}\na={sim.a_fm:.1f}fm')


def update_phys_bar():
    regime = ('⚠ Nuclear penetration possible!' if sim.E_MeV >= sim.V_barrier
               else '✓ Rutherford regime (Coulomb-only valid)')
    sym = _get_target_symbol()
    phys_bar.set_text(
        f"Projectile: α (Z₁=2)  │  Target: {sym} (Z₂={sim.Z2}, A={sim.A_target})  │  "
        f"Eₖ={sim.E_MeV:.1f} MeV  │  a={sim.a_fm:.2f} fm  │  "
        f"V_Coulomb={sim.V_barrier:.1f} MeV  │  r_nuc={sim.r_nuc_dim:.4f} a  │  {regime}")
    fig.canvas.draw_idle()


def update_status(outcome_str, details_str, color='#445566'):
    status_outcome.set_text(outcome_str); status_outcome.set_color(color)
    status_details.set_text(details_str)


def update_validation_panel():
    valid_res = [r for r in state['history'] if not r.get('nuclear_hit', False)]
    b_abs = [abs(r['b_prime']) for r in valid_res]
    t_num = [r['theta']        for r in valid_res]
    t_ana = [float(theta_from_b(b)) for b in b_abs]
    val_scatter.set_xdata(b_abs); val_scatter.set_ydata(t_num)
    val_scatter_x.clear(); val_scatter_x.extend(b_abs)
    val_scatter_y.clear(); val_scatter_y.extend(t_num)
    n_nuc = sum(1 for r in state['history'] if r.get('nuclear_hit', False))
    if t_num:
        errs = [abs(n-a) for n,a in zip(t_num,t_ana)]
        rms  = float(np.sqrt(np.mean(np.array(errs)**2)))
        note = f'  ({n_nuc} nuclear excl.)' if n_nuc else ''
        val_rms_text.set_text(
            f"N={len(t_num)} Coulomb-valid{note}  "
            f"RMS={rms:.5f}°  max={max(errs):.5f}°")
    else:
        val_rms_text.set_text('No Coulomb-valid trajectories yet')


def redraw_history():
    for ln in hist_lines:
        try: ln.remove()
        except Exception: pass
    hist_lines.clear()
    for res in state['history']:
        t = res['traj']
        col = res['color']
        ln,  = ax_traj.plot(t[:,0], t[:,1], '-', color=col, lw=1.2, alpha=.55, zorder=4)
        ep,  = ax_traj.plot([t[-1,0]], [t[-1,1]], 'o', color=col, ms=4, alpha=.7, zorder=5)
        hist_lines.extend([ln, ep])
    fig.canvas.draw_idle()


def make_fading_lc(x, y, rgb):
    if len(x) < 2: return [], []
    pts  = np.array([x,y]).T.reshape(-1,1,2)
    segs = np.concatenate([pts[:-1],pts[1:]],axis=1)
    n    = len(segs)
    als  = np.linspace(.02, .95, n)
    return segs, np.array([(*rgb,a) for a in als])


def setup_energy_panel():
    global line_KE, line_PE, line_E_tot, eng_text
    ax_eng.cla(); ax_eng.set_facecolor(BG)
    ax_eng.set_title("Is  ½|v|² + 1/r  conserved?   (live RK4 state)",
                      fontsize=9, pad=5, color=FG)
    ax_eng.set_xlabel("Step", fontsize=8)
    ax_eng.set_ylabel("E [dimensionless]", fontsize=8)
    ax_eng.set_xlim(0,1); ax_eng.set_ylim(0., .65)
    ax_eng.grid(lw=.4)
    for sp in ax_eng.spines.values(): sp.set_edgecolor(ACCENT)
    line_KE,    = ax_eng.plot([],[],'-',color='#ff6633',lw=1.4,label='KE = ½|v|²')
    line_PE,    = ax_eng.plot([],[],'-',color='#33aaff',lw=1.4,label='PE = 1/r')
    line_E_tot, = ax_eng.plot([],[],'-',color='#44ff88',lw=1.9,label='Total E (const)')
    ax_eng.legend(fontsize=7.5, loc='upper right',
                   facecolor='#08080f', edgecolor=ACCENT, framealpha=.95)
    eng_text = ax_eng.text(.02,.06,'',transform=ax_eng.transAxes,
                            fontsize=8,color='#44ff88',family='monospace')


# ══════════════════════════════════════════════════════════════════════
#  ANALYTICAL PREVIEW
# ══════════════════════════════════════════════════════════════════════
def draw_asymptotes(b_prime):
    b_abs   = max(abs(b_prime), 1e-6)
    th_deg  = float(theta_from_b(b_abs))
    th_rad  = np.radians(th_deg)
    sign    = 1. if b_prime >= 0 else -1.
    cos_th  = np.cos(th_rad)
    sin_th  = np.sin(th_rad) * sign

    t_int = b_prime / sin_th if abs(sin_th) > 1e-6 else XLIM
    x_int = np.clip(t_int * cos_th, -XLIM, XLIM)
    y_int = b_prime

    ext = XLIM * 2.5
    x_draw = np.concatenate([[-X0, x_int], [np.nan], [x_int, x_int+ext*cos_th]])
    y_draw = np.concatenate([[b_prime, y_int], [np.nan], [y_int, y_int+ext*sin_th]])
    preview_line.set_data(x_draw, y_draw)
    preview_dot.set_data([x_int], [y_int])

    val_dot.set_data([b_abs], [th_deg])
    oc = ('large_scatter' if th_deg>90 else ('scatter' if th_deg>10 else 'slight'))
    val_dot.set_color(OUTCOME_COLORS[oc])
    val_vline.set_xdata([b_abs,b_abs]); val_vline.set_alpha(.45)
    val_hline.set_ydata([th_deg,th_deg]); val_hline.set_alpha(.45)

    b_arrow.set_data(x=-XLIM+.5, y=0, dx=0, dy=b_prime)
    nuc_barrier_circle.set_radius(max(sim.r_nuc_dim, .01))
    nuc_barrier_circle.set_alpha(.65 if sim.E_MeV >= sim.V_barrier else .22)

    rmin = float(r_min_dim(b_abs))
    update_status(
        f"[Analytical preview]\n"
        f"b' = {b_prime:+.2f}   θ ≈ {th_deg:.1f}°\n"
        f"{OUTCOME_LABELS[oc]}",
        f"b'     = {b_prime:+.4f} a\n"
        f"θ(ana) = {th_deg:.4f}°\n"
        f"r_min  = {rmin:.4f} a = {rmin*sim.a_fm:.3f} fm\n"
        f"[RK4 preview ~200 ms after release]\n"
        f"Shots  = {len(state['history'])}",
        color=OUTCOME_COLORS[oc]
    )
    update_phys_bar()
    fig.canvas.draw_idle()


def run_rk4_preview():
    if state['mode'] in ('animating', 'paused'): return
    b   = sl_b.val
    res = sim.trajectory_fast(b, X0=X0, dt=0.18, max_steps=400)
    t   = res['traj']
    preview_line.set_data(t[:,0], t[:,1])
    preview_dot.set_data([t[0,0]], [t[0,1]])
    th_n = res['theta']
    th_a = float(theta_from_b(abs(b)))
    update_status(
        f"[RK4 preview]\nOutcome: {OUTCOME_LABELS[res['outcome']]}",
        f"b'       = {b:+.4f} a\n"
        f"θ_RK4    = {th_n:.5f}°\n"
        f"θ_ana    = {th_a:.5f}°\n"
        f"r_min    = {res['r_min']:.4f} a = {res['r_min']*sim.a_fm:.3f} fm\n"
        f"E error  = {res.get('E_err', 100-res['E_cons']):.5f}%\n"
        f"E-cons   = {res['E_cons']:.5f}%\n"
        f"Shots    = {len(state['history'])}",
        color=res['color']
    )
    fig.canvas.draw_idle()


_preview_timer = fig.canvas.new_timer(interval=200)
_preview_timer.single_shot = True
_preview_timer.add_callback(run_rk4_preview)


# ══════════════════════════════════════════════════════════════════════
#  SLIDER CALLBACKS  —  GUARDED AGAINST ACTIVE ANIMATION
# ══════════════════════════════════════════════════════════════════════
def on_b_change(val):
    # BLOCK during any active simulation (animating or paused)
    if state['mode'] in ('animating', 'paused'):
        return
    draw_asymptotes(val)
    _preview_timer.stop(); _preview_timer.start()


def on_E_change(val):
    # CRITICAL: block BEFORE mutating simulator state
    if state['mode'] in ('animating', 'paused'):
        return
    sim.update_params(E_MeV=sl_E.val)
    update_nucleus_label()
    draw_asymptotes(sl_b.val)
    _preview_timer.stop(); _preview_timer.start()


def on_target_change(val):
    # CRITICAL: block BEFORE mutating simulator state
    if state['mode'] in ('animating', 'paused'):
        return
    idx = int(round(sl_target.val))
    sym, Z2, A = NUCLEI[idx]
    sl_target.valtext.set_text(sym)
    # SINGLE SOURCE OF TRUTH
    sim.A_target = A
    sim.update_params(Z2=Z2)
    update_nucleus_label()
    draw_asymptotes(sl_b.val)
    _preview_timer.stop(); _preview_timer.start()


sl_b.on_changed(on_b_change)
sl_E.on_changed(on_E_change)
sl_target.on_changed(on_target_change)


# ══════════════════════════════════════════════════════════════════════
#  BUTTON CALLBACKS
# ══════════════════════════════════════════════════════════════════════
def on_fire(event):
    if state['mode'] in ('animating', 'paused'):
        return
    b   = sl_b.val
    res = sim.trajectory(b, X0=X0, dt=.05)
    state['traj_result']  = res
    state['anim_frame']   = 0
    state['mode']         = 'animating'
    state['energy_steps'] = []
    _controls_active(False)   # DISABLE sliders during active simulation
    if state.get('shower_mode', False):
        setup_energy_panel(); state['shower_mode'] = False
    col = to_rgb(res['color'])
    anim_glow.set_color(res['color']); anim_core.set_color(res['color'])
    ax_eng.set_xlim(0, len(res['traj'])); ax_eng.set_ylim(0., .65)
    preview_line.set_data([],[]); preview_dot.set_data([],[])
    nuc_contact_dot.set_data([], [])
    nuc_flash.set_alpha(0); nuc_flash_ring.set_alpha(0)
    state['flash_active'] = False


def on_shower(event):
    if state['mode'] in ('animating', 'paused'):
        return
    b_traj = np.concatenate([np.linspace(.30,5.,10),-np.linspace(.30,5.,10)])
    for b in b_traj:
        res = sim.trajectory(b, X0=X0, dt=.08)
        if len(state['history']) >= MAX_HIST: state['history'].pop(0)
        state['history'].append(res)
    redraw_history()

    N_B = 400
    b_batch = np.random.uniform(.2, 6., N_B)
    print(f"  Batch N={N_B}...", end='', flush=True)
    batch = sim.batch(b_batch, X0=X0, dt=.07, max_steps=5000)
    print(" done.")
    th_num, th_ana = batch['theta_num'], batch['theta_ana']
    rms   = batch['rms_error']; e_err = batch['energy_error']
    n_nuc = batch.get('nuclear_hits', 0)
    n_val = batch.get('n_valid', N_B)

    ax_eng.cla(); ax_eng.set_facecolor(BG)
    ax_eng.tick_params(colors='#445566', labelsize=8)
    for sp in ax_eng.spines.values(): sp.set_edgecolor(ACCENT)
    bins = np.linspace(0,180,37); centers = .5*(bins[:-1]+bins[1:])
    vm   = ~batch.get('nuclear_mask', np.zeros(N_B, bool))
    cnt_n,_ = np.histogram(th_num[vm], bins=bins)
    cnt_a,_ = np.histogram(th_ana[vm], bins=bins)
    ax_eng.bar(centers, cnt_n, width=4.8, color='#4488ff', alpha=.78,
               label=f'RK4  (N={N_B})', zorder=3)
    ax_eng.step(centers, cnt_a, where='mid', color='#ff5555', lw=2.,
                label='Analytical θ(b)', zorder=4)
    ax_eng.fill_between(centers, cnt_a, step='mid', color='#ff5555', alpha=.15)
    ax_eng.set_title(f'Shower — Angle Distribution  (N={N_B})',
                      fontsize=9, pad=5, color=FG)
    ax_eng.set_xlabel("θ [°]", fontsize=8, color='#5a6d89')
    ax_eng.set_ylabel("Counts", fontsize=8, color='#5a6d89')
    ax_eng.set_xlim(0,180); ax_eng.grid(lw=.4)
    ax_eng.legend(fontsize=7.5, facecolor='#08080f', edgecolor=ACCENT, framealpha=.95)
    ax_eng.text(.97,.97,
                f'N valid      : {n_val}\n'
                f'Nuclear hits : {n_nuc}\n'
                f'RMS error    : {rms:.5f}°\n'
                f'Energy error : {e_err:.5f}%\n'
                f'E-conserv    : {100-e_err:.5f}%',
                transform=ax_eng.transAxes, ha='right', va='top',
                fontsize=8, family='monospace', color='#77ff99',
                bbox=dict(boxstyle='round', fc='#040e04', ec='#1a3a1a', lw=1))
    state['shower_mode'] = True

    reps = state['history'][-20:]
    outs = [r['outcome'] for r in reps]
    n_back = outs.count('large_scatter')
    n_hit_rep  = outs.count('nuclear_hit')
    update_status(
        f"SHOWER  N={N_B}  (RK4 batch)",
        f"RMS error              = {rms:.5f}°\n"
        f"E-conservation         = {100-e_err:.5f}%\n"
        f"Batch nuclear hits     = {n_nuc}/{N_B}\n"
        f"Representative hits    = {n_hit_rep}/20\n"
        f"Back-scatter (repres.) = {n_back}/20\n"
        f"[Press FIRE to restore energy panel]",
        color='#aabbcc'
    )
    update_validation_panel()
    fig.canvas.draw_idle()


def on_clear(event):
    state['history'].clear(); state['mode'] = 'idle'
    _controls_active(True)    # RE-ENABLE sliders
    val_scatter_x.clear(); val_scatter_y.clear()
    val_scatter.set_xdata([]); val_scatter.set_ydata([])
    redraw_history()
    anim_lc.set_segments([]); anim_glow.set_data([],[]); anim_core.set_data([],[])
    line_KE.set_data([],[]); line_PE.set_data([],[]); line_E_tot.set_data([],[])
    nuc_flash.set_alpha(0); nuc_flash_ring.set_alpha(0)
    nuc_contact_dot.set_data([],[])
    state['flash_active'] = False
    if state.get('shower_mode', False):
        setup_energy_panel(); state['shower_mode'] = False
    update_status('Fire a particle to see results →', '', color='#445566')
    draw_asymptotes(sl_b.val)
    _preview_timer.stop(); _preview_timer.start()


def on_pause(event):
    if   state['mode'] == 'animating':
        state['mode']='paused'
        btn_pause.label.set_text('▶ RESUME')
    elif state['mode'] == 'paused':
        state['mode']='animating'
        btn_pause.label.set_text('⏸ PAUSE')
    fig.canvas.draw_idle()

btn_fire.on_clicked(on_fire);   btn_shower.on_clicked(on_shower)
btn_clear.on_clicked(on_clear); btn_pause.on_clicked(on_pause)


# ══════════════════════════════════════════════════════════════════════
#  ANIMATION
# ══════════════════════════════════════════════════════════════════════
def animate(_frame):
    artists = [anim_lc, anim_glow, anim_core, pulse,
               nuc_flash, nuc_flash_ring, nuc_contact_dot,
               line_KE, line_PE, line_E_tot,
               status_outcome, status_details, stat_text, eng_text]

    t_ = _frame * .08
    pulse.set_radius(2.5 + .6*abs(np.sin(t_)))
    pulse.set_alpha(.42*np.sin(t_)**2)

    if state['flash_active']:
        el = _frame - state['flash_frame']
        fx,fy = state['flash_pos']
        nuc_flash.set_center((fx,fy)); nuc_flash.set_radius(.25+el*.16); nuc_flash.set_alpha(max(0,.7-el*.04))
        nuc_flash_ring.set_center((fx,fy)); nuc_flash_ring.set_radius(.25+el*.22); nuc_flash_ring.set_alpha(max(0,.8-el*.04))
        if .8 - el*.04 <= 0:
            state['flash_active'] = False
            nuc_flash.set_alpha(0); nuc_flash_ring.set_alpha(0)
    else:
        nuc_flash.set_alpha(0); nuc_flash_ring.set_alpha(0)

    if state['mode'] != 'animating':
        return artists

    res   = state['traj_result']
    traj  = res['traj']
    idx   = min(state['anim_frame']*SPEED, len(traj)-1)
    state['anim_frame'] += 1
    col   = res['color']; rgb = to_rgb(col)

    px,py = traj[idx,0], traj[idx,1]
    anim_glow.set_data([px],[py]); anim_core.set_data([px],[py])

    s0 = max(0, idx-TRAIL)
    segs,colors = make_fading_lc(traj[s0:idx+1,0], traj[s0:idx+1,1], rgb)
    if len(segs): anim_lc.set_segments(segs); anim_lc.set_color(colors)
    else:         anim_lc.set_segments([])

    r_now = np.hypot(px,py)
    vx_now,vy_now = traj[idx,2], traj[idx,3]
    KE = .5*(vx_now**2+vy_now**2); PE = 1./max(r_now,1e-4); ET = KE+PE
    state['energy_steps'].append((idx,KE,PE,ET))
    if len(state['energy_steps']) > 2:
        sa  = np.array(state['energy_steps'])
        line_KE.set_data(sa[:,0],sa[:,1])
        line_PE.set_data(sa[:,0],sa[:,2])
        line_E_tot.set_data(sa[:,0],sa[:,3])
        E0_ = res['E0']
        E_err = abs(ET-E0_)/abs(E0_)*100
        eng_text.set_text(
            f"E₀             = {E0_:.6f}\n"
            f"E_now          = {ET:.6f}\n"
            f"Energy error   = {E_err:.5f}%\n"
            f"E-conservation = {100-E_err:.5f}%")

    theta_ = res['theta'] if idx >= len(traj)-SPEED-5 else '…'
    th_str = f"{theta_:.3f}°" if isinstance(theta_, float) else theta_
    r_fm   = r_now * sim.a_fm
    e_err_r  = res.get('E_err', 100-res['E_cons'])
    e_cons_r = res['E_cons']
    update_status(
        f"b' = {res['b_prime']:+.3f}   θ = {th_str}\n"
        f"{OUTCOME_LABELS[res['outcome']]}",
        f"r now    = {r_now:.4f} a = {r_fm:.3f} fm\n"
        f"b'       = {res['b_prime']:+.4f} a\n"
        f"θ_RK4    = {th_str}\n"
        f"r_min    = {res['r_min']:.4f} a = {res['r_min']*sim.a_fm:.3f} fm\n"
        f"E error  = {e_err_r:.5f}%\n"
        f"E-cons   = {e_cons_r:.5f}%",
        color=col
    )

    stat_text.set_text(f"step {idx}/{len(traj)}  |  mode={state['mode']}")

    if idx >= len(traj)-1:
        state['mode'] = 'idle'
        _controls_active(True)   # RE-ENABLE sliders when animation completes
        if len(state['history']) >= MAX_HIST: state['history'].pop(0)
        state['history'].append(res)
        update_validation_panel(); redraw_history()
        b_abs = abs(res['b_prime'])

        if res['nuclear_hit']:
            val_dot.set_data([], [])
            val_vline.set_alpha(0); val_hline.set_alpha(0)
            state['flash_active']=True; state['flash_frame']=_frame
            state['flash_pos']=(px,py)
            nuc_contact_dot.set_data([px],[py])
            update_status(
                "⚠  NUCLEAR CONTACT\n"
                "Coulomb-only model terminated at nuclear surface",
                f"b'             = {res['b_prime']:+.4f} a\n"
                f"r_min          = {res['r_min']:.4f} a = {res['r_min']*sim.a_fm:.3f} fm\n"
                f"r_nucleus      = {sim.r_nuc_dim:.4f} a\n"
                f"Eₖ = {sim.E_MeV:.1f} MeV  >  V_C = {sim.V_barrier:.1f} MeV\n"
                f"θ Rutherford    = N/A  (nuclear contact)\n"
                f"Δθ              = N/A  (nuclear contact)\n"
                f"Energy error   = {e_err_r:.5f}%\n"
                f"E-conservation = {e_cons_r:.5f}%",
                color='#ff3300'
            )
        else:
            nuc_contact_dot.set_data([],[])
            val_dot.set_data([b_abs],[res['theta']]); val_dot.set_color(col)
            val_vline.set_xdata([b_abs,b_abs]); val_vline.set_alpha(.45)
            val_hline.set_ydata([res['theta'],res['theta']]); val_hline.set_alpha(.45)
            th_a  = float(theta_from_b(b_abs))
            delta = abs(res['theta'] - th_a)
            update_status(
                f"Outcome: {OUTCOME_LABELS[res['outcome']]}",
                f"b'             = {res['b_prime']:+.4f} a\n"
                f"θ numerical     = {res['theta']:.5f}°\n"
                f"θ Rutherford    = {th_a:.5f}°\n"
                f"Δθ              = {delta:.5f}°\n"
                f"r_min          = {res['r_min']:.4f} a = {res['r_min']*sim.a_fm:.3f} fm\n"
                f"Energy error   = {e_err_r:.5f}%\n"
                f"E-conservation = {e_cons_r:.5f}%",
                color=col
            )

    return artists


ani = animation.FuncAnimation(
    fig, animate, interval=28, blit=True,
    cache_frame_data=False)


def run():
    update_nucleus_label()
    update_phys_bar()
    draw_asymptotes(sl_b.val)
    _preview_timer.start()
    plt.show()
