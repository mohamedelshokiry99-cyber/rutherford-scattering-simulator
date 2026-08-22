# Rutherford Scattering — Interactive RK4 Simulator

An interactive Python simulation of Rutherford (Coulomb) scattering.  
Fire alpha particles at a target nucleus, watch them deflect in real time, and verify the 1911 Rutherford formula numerically.

---

## Physics background

The simulator models an **alpha particle (Z₁ = 2)** fired at a stationary target nucleus under **pure Coulomb repulsion**. Nuclear forces and quantum effects are outside the scope of this model — the simulation terminates (and labels the event *Nuclear Contact*) the moment the particle reaches the nuclear surface.

### Dimensionless unit system

All integration is carried out in a natural unit system that removes physical constants from the equations of motion:

| Quantity | Unit |
|---|---|
| Length | *a* = k Z₁Z₂e² / (2Eₖ) — Rutherford scattering parameter |
| Speed  | *v₀* = √(2Eₖ/m) — initial projectile speed |
| Time   | *a* / *v₀* |

### Equations of motion

```
d²x/dt² = x / r³
d²y/dt² = y / r³        (Coulomb repulsion, dimensionless)
```

Conserved quantity: **E = ½|v|² + 1/r ≈ 0.5** (initial value when the particle is far from the nucleus).

### Key formulas

| Formula | Expression |
|---|---|
| Rutherford scattering angle | θ = 2 · arctan(a / b) |
| Distance of closest approach | solved from E and L conservation |
| Coulomb barrier | V_C = k Z₁Z₂e² / r_nucleus |
| Nuclear radius | r = R₀ · A^(1/3),  R₀ = 1.2 fm  (liquid-drop model) |

---

## Integration method

**4th-order Runge-Kutta (RK4)**, local truncation error O(dt⁵).

- Single trajectory (FIRE): dt = 0.05, up to 3 000 steps.
- Batch mode (SHOWER): dt = 0.05, up to 5 000 steps, fully **vectorized** — all N particles propagated in one NumPy array operation per step.
- Energy conservation is tracked live and reported as a percentage error after each shot.

---

## Project structure

```
rutherford-scattering/
├── main.py            # Entry point — dependency check, startup info, launches GUI
├── physics_engine.py  # Pure physics module (no GUI): RK4, Simulator class, analytical formulas
└── gui.py             # matplotlib GUI: 4-panel layout, sliders, buttons, animation loop
```

`physics_engine.py` is fully self-contained and can be imported independently of the GUI for scripting or testing.

---

## Requirements

| Package | Role |
|---|---|
| Python ≥ 3.8 | |
| numpy | Required — array math, vectorized RK4 |
| matplotlib | Required — GUI, animation, widgets |
| scipy | Optional — physical constants only; built-in fallback values are used if absent |

Install:

```bash
pip install numpy matplotlib
# optional
pip install scipy
```

---

## Running

```bash
python main.py
```

On startup, the terminal prints a sanity check for the default configuration (α on Au, Eₖ = 5.0 MeV):

```
  a  = <value> fm
  v₀ = <value> c
  Coulomb barrier (Au) = <value> MeV
  Nuclear radius  (Au) = <value> fm
```

Then the GUI window opens.

---

## GUI layout

The window is divided into four panels (GridSpec 4×2):

```
┌──────────────────────────┬──────────────────────────┐
│                          │  Energy conservation      │
│   Trajectory canvas      ├──────────────────────────┤
│                          │  θ vs b′ validation       │
├──────────────────────────┼──────────────────────────┤
│  Shot status             │  Controls                 │
├──────────────────────────┴──────────────────────────┤
│  Physics bar                                         │
└──────────────────────────────────────────────────────┘
```

### Panel descriptions

**Trajectory canvas**  
Animated α-particle path with a fading colour trail. Shows the target nucleus (glow layers), a detector ring at r = 14 a, a target-foil marker, the α source arrow, and a dashed asymptote preview that updates as you move the b′ slider.

