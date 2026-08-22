"""
╔══════════════════════════════════════════════════════════════════════╗
║              RUTHERFORD SCATTERING — PHYSICS ENGINE                ║
║                                                                      ║
║  Pure physics module. No GUI, no matplotlib.                        ║
║  All quantities in DIMENSIONLESS UNITS unless stated otherwise.     ║
║                                                                      ║
║  Dimensionless system:                                              ║
║    Length  → units of  a = k·Z₁·Z₂·e² / (2·Eₖ)                   ║
║    Speed   → units of  v₀ = √(2Eₖ/m)                              ║
║    Time    → units of  a/v₀                                        ║
║                                                                      ║
║  Equations of motion:                                               ║
║    d²x/dt² = +x/r³   (Coulomb repulsion)                           ║
║    d²y/dt² = +y/r³                                                  ║
║                                                                      ║
║  Conserved energy (dimensionless):                                  ║
║    E = ½|v|² + 1/r  ≈  0.5  (initial, when particle is far away)  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import numpy as np

# ══════════════════════════════════════════════════════════════════════
#  PHYSICAL CONSTANTS
# ══════════════════════════════════════════════════════════════════════
try:
    from scipy.constants import elementary_charge, epsilon_0
    from math import pi
    K_E = 1.0 / (4.0 * pi * epsilon_0)   # Coulomb constant [N·m²/C²]
    q_e = elementary_charge               # [C]
except ImportError:
    K_E = 8.9875517923e9
    q_e = 1.602176634e-19

M_ALPHA = 6.6447e-27    # Alpha-particle mass [kg]
MEV     = 1.602e-13     # 1 MeV in Joules
R0_NUC  = 1.2e-15       # Nuclear radius constant [m]:  r = R0·A^(1/3)


# ══════════════════════════════════════════════════════════════════════
#  PHYSICAL QUANTITIES  (all return SI unless name ends in _dim/_MeV)
# ══════════════════════════════════════════════════════════════════════
def rutherford_a(Z1, Z2, E_MeV):
    """
    Rutherford scattering parameter [m].
    a = k·Z₁·Z₂·e² / (2·Eₖ)
    Physical meaning: half the distance of closest approach in a
    head-on collision (b=0).
    """
    return K_E * Z1 * Z2 * q_e**2 / (2.0 * E_MeV * MEV)


def initial_speed(E_MeV):
    """Initial speed of alpha particle [m/s]: v₀ = √(2Eₖ/m)"""
    return np.sqrt(2.0 * E_MeV * MEV / M_ALPHA)


def nuclear_radius_m(A):
    """
    Nuclear radius [m] using liquid-drop model: r = R₀·A^(1/3)
    A: mass number of target nucleus
    """
    return R0_NUC * (A ** (1.0/3.0))


def coulomb_barrier_MeV(Z1, Z2, A_target):
    """
    Classical Coulomb barrier energy [MeV].
    V_barrier = k·Z₁·Z₂·e² / r_nucleus

    If E_k < V_barrier: particle CANNOT reach the nucleus classically.
    Rutherford formula is valid here (pure Coulomb scattering).

    If E_k > V_barrier: particle CAN penetrate to nuclear surface.
    Nuclear reactions become possible.
    """
    r_n = nuclear_radius_m(A_target)
    return K_E * Z1 * Z2 * q_e**2 / r_n / MEV


def nuclear_radius_dim(Z1, Z2, E_MeV, A_target):
    """
    Nuclear radius in dimensionless units (units of Rutherford 'a').
    r_nuc_dim = r_nuc / a
    """
    return nuclear_radius_m(A_target) / rutherford_a(Z1, Z2, E_MeV)


def min_b_for_safe_scatter(Z1, Z2, E_MeV, A_target):
    """
    Minimum impact parameter b' (in units of a) for the particle
    to NOT reach the nuclear surface.

    Derived from conservation of E and L:
      ½(b'/r_nuc)² + 1/r_nuc = ½
      → b'_min = √[r_nuc·(r_nuc − 2)]

    Returns 0 if E_k > V_barrier (all b values can lead to collision).
    """
    r_n = nuclear_radius_dim(Z1, Z2, E_MeV, A_target)
    val = r_n * (r_n - 2.0)
    return np.sqrt(val) if val > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════
#  ANALYTICAL RUTHERFORD FORMULAS
# ══════════════════════════════════════════════════════════════════════
def theta_from_b(b_prime):
    """
    Scattering angle from impact parameter [degrees].
    Rutherford formula: cot(θ/2) = b/a  →  θ = 2·arctan(a/b)
    """
    b = np.maximum(np.abs(np.asarray(b_prime, float)), 1e-9)
    return np.degrees(2.0 * np.arctan(1.0 / b))


def b_from_theta(theta_deg):
    """Inverse Rutherford: b' = cot(θ/2)"""
    t = np.radians(np.asarray(theta_deg, float))
    return 1.0 / np.tan(t / 2.0)


def r_min_dim(b_prime):
    """
    Distance of closest approach [units of a].
    Solved from energy + angular momentum conservation.
    Head-on (b=0): r_min = 2.
    """
    b = np.asarray(b_prime, float)
    # Quadratic: b'²·u² + 2·u − 1 = 0, u = 1/r_min
    discriminant = 1.0 + np.asarray(b)**2
    u = (-1.0 + np.sqrt(discriminant)) / (np.asarray(b)**2 + 1e-12)
    return np.where(np.abs(b) < 1e-6, 2.0, 1.0 / u)


def dsigma_domega(theta_deg, Z1, Z2, E_MeV):
    """
    Rutherford differential cross-section [fm²/sr].
    dσ/dΩ = (k·Z₁·Z₂·e² / 4Eₖ)² · csc⁴(θ/2)
    """
    theta = np.radians(theta_deg)
    factor = (K_E * Z1 * Z2 * q_e**2 / (4.0 * E_MeV * MEV))**2
    return factor / np.sin(theta/2)**4 / (1e-15)**2   # in fm²/sr


# ══════════════════════════════════════════════════════════════════════
#  RK4 INTEGRATION ENGINE  (dimensionless)
# ══════════════════════════════════════════════════════════════════════
def _deriv(s):
    """Equations of motion: ds/dt = [vx, vy, x/r³, y/r³]"""
    x, y, vx, vy = s
    r3 = np.hypot(x, y) ** 3
    return np.array([vx, vy, x / r3, y / r3])


def rk4_step(s, dt):
    """
    Single Runge-Kutta 4th-order step.
    s = [x, y, vx, vy] (dimensionless)
    Local truncation error: O(dt⁵)
    """
    k1 = _deriv(s)
    k2 = _deriv(s + 0.5*dt*k1)
    k3 = _deriv(s + 0.5*dt*k2)
    k4 = _deriv(s +     dt*k3)
    return s + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)


