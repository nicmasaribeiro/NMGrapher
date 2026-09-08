"""Numerical calculus kernels; callbacks come only from the restricted interpreter."""
import numpy as np
from scipy.integrate import quad_vec

class CalculusError(ValueError):
    pass


def differentiate(function, point, order=1, step=None):
    if np.ndim(order) or order not in (1, 2):
        raise CalculusError('Derivative order must be 1 or 2.')
    point=np.asarray(point)
    if not np.all(np.isfinite(point)):
        raise CalculusError('Derivative points must be finite.')
    if step is not None and (np.ndim(step) or np.iscomplexobj(step) or not np.isfinite(step) or step<=0):
        raise CalculusError('Derivative step must be a positive finite real scalar.')
    h=step if step is not None else np.finfo(float).eps**(1/(5 if order==1 else 6)) * np.maximum(1,np.abs(point))
    if np.any(~np.isfinite(h)) or np.any(point+h/2 == point) or (order == 2 and np.any((np.asarray(h)/2)**2 == 0)):
        raise CalculusError('Derivative step is too small to resolve at this point, or too large to remain finite.')
    def stencil(h):
        fm2,fm1,f0,fp1,fp2=[np.asarray(function(point+k*h)) for k in (-2,-1,0,1,2)]
        if order==1:
            d=(fm2-8*fm1+8*fp1-fp2)/(12*h)
        else:
            d=(-fp2+16*fp1-30*f0+16*fm1-fm2)/(12*h*h)
        left=(3*f0-4*fm1+fm2)/(2*h)
        right=(-3*f0+4*fp1-fp2)/(2*h)
        smooth=np.abs(left-right)<=1e-4*(1+np.maximum(np.abs(left),np.abs(right)))
        return d,smooth
    coarse,_=stencil(h)
    fine,smooth=stencil(h/2)
    error=np.abs(fine-coarse)/15
    valid=np.isfinite(fine)&smooth
    value=np.where(valid,fine,np.nan)
    finite_error=error[np.isfinite(error)]
    diagnostics={'operation':'derivative','order':int(order),
                 'error_estimate':float(np.max(finite_error)) if finite_error.size else None,
                 'undefined_samples':int(np.count_nonzero(~valid))}
    return value,diagnostics


def integrate(function, lower, upper, abs_tol=1e-8, rel_tol=1e-7):
    if (np.ndim(abs_tol) or np.iscomplexobj(abs_tol) or not np.isfinite(abs_tol) or not 1e-12 <= abs_tol <= 1
        or np.ndim(rel_tol) or np.iscomplexobj(rel_tol) or not np.isfinite(rel_tol) or not 0 <= rel_tol <= 1):
        raise CalculusError('Use absolute tolerance from 1e-12 to 1 and relative tolerance from 0 to 1.')
    lower,upper=np.asarray(lower),np.asarray(upper)
    if np.any(np.imag(lower)!=0) or np.any(np.imag(upper)!=0) or not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)):
        raise CalculusError('Integration limits must be finite real values.')
    lower,upper=np.broadcast_arrays(lower.real,upper.real)
    width=upper-lower
    def transformed(t):
        # Map every finite interval onto [0,1], including reversed limits.
        value=np.asarray(function(lower+width*t))
        value=np.where(width==0,0,value*width)
        if not np.all(np.isfinite(value)):
            raise CalculusError('Integrand is non-finite inside the interval; split the integral at singularities.')
        return value
    value,error,info=quad_vec(transformed,0.0,1.0,epsabs=abs_tol,epsrel=rel_tol,
                              norm='max',limit=100,full_output=True)
    if not info.success or not np.all(np.isfinite(value)):
        raise CalculusError('Integral did not converge. Split the interval or simplify the integrand.')
    return np.asarray(value),{'operation':'integral','error_estimate':float(error),
                             'evaluations':int(info.neval), 'absolute_tolerance':float(abs_tol), 'relative_tolerance':float(rel_tol)}


