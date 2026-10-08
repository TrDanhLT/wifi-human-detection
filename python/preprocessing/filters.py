import numpy as np

def moving_average(x, kernel_size=5):
    if kernel_size <= 1: return x
    k = np.ones(kernel_size, dtype=np.float32) / kernel_size
    if x.ndim == 1: return np.convolve(x, k, mode="same")
    return np.column_stack([np.convolve(x[:,i], k, mode="same") for i in range(x.shape[1])])