def _deriv_N(S):
    """Vectorized EOM for N particles. S shape (N,4)."""
    x, y = S[:,0], S[:,1]
    r3 = np.maximum(np.hypot(x, y)**3, 1e-8)
    dS = np.empty_like(S)
    dS[:,0]=S[:,2]; dS[:,1]=S[:,3]; dS[:,2]=x/r3; dS[:,3]=y/r3
    return dS


def rk4_N_step(S, dt):
    """Vectorized RK4 step — propagates all N particles in one NumPy call."""
    k1=_deriv_N(S); k2=_deriv_N(S+0.5*dt*k1)
    k3=_deriv_N(S+0.5*dt*k2); k4=_deriv_N(S+dt*k3)
    return S + (dt/6.0)*(k1+2*k2+2*k3+k4)


def dimensionless_energy(S):
    """
    Total dimensionless energy per particle.
    E = ½|v|² + 1/r  (conserved, initial value ≈ 0.5)
    Accepts single state [4] or batch (N,4).
    """
    if np.ndim(S) == 1:
        S = S[np.newaxis]
    r = np.hypot(S[:,0], S[:,1])
    return 0.5*(S[:,2]**2 + S[:,3]**2) + 1.0/r


# ══════════════════════════════════════════════════════════════════════
#  SIMULATOR CLASS
# ══════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════
#  PREDEFINED TARGET NUCLEI  (Z, A, name) — physically consistent sets
# ══════════════════════════════════════════════════════════════════════
NUCLEI = [
    #  symbol   Z    A       (index → use in GUI slider)
    ('He',    2,   4),    # 0 — helium     (α on α: low barrier)
    ('C',     6,  12),    # 1 — carbon
    ('O',     8,  16),    # 2 — oxygen
    ('Al',   13,  27),    # 3 — aluminium
    ('Fe',   26,  56),    # 4 — iron
    ('Cu',   29,  63),    # 5 — copper
    ('Ag',   47, 107),    # 6 — silver
    ('Au',   79, 197),    # 7 — gold  ← Geiger-Marsden default
    ('Pb',   82, 208),    # 8 — lead
]

