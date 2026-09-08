"""Progressively refine complete grids without exceeding interpreter work limits."""
from fractions import Fraction
import numpy as np


class SamplingLimit(Exception):
    pass


class WorkBudget:
    def __init__(self, limit):
        self.limit = limit
        self.used = 0

    def consume(self):
        if self.used >= self.limit:
            raise SamplingLimit('Plot sampling budget exhausted.')
        self.used += 1


def sample_grid(calculator, evaluate, ranges, target, limit, initial=None):
    """Return the finest completed uniform grid, including both range endpoints.

    Cached coordinates are reused between refinement levels. An interrupted
    level is discarded, never presented as a truncated curve or partial surface.
    Syntax, shape, and per-point evaluation errors still propagate normally.
    """
    budget = WorkBudget(limit)
    previous_budget = calculator.sampling_budget
    calculator.sampling_budget = budget
    cache = {}
    completed = None
    side = min(target, initial or (3 if len(ranges) == 2 else 9))
    try:
        while True:
            fractions = [Fraction(k, side - 1) for k in range(side)]
            keys = [(a, b) for b in fractions for a in fractions] if len(ranges) == 2 else [(a,) for a in fractions]
            try:
                for key in keys:
                    if key not in cache:
                        point = tuple(lo + float(t) * (hi - lo) for t, (lo, hi) in zip(key, ranges))
                        calculator.steps = 0
                        cache[key] = evaluate(*point)
            except SamplingLimit:
                if completed is None:
                    raise ValueError('This formula is too expensive to plot even at low resolution. Try a narrower input range or evaluate it at a single point.')
                break
            completed = (side, keys)
            if side == target:
                break
            side = min(target, 2 * (side - 1) + 1)
    finally:
        calculator.sampling_budget = previous_budget
    side, keys = completed
    axes = [np.linspace(lo, hi, side) for lo, hi in ranges]
    info = {'points': len(keys), 'target_points': target ** len(ranges),
            'reduced': side < target, 'evaluation_steps': budget.used}
    if side < target:
        detail = f'{side} × {side} grid' if len(ranges) == 2 else f'{side} points'
        info['notice'] = f'Reduced plot detail: {detail}. The full input range is shown; narrow the range to inspect small features.'
    return axes, [cache[key] for key in keys], info