**Energy conservation panel**  
Live plot of kinetic energy (KE = ½|v|²), potential energy (PE = 1/r), and total energy during a FIRE animation. Confirms RK4 accuracy in real time. Displays the numerical energy error (%) at each step.

**θ vs b′ validation panel**  
Overlays every completed (non-nuclear) trajectory as a dot on the analytical Rutherford curve θ = 2·arctan(a/b). Reports RMS angular error and maximum error across all accumulated shots.

**Physics bar**  
Single-line live summary: projectile, target nucleus, Eₖ, *a* (fm), Coulomb barrier (MeV), nuclear radius (units of *a*), and current regime flag.

---

## Controls

| Control | Range / Options | Description |
|---|---|---|
| b′ slider | −6 to +6 (units of *a*) | Impact parameter |
| Eₖ slider | 1 to 80 MeV | Projectile kinetic energy |
| Target nucleus slider | 0–8 (integer steps) | Select predefined nucleus |
| 🔥 FIRE | — | Compute and animate a single trajectory |
| 🌧 SHOWER | — | RK4 batch of 400 particles + 20 animated representative trajectories |
| 🗑 CLEAR | — | Remove all trajectories and reset all panels |
| ⏸ PAUSE / ▶ RESUME | — | Pause or resume a running animation |

Sliders are **disabled during animation** and re-enabled automatically when the animation completes or after CLEAR.

---

## Predefined target nuclei

| Index | Symbol | Z | A | Notes |
|---|---|---|---|---|
| 0 | He | 2 | 4 | α on α — very low barrier |
| 1 | C | 6 | 12 | |
| 2 | O | 8 | 16 | |
| 3 | Al | 13 | 27 | |
| 4 | Fe | 26 | 56 | |
| 5 | Cu | 29 | 63 | |
| 6 | Ag | 47 | 107 | |
| **7** | **Au** | **79** | **197** | **Default — Geiger-Marsden experiment** |
| 8 | Pb | 82 | 208 | |

---

## Scatter outcomes

| Label | Condition | Colour |
|---|---|---|
| ⚠ NUCLEAR CONTACT | Particle reaches nuclear surface (r < r_nuc) | Red |
| ↩ LARGE DEFLECTION | θ > 90° | Orange |
| ↗ RUTHERFORD SCATTER | 10° < θ ≤ 90° | Yellow |
| → SLIGHT DEFLECTION | θ ≤ 10° | Blue |

---

## SHOWER mode details

SHOWER sends **400 uniformly-spaced impact parameters** through the vectorized RK4 engine in a single batch, then animates **20 representative trajectories** (subsampled from the batch). The Shot Status panel reports:

- RMS angular error: RK4 numerical vs analytical Rutherford formula
- Energy conservation percentage across the batch
- Number of nuclear contacts in the full 400-particle batch
- Number of back-scattered (θ > 90°) and nuclear-hit particles among the 20 representatives

---

## Physics tip

Raise Eₖ above the Coulomb barrier of a light nucleus (e.g. He or C) to trigger Nuclear Contact. The simulator will halt and display a flash effect at the point of contact. The Coulomb-only model has no validity inside the nucleus; what happens next is outside its scope.

---

## Limitations

- **Coulomb model only.** Nuclear forces, strong interaction, quantum tunnelling, and nuclear reactions are not modelled.
- The target nucleus is treated as a **fixed point mass** (infinite-mass approximation). Recoil is not included.
- RK4 uses a **fixed step size**. For very small b′ values near head-on collision, or very high energies, energy conservation may degrade slightly — the energy panel makes this visible.
- The GUI backend is selected automatically in order: `TkAgg → Qt5Agg → Qt6Agg → WxAgg`. If none is available, matplotlib may fall back to a non-interactive backend and the animation will not work.

---

## Reference

Rutherford, E. (1911). *The scattering of α and β particles by matter and the structure of the atom.* Philosophical Magazine, Series 6, **21**(125), 669–688.

---

## License

MIT
