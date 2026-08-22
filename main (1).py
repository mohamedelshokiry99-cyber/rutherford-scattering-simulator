"""
Rutherford Scattering Simulator — Entry Point
=============================================
Run:  python main.py
"""
import sys
import os

# Ensure same directory is on path so gui.py finds physics_engine.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("═" * 56)
    print("  Rutherford Scattering Interactive Simulator")
    print("  RK4 High-Precision | Coulomb Physics Engine")
    print("═" * 56)
    print()

    # Verify dependencies
    missing = []
    for pkg in ['numpy', 'matplotlib']:
        try: __import__(pkg)
        except ImportError: missing.append(pkg)
    if missing:
        print(f"[ERROR] Missing packages: {', '.join(missing)}")
        print(f"  Install: pip install {' '.join(missing)}")
        sys.exit(1)

    try:
        import scipy
    except ImportError:
        print("[WARN] scipy not found — using built-in constants (fine).")

    print("  Loading physics engine...")
    from physics_engine import Simulator, coulomb_barrier_MeV, nuclear_radius_m

    # Quick sanity check
    sim = Simulator(Z1=2, Z2=79, E_MeV=5.0, A_target=197)
    print(f"  a  = {sim.a_fm:.2f} fm")
    print(f"  v₀ = {sim.v0/3e8:.4f} c")
    print(f"  Coulomb barrier (Au) = {sim.V_barrier:.1f} MeV")
    print(f"  Nuclear radius  (Au) = {nuclear_radius_m(197)/1e-15:.2f} fm")
    print()
    print("  ┌─────────────────────────────────────────┐")
    print("  │  CONTROLS                               │")
    print("  │  b' slider     → aim the particle       │")
    print("  │  Eₖ slider     → change kinetic energy  │")
    print("  │  Target nucleus → change the predefined │")
    print("  │                    target nucleus         │")
    print("  │  🔥 FIRE       → animate single shot    │")
    print("  │  🌧 SHOWER     → run 400-particle batch  │")
    print("  │                    + 20 representative  │")
    print("  │                      trajectories       │")
    print("  │  🗑 CLEAR      → reset all trajectories  │")
    print("  │  ⏸ PAUSE      → pause/resume animation  │")
    print("  ├─────────────────────────────────────────┤")
    print("  │  PHYSICS OUTCOMES                       │")
    print("  │  ⚠  NUCLEAR CONTACT  (Eₖ > barrier)    │")
    print("  │  ↩  LARGE DEFLECTION   θ > 90°          │")
    print("  │  ↗  RUTHERFORD SCATTER 10° < θ < 90°   │")
    print("  │  →  SLIGHT DEFLECTION  θ < 10°          │")
    print("  └─────────────────────────────────────────┘")
    print()
    print("  Tip: raise Eₖ above the Coulomb barrier to")
    print("       see nuclear contact with lighter nuclei.")
    print("       Nuclear dynamics are outside the scope")
    print("       of this Coulomb-only model.")
    print()

    print("  Launching GUI...")
    from gui import run
    run()

if __name__ == '__main__':
    main()
