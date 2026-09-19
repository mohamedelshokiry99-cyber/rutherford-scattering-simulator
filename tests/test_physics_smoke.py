"""Headless regression checks; these are not a full physics validation."""
import unittest

import numpy as np

from physics_engine import Simulator


class PhysicsSmokeTests(unittest.TestCase):
    def test_default_trajectory_is_finite_and_conserves_energy(self):
        result = Simulator().trajectory(1.5)
        self.assertTrue(np.isfinite(result['traj']).all())
        self.assertFalse(result['nuclear_hit'])
        self.assertGreater(result['theta'], 0)
        self.assertLess(result['theta'], 180)
        self.assertLess(result['E_err'], 0.001)

    def test_mirrored_shots_have_mirrored_paths(self):
        sim = Simulator()
        above, below = sim.trajectory(1.5), sim.trajectory(-1.5)
        self.assertAlmostEqual(above['theta'], below['theta'], places=9)
        np.testing.assert_allclose(above['traj'][:, 0], below['traj'][:, 0])
        np.testing.assert_allclose(above['traj'][:, 1], -below['traj'][:, 1])

    def test_batch_outputs_are_finite(self):
        result = Simulator().batch(np.array([0.5, 1.5, 3.0, 6.0]))
        self.assertEqual(result['n_valid'], 4)
        self.assertEqual(result['nuclear_hits'], 0)
        self.assertTrue(np.isfinite(result['theta_num']).all())
        self.assertLess(result['energy_error'], 0.001)

    def test_high_energy_helium_shot_stops_at_nuclear_contact(self):
        sim = Simulator(Z2=2, A_target=4, E_MeV=80)
        result = sim.trajectory(0)
        self.assertTrue(result['nuclear_hit'])
        self.assertEqual(result['outcome'], 'nuclear_hit')
        self.assertLess(result['r_min'], sim.r_nuc_dim)


if __name__ == '__main__':
    unittest.main()