OUTCOME_LABELS = {
    'nuclear_hit':    '⚠  NUCLEAR CONTACT',
    'large_scatter':  '↩  LARGE DEFLECTION  (θ > 90°)',
    'scatter':        '↗  RUTHERFORD SCATTER (10° < θ < 90°)',
    'slight':         '→  SLIGHT DEFLECTION  (θ < 10°)',
}

OUTCOME_COLORS = {
    'nuclear_hit':   '#ff2200',
    'large_scatter': '#ff8800',
    'scatter':       '#ffdd00',
    'slight':        '#44aaff',
}


class Simulator:
    """
    Encapsulates all physics for a single Rutherford scattering setup.

    Parameters
    ----------
    Z1 : int    — projectile charge (2 for alpha)
    Z2 : int    — target nuclear charge
    E_MeV : float — projectile kinetic energy [MeV]
    A_target : int  — target mass number (for nuclear radius)
    """

    def __init__(self, Z1=2, Z2=79, E_MeV=5.0, A_target=197):
        self.Z1 = Z1
        self.Z2 = Z2
        self.E_MeV = E_MeV
        self.A_target = A_target
        self.update_params()

    def update_params(self, Z1=None, Z2=None, E_MeV=None):
        """Recompute derived quantities after a parameter change."""
        if Z1    is not None: self.Z1    = int(Z1)
        if Z2    is not None: self.Z2    = int(Z2)
        if E_MeV is not None: self.E_MeV = float(E_MeV)

        self.a_m       = rutherford_a(self.Z1, self.Z2, self.E_MeV)
        self.a_fm      = self.a_m / 1e-15
        self.v0        = initial_speed(self.E_MeV)
        self.V_barrier = coulomb_barrier_MeV(self.Z1, self.Z2, self.A_target)
        self.r_nuc_dim = nuclear_radius_dim(self.Z1, self.Z2, self.E_MeV, self.A_target)
        self.b_safe    = min_b_for_safe_scatter(self.Z1, self.Z2, self.E_MeV, self.A_target)

    # ── Single trajectory ──────────────────────────────────────────
    def trajectory(self, b_prime, X0=22.0, dt=0.05, max_steps=3000):
        """
        Compute full RK4 trajectory for impact parameter b_prime.

        Parameters
        ----------
        b_prime  : float  — impact parameter / a  (+ above axis, − below)
        X0       : float  — starting distance from nucleus [units of a]
        dt       : float  — integration time step [dimensionless]
        max_steps: int    — safety cap on integration steps

        Returns
        -------
        dict with keys:
          'traj'         (N,2) array of (x,y) positions
          'theta'        scattering angle [°]
          'r_min'        closest approach [units of a]
          'E0'           initial energy
          'E_final'      final energy
          'E_cons'       energy conservation [%]
          'outcome'      string key in OUTCOME_LABELS
          'color'        color string for this outcome
          'b_prime'      echo of input
          's_final'      final state vector [x,y,vx,vy]
          'nuclear_hit'  bool
        """
        s      = np.array([-X0, float(b_prime), 1.0, 0.0])
        E0     = dimensionless_energy(s)[0]
        pts    = [s.copy()]   # full [x,y,vx,vy]
        r_min  = np.hypot(s[0], s[1])
        r_prev = r_min
        nuclear_hit = False

        for _ in range(max_steps):
            s = rk4_step(s, dt)
            r = np.hypot(s[0], s[1])
            if r < r_min: r_min = r
            pts.append(s.copy())

            if r < self.r_nuc_dim:          # Entered nuclear volume
                nuclear_hit = True
                break
            if r > r_prev and r > 0.80*X0:  # Particle escaping
                for ex in range(1, 26):
                    p = s[:2] + s[2:4] * (ex * dt * 14)
                    pts.append(np.array([p[0], p[1], s[2], s[3]]))
                break
            r_prev = r

        speed   = np.hypot(s[2], s[3])
        theta   = np.degrees(np.arccos(np.clip(s[2]/speed, -1.0, 1.0)))
        E_final = dimensionless_energy(s)[0]
        E_cons  = 100.0 * (1.0 - abs(E_final - E0) / abs(E0))  # conservation %
        E_err   = 100.0 * abs(E_final - E0) / abs(E0)           # error %

        if nuclear_hit:
            outcome = 'nuclear_hit'
        elif theta > 90:
            outcome = 'large_scatter'
        elif theta > 10:
            outcome = 'scatter'
        else:
            outcome = 'slight'

        return {
            'traj':        np.array(pts),
            'theta':       theta,
            'r_min':       r_min,
            'E0':          E0,
            'E_final':     E_final,
            'E_cons':      E_cons,   # conservation %  (e.g. 99.99999)
            'E_err':       E_err,    # error %         (e.g.  0.00001)
            'outcome':     outcome,
            'color':       OUTCOME_COLORS[outcome],
            'b_prime':     b_prime,
            's_final':     s.copy(),
            'nuclear_hit': nuclear_hit,
        }

    # ── Fast coarse trajectory (for real-time slider preview) ─────
    def trajectory_fast(self, b_prime, X0=22.0, dt=0.20, max_steps=500):
        """Same as trajectory() but with large dt for instant preview."""
        return self.trajectory(b_prime, X0=X0, dt=dt, max_steps=max_steps)

    # ── Batch simulation (vectorized) ─────────────────────────────
    def batch(self, b_values, X0=22.0, dt=0.05, max_steps=5000):
        """
        Simulate many particles simultaneously (NumPy vectorized).
        Returns dict with 'theta_num', 'theta_ana', 'b_values',
        'rms_error', 'energy_error'.
        """
        b  = np.asarray(b_values, float)
        N  = len(b)
        S  = np.zeros((N, 4))
        S[:,0]=-X0; S[:,1]=b; S[:,2]=1.0
        E0 = dimensionless_energy(S)

        # Per-particle "been_close" threshold based on analytical r_min
        r_min_each = r_min_dim(np.abs(b))        # analytical closest approach
        close_thresh = np.maximum(r_min_each * 1.4, self.r_nuc_dim * 2.0)

        been_close   = np.zeros(N, bool)
        nuclear_hits = np.zeros(N, bool)
        active       = np.ones(N, bool)

        for _ in range(max_steps):
            if not active.any(): break
            S[active] = rk4_N_step(S[active], dt)
            r = np.hypot(S[:,0], S[:,1])

            # Nuclear collision — IDENTICAL to trajectory() criterion
            hit_now = active & (r < self.r_nuc_dim)
            nuclear_hits |= hit_now
            active[hit_now] = False

            been_close |= (r < close_thresh)
            done = active & been_close & (r > 0.78*X0)
            active[done] = False

        spd     = np.hypot(S[:,2], S[:,3])
        th_num  = np.degrees(np.arccos(np.clip(S[:,2]/spd, -1, 1)))
        th_ana  = theta_from_b(b)
        E_final = dimensionless_energy(S)

        # Exclude nuclear hits from angle statistics (undefined theta after hit)
        valid   = ~nuclear_hits
        rms     = float(np.sqrt(np.mean((th_num[valid]-th_ana[valid])**2))) if valid.any() else 0.0
        e_err   = float(np.mean(np.abs(E_final-E0)/np.abs(E0))*100)

        return {
            'theta_num':    th_num,
            'theta_ana':    th_ana,
            'b_values':     b,
            'rms_error':    rms,
            'energy_error': e_err,
            'nuclear_hits': int(nuclear_hits.sum()),
            'nuclear_mask': nuclear_hits.copy(),
            'n_valid':      int(valid.sum()),
        }

    # ── Summary string (for live dashboard) ───────────────────────
    def info_string(self):
        barrier_flag = ("✓ Rutherford regime" if self.E_MeV < self.V_barrier
                        else "⚠ Nuclear penetration possible!")
        return (
            f"Z₁={self.Z1}  Z₂={self.Z2}  Eₖ={self.E_MeV:.1f} MeV\n"
            f"a  = {self.a_fm:.2f} fm\n"
            f"v₀ = {self.v0/3e8:.4f} c\n"
            f"Coulomb barrier = {self.V_barrier:.1f} MeV\n"
            f"{barrier_flag}\n"
            f"Nuclear radius  = {self.r_nuc_dim:.4f} a\n"
            f"Min b (safe)    = {self.b_safe:.4f} a"
        )
