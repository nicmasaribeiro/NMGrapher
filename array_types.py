"""Tag worksheet arrays separately from sampled graph coordinates."""
import numpy as np

class MatrixValue(np.ndarray):
    pass

class VectorValue(np.ndarray):
    pass
