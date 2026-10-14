import numpy as np


def estimate_pass_at_k(
    num_samples: list[int], num_correct: list[int], k: int
) -> np.ndarray:
    """
    Estimates pass@k of each problem and returns them in an array.
    """

    def estimator(n: int, c: int, k: int) -> float:
        """
        Calculates 1 - comb(n - c, k) / comb(n, k).
        """
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

    return np.array(
        [estimator(int(n), int(c), k) for n, c in zip(num_samples, num_correct)]
    )


def pass_at_k(ns, cs, k):
    return np.mean(estimate_pass_at_k(ns, cs, k))
