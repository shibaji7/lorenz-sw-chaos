import numpy as np

from lorenzsw.transfer_operator import dmd_transfer_operator


def test_dmd_transfer_operator_shapes_and_decay():
    snapshots = np.array([[1.0, 0.8, 0.64, 0.512]])
    eigs, modes = dmd_transfer_operator(snapshots)
    assert eigs.shape[0] == modes.shape[1]
    assert modes.shape[0] == snapshots.shape[0]
    assert np.all(np.abs(eigs) < 1.0)