def multivariable(function, point, operation, step=None, direction=None):
    """Coordinate derivatives with scalar coordinates and explicit output axes."""
    point = np.asarray(point, dtype=complex)
    if point.ndim != 1 or not 1 <= point.size <= 32 or not np.all(np.isfinite(point)):
        raise CalculusError('Choose 1–32 calculus variables with finite scalar coordinates.')
    if step is not None and (np.ndim(step) or np.iscomplexobj(step) or not np.isfinite(step) or step <= 0):
        raise CalculusError('Derivative step must be a positive finite real scalar.')
    if np.all(point.imag == 0): point = point.real
    n = len(point)
    cache = {}
    output_shape = None

    def value(p):
        nonlocal output_shape
        key = tuple(p)
        if key not in cache:
            a = np.asarray(function(p), dtype=complex)
            if a.ndim > 2 or not a.size or (a.ndim and max(a.shape) > 32):
                raise CalculusError('Calculus output must be a scalar, vector, or matrix up to 32×32.')
            if output_shape is None: output_shape = a.shape
            elif a.shape != output_shape: raise CalculusError('Output shape changes near the evaluation point.')
            cache[key] = a
        return cache[key]

    f0 = value(point)
    scalar = f0.ndim == 0
    if operation in ('gradient', 'hessian', 'mixed_diff') and not scalar:
        raise CalculusError('This operation needs a scalar-valued expression; use jacobian for vector/matrix outputs.')
    if operation == 'jacobian' and f0.size > 32:
        raise CalculusError('Jacobian supports up to 32 output entries; select a smaller output or individual matrix entries.')
    if operation == 'divergence' and (f0.ndim != 1 or len(f0) != n):
        raise CalculusError('Divergence needs a vector with one component per selected variable.')
    if operation == 'curl' and (n != 3 or f0.shape != (3,)):
        raise CalculusError('Curl needs three selected variables and a three-component vector.')
    if operation == 'mixed_diff' and n != 2:
        raise CalculusError('mixed_diff needs exactly two distinct variables; use diff(..., x, x, 2) for a repeated variable.')
    errors = []

    def partial(axis, order):
        def callback(coordinate):
            p = point.copy(); p[axis] = coordinate
            return value(p)
        result, diag = differentiate(callback, point[axis], order, step)
        if diag['error_estimate'] is not None: errors.append(diag['error_estimate'])
        return result

    if operation == 'directional':
        direction = np.asarray(direction)
        if direction.shape != point.shape or np.any(np.imag(direction) != 0) or not np.all(np.isfinite(direction)):
            raise CalculusError('Direction must contain one finite real value per selected variable.')
        result, diag = differentiate(lambda t: value(point + t*direction.real), 0.0, 1, step)
        if diag['error_estimate'] is not None: errors.append(diag['error_estimate'])
    elif operation in ('gradient', 'jacobian', 'divergence', 'curl'):
        columns = [partial(axis, 1) for axis in range(n)]
        if operation == 'gradient': result = np.asarray(columns)
        elif operation == 'jacobian': result = np.column_stack([c.reshape(-1) for c in columns])
        elif operation == 'divergence': result = np.asarray(sum(columns[k][k] for k in range(n)))
        else:
            result = np.asarray([columns[1][2]-columns[2][1], columns[2][0]-columns[0][2], columns[0][1]-columns[1][0]])
    elif operation == 'laplacian':
        result = np.sum([partial(axis, 2) for axis in range(n)], axis=0)
    elif operation in ('hessian', 'mixed_diff'):
        diagonal = [partial(axis, 2) for axis in range(n)]
        h = np.full(n, step) if step is not None else np.finfo(float).eps**(1/6) * np.maximum(1, np.abs(point))
        result = np.diag(np.asarray(diagonal, dtype=complex))
        for a in range(n):
            for b in range(a+1, n):
                def mixed(scale):
                    total = 0j
                    for sa, sb in ((1,1), (1,-1), (-1,1), (-1,-1)):
                        p = point.copy(); p[a] += sa*h[a]*scale; p[b] += sb*h[b]*scale
                        total += sa*sb*value(p)
                    return total / (4*h[a]*h[b]*scale**2)
                coarse, fine = mixed(1), mixed(.5)
                errors.append(float(abs(fine-coarse)/3))
                entry = fine + (fine-coarse)/3
                if not np.isfinite(diagonal[a]) or not np.isfinite(diagonal[b]): entry = complex(np.nan)
                result[a,b] = result[b,a] = entry
        if operation == 'mixed_diff': result = np.asarray(result[0,1])
    else:
        raise CalculusError('Unknown multivariable calculus operation.')
    result = np.asarray(result)
    finite_errors = [e for e in errors if np.isfinite(e)]
    estimate = (sum(finite_errors) if operation in ('divergence','laplacian','curl') else max(finite_errors)) if finite_errors else None
    return result, {'operation':operation, 'error_estimate':estimate, 'evaluations':len(cache),
                    'undefined_samples':int(np.count_nonzero(~np.isfinite(result))),
                    'input_dimensions':n, 'output_shape':list(f0.shape)}
