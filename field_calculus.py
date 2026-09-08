"""Spatial derivatives and work integrals through the bounded calculator."""
import ast
import numpy as np
from calculus import multivariable, differentiate, integrate, CalculusError
from array_types import VectorValue, MatrixValue

OPERATIONS={'field_gradient':'gradient','field_jacobian':'jacobian',
            'field_divergence':'divergence','field_curl':'curl',
            'field_laplacian':'laplacian','field_hessian':'hessian',
            'field_directional':'directional','force':'gradient',
            'field_convective':'jacobian'}
NAMES=set(OPERATIONS)|{'work'}


def point(value):
    a=np.asarray(value,dtype=complex)
    if a.ndim!=1 or not 1<=a.size<=32 or not np.all(np.isfinite(a)) or np.any(a.imag):
        raise CalculusError('Supply a finite real position vector with 1–32 coordinates.')
    return a.real


def function_name(node,calculator):
    if not isinstance(node,ast.Name) or node.id not in calculator.functions:
        raise CalculusError('Use a defined function name, for example field_divergence(F,[1,2]).')
    return node.id


def call(calculator,name,p,stack):
    params,tree=calculator.functions[name]
    if name in stack:raise CalculusError('Recursive fields are not supported.')
    if len(params)==1:
        local={params[0]:np.asarray(p).view(VectorValue)}
    elif len(params)==len(p):local=dict(zip(params,p))
    else:raise CalculusError(f'{name} must accept one position vector or {len(p)} coordinate arguments.')
    return calculator.evaluate(tree,local,stack+(name,))


def typed(value):
    value=np.asarray(value)
    return value.view(MatrixValue) if value.ndim==2 else value.view(VectorValue) if value.ndim==1 else value


def evaluate(calculator,node,local,stack):
    operation=node.func.id
    if operation=='work':return work(calculator,node,local,stack)
    directional=operation=='field_directional'
    if len(node.args) not in ((3,4) if directional else (2,3)):
        raise CalculusError('Use field_op(F, [position][, step]); field_directional(F, [position], [direction][, step]).')
    name=function_name(node.args[0],calculator)
    position=point(calculator.evaluate(node.args[1],local,stack))
    direction=point(calculator.evaluate(node.args[2],local,stack)) if directional else None
    step_index=3 if directional else 2
    step=calculator.evaluate(node.args[step_index],local,stack) if len(node.args)>step_index else None
    if calculator.calculus_depth>=3:raise CalculusError('Limit nested calculus to three operations.')
    calculator.calculus_depth+=1
    try:
        callback=lambda p:call(calculator,name,p,stack)
        kernel=OPERATIONS[operation]
        # Planar curl is the signed component perpendicular to the x/y plane.
        planar=operation=='field_curl' and len(position)==2
        if planar:kernel='jacobian'
        result,diagnostics=multivariable(callback,position,kernel,step,direction)
        if planar:
            if result.shape!=(2,2):raise CalculusError('Planar curl requires a two-component field.')
            result=np.asarray(result[1,0]-result[0,1])
            if diagnostics['error_estimate'] is not None:diagnostics['error_estimate']*=2
        if operation=='force':result=-result
        if operation=='field_convective':
            vector=np.asarray(callback(position))
            if vector.shape!=position.shape or result.shape!=(len(position),len(position)):
                raise CalculusError('Convective derivative requires one field component per spatial coordinate.')
            result=result@vector
            if diagnostics['error_estimate'] is not None:diagnostics['error_estimate']*=float(np.sum(np.abs(vector)))
        diagnostics.update(operation=operation,input_dimensions=len(position),field=name)
        calculator.calculus_diagnostics.append(diagnostics)
        calculator.calculus_diagnostics=calculator.calculus_diagnostics[-20:]
        return typed(result)
    finally:calculator.calculus_depth-=1


def work(calculator,node,local,stack):
    if len(node.args) not in (4,5,6):raise CalculusError('Use work(F, path, lower, upper[, abs_tol, rel_tol]).')
    field=function_name(node.args[0],calculator);path=function_name(node.args[1],calculator)
    params,tree=calculator.functions[path]
    if len(params)!=1:raise CalculusError('The path must have one scalar parameter, for example r(t)=[cos(t),sin(t)].')
    args=[calculator.evaluate(arg,local,stack) for arg in node.args[2:]]
    if calculator.calculus_depth>=2:raise CalculusError('Work integrals need two available calculus nesting levels.')
    calculator.calculus_depth+=2
    errors=[]
    def curve(t):
        if path in stack:raise CalculusError('Recursive paths are not supported.')
        return point(calculator.evaluate(tree,{params[0]:t},stack+(path,)))
    def integrand(t):
        location=curve(t)
        tangent,diag=differentiate(curve,t)
        force=np.asarray(call(calculator,field,location,stack))
        if force.shape!=location.shape:raise CalculusError('Field and path must have matching vector dimensions.')
        if diag['error_estimate'] is not None:errors.append(diag['error_estimate'])
        return np.dot(force,tangent)
    try:
        if any(np.ndim(a) for a in args[:2]):raise CalculusError('Work integral limits must be scalar.')
        result,diagnostics=integrate(integrand,*args)
        diagnostics.update(operation='work integral',field=field,path=path,tangent_error_estimate=max(errors,default=None))
        calculator.calculus_diagnostics.append(diagnostics)
        calculator.calculus_diagnostics=calculator.calculus_diagnostics[-20:]
        return result
    finally:calculator.calculus_depth-=2
