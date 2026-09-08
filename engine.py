"""Bounded numeric AST interpreter. No eval, exec, or symbolic string parsing."""
import ast
import re
import operator
import keyword
from notation import normalize_notation
from calculus import differentiate, integrate, multivariable
from symbols import normalize_symbols
from array_types import MatrixValue, VectorValue
import quantum
import linear_algebra
import probability
import wavelets
import resident_math
import datasets as dataset_math
from datasets import DataColumn, PointSeries
import numpy as np
from scipy.linalg import expm, logm, sqrtm

MAX_MATRIX = 32


class ExpressionError(ValueError):
    pass

def matrix(a):
    a = np.asarray(a, dtype=complex)
    if a.ndim != 2 or max(a.shape) > MAX_MATRIX:
        raise ExpressionError('Use a rectangular matrix with 1–32 rows and columns.')
    return (a.real if np.all(a.imag == 0) else a).view(MatrixValue)

def square(a):
    a = matrix(a)
    if a.shape[0] != a.shape[1]:
        raise ExpressionError('This operation needs a square matrix.')
    return a

def eye(n):
    if np.ndim(n) or int(n) != n or not 1 <= n <= MAX_MATRIX:
        raise ExpressionError('eye(n) needs an integer between 1 and 32.')
    return np.eye(int(n)).view(MatrixValue)

def power(a,b):
    if np.ndim(b) == 0 and abs(b) > 1000:
        raise ExpressionError('Exponent magnitude must be at most 1000.')
    if isinstance(a, MatrixValue) and a.ndim == 2:
        if np.ndim(b) or not np.isreal(b) or int(np.real(b)) != b:
            raise ExpressionError('Matrix powers need an integer; use expm(A) for the matrix exponential.')
        return np.linalg.matrix_power(square(a), int(np.real(b)))
    return np.emath.power(a,b)

def phase(a):
    a = np.asarray(a)
    return np.where((np.abs(a) == 0) | ~np.isfinite(a), np.nan, np.angle(a))

def polar(r, theta):
    if np.iscomplexobj(r) or np.iscomplexobj(theta) or np.any(np.asarray(r) < 0):
        raise ExpressionError('polar(r, theta) needs a nonnegative real radius and real angle.')
    return np.asarray(r) * np.exp(1j * np.asarray(theta))

def roots(z, n):
    if np.ndim(z) or np.ndim(n) or not np.isreal(n) or int(np.real(n)) != n or not 1 <= np.real(n) <= 32:
        raise ExpressionError('roots(z, n) needs a scalar z and integer n from 1 to 32.')
    n = int(np.real(n))
    return abs(z)**(1/n) * np.exp(1j * (np.angle(z) + 2*np.pi*np.arange(n))/n)

def inner(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape:
        raise ExpressionError('inner(u, v) needs equal-length vectors; use [1, i] notation.')
    return np.vdot(a, b)

def algebraic_vector(a):
    return np.asarray(quantum.vector(a)).view(VectorValue)

def matmul(a,b):
    a,b=np.asarray(a),np.asarray(b)
    if a.ndim not in (1,2) or b.ndim not in (1,2):
        raise ExpressionError('Matrix multiplication needs vectors or matrices; use * for scalar scaling.')
    try:return a@b
    except ValueError as exc:raise ExpressionError(f'Cannot multiply shapes {a.shape} and {b.shape}; inner dimensions must match.') from exc

def tensor(a,b):
    a,b=np.asarray(a),np.asarray(b)
    if a.ndim not in (1,2) or b.ndim!=a.ndim:
        raise ExpressionError('tensor needs two vectors or two matrices; use col(v) to give a vector a column shape.')
    if any(x*y>MAX_MATRIX for x,y in zip(a.shape,b.shape)):
        raise ExpressionError('Tensor product would exceed the 32-entry / 32×32 limit.')
    return np.kron(a,b)

def vector_dot(a,b):
    a,b=quantum.vector(a),quantum.vector(b)
    if a.shape!=b.shape:raise ExpressionError('Dot product needs equal-length vectors.')
    return np.dot(a,b)

def hadamard_product(a,b):
    if np.shape(a)!=np.shape(b):raise ExpressionError('Entrywise multiplication needs matching shapes.')
    return np.multiply(a,b)

FUNCTIONS = {
    'sin':np.sin, 'cos':np.cos, 'tan':np.tan, 'asin':np.emath.arcsin,
    'acos':np.emath.arccos, 'atan':np.arctan, 'sinh':np.sinh, 'cosh':np.cosh,
    'exp':np.exp, 'log':np.emath.log, 'ln':np.emath.log, 'log10':np.emath.log10,
    'sqrt':np.emath.sqrt, 'abs':np.abs, 'floor':np.floor, 'ceil':np.ceil,
    'sign':np.sign, 'min':np.minimum, 'max':np.maximum, 'where':np.where,
    'det':lambda a:np.linalg.det(square(a)), 'inv':lambda a:np.linalg.inv(square(a)),
    'pinv':lambda a:np.linalg.pinv(matrix(a)), 'T':lambda a:matrix(a).T,
    'trace':lambda a:np.trace(matrix(a)), 'rank':lambda a:np.linalg.matrix_rank(matrix(a)),
    'eigvals':lambda a:np.linalg.eigvals(square(a)),
    'expm':lambda a:expm(square(a)), 'logm':lambda a:logm(square(a)),
    'solve':lambda a,b:np.linalg.solve(square(a),np.asarray(b)),
    'norm':lambda a:np.linalg.norm(a), 'eye':eye, 'matrix':matrix,
    'real':np.real, 'imag':np.imag, 'conj':np.conj,
    'arg':phase, 'phase':phase, 'polar':polar,
    'cis':lambda t:polar(1, t), 'roots':roots, 'inner':inner,
    'H':lambda a:matrix(a).conj().T, 'sqrtm':lambda a:sqrtm(square(a)),
    'ishermitian':lambda a:bool(np.allclose(square(a), square(a).conj().T, atol=1e-10, rtol=1e-8)),
    'isunitary':lambda a:bool(np.allclose(square(a).conj().T @ square(a), np.eye(len(a)), atol=1e-10, rtol=1e-8)),
    'sum':lambda a:np.sum(a), 'mean':lambda a:np.mean(a),
}
FUNCTIONS.update(quantum.FUNCTIONS)
FUNCTIONS.update(dataset_math.FUNCTIONS)
FUNCTIONS.update(linear_algebra.FUNCTIONS)
FUNCTIONS.update({'vector':algebraic_vector,'matmul':matmul,'dot':vector_dot,'outer':lambda a,b:np.outer(quantum.vector(a),quantum.vector(b)),
                  'tensor':tensor,'kron':tensor,'col':lambda a:quantum.vector(a).reshape(-1,1),'row':lambda a:quantum.vector(a).reshape(1,-1),
                  'bra':lambda a:quantum.vector(a).conj().reshape(1,-1),'hadamard_product':hadamard_product})
probability.install(FUNCTIONS)
FUNCTIONS.update(wavelets.FUNCTIONS)
FUNCTIONS.update(resident_math.FUNCTIONS)
ALGEBRAIC_FUNCTIONS=set(quantum.FUNCTIONS)|set(linear_algebra.FUNCTIONS)|{'vector','matmul','dot','outer','tensor','kron','col','row','bra','hadamard_product',
    'inv','pinv','T','H','eigvals','expm','logm','solve','eye','matrix','sqrtm','roots'}
MULTIVARIABLE = {'grad':'gradient', 'gradient':'gradient', 'jacobian':'jacobian', 'hessian':'hessian', 'divergence':'divergence', 'curl':'curl', 'laplacian':'laplacian', 'directional':'directional', 'mixed_diff':'mixed_diff'}
REDUCTIONS = {'sum','summation','product','prod'}
CALCULUS = {'prime','diff','derivative','integrate','integral','antiderivative','at'} | set(MULTIVARIABLE)
CONSTANTS = {'pi':np.pi, 'π':np.pi, 'e':np.e, 'i':1j, 'j':1j}
OPS = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul,
       ast.Div:operator.truediv, ast.Pow:power, ast.MatMult:matmul,
       ast.Mod:operator.mod}
COMPS = {ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,
         ast.Eq:operator.eq,ast.NotEq:operator.ne}

def parse(text):
    text = normalize_notation(text.strip()).replace('^','**').replace('×','*').replace('−','-')
    # Only numeric imaginary coefficients get implicit multiplication (2i, 1e-3i).
    text = re.sub(r'(?<![\w.])((?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)i\b', r'\1*i', text)
    if len(text)>1200:
        raise ExpressionError('Expression is too long (maximum 1200 characters).')
    try:
        tree=ast.parse(text,mode='eval').body
    except (SyntaxError,RecursionError) as exc:
        raise ExpressionError('Check expression syntax. Use * for multiplication.') from exc
    if sum(1 for _ in ast.walk(tree))>300:
        raise ExpressionError('Expression is too complex.')
    return tree

class Calculator:
    def __init__(self, rows, datasets=None):
        self.rows=rows
        self.datasets, self.dataset_values = dataset_math.validate_datasets([] if datasets is None else datasets, set(FUNCTIONS)|set(CONSTANTS)|CALCULUS|{'x','y'})
        self.definitions={}
        self.functions={}
        self.items=[]
        self.steps=0
        self.calculus_diagnostics=[]
        self.calculus_depth=0
        for row in rows:
            text=row.get('text','').strip()
            item={'text':text,'kind':'value'}
            try:
                # A single '=' is an assignment, function definition, or plotted equality.
                normalized=normalize_notation(text)
                match=re.match(r'^([^\W\d]\w*)(?:\(([^()]*)\))?\s*=(?!=)(.+)$',normalized,re.S)
                if match:
                    name,arg,rhs=match.groups()
                    if keyword.iskeyword(name):raise ExpressionError('A function or variable name cannot be a Python keyword.')
                    if name in ('x','y') and arg is None:
                        item.update(kind='explicit' if name=='y' else 'implicit', tree=parse(rhs if name=='y' else f'x-({rhs})'))
                    else:
                        if name in FUNCTIONS or name in CALCULUS or name in CONSTANTS or name in self.definitions or name in self.functions or name in self.dataset_values:
                            raise ExpressionError(f'Name {name} is reserved or already defined.')
                        tree=parse(rhs)
                        if arg is not None:
                            params=tuple(a.strip() for a in arg.split(','))
                            if not params or any(not a.isidentifier() or keyword.iskeyword(a) for a in params):
                                raise ExpressionError('Use distinct named arguments, for example f(x, y, z) = x^2 + y*z.')
                            if len(set(params))!=len(params):raise ExpressionError('Function arguments must have different names.')
                            if any(a in CONSTANTS or a in FUNCTIONS or a in CALCULUS for a in params):raise ExpressionError('Function arguments cannot use reserved constants or built-in function names.')
                            self.functions[name]=(params,tree)
                            item.update(kind='function',name=name,tree=tree,params=params,body=text.split('=',1)[1].strip())
                        else:
                            self.definitions[name]=tree
                            item.update(kind='definition',name=name,tree=tree)
                elif re.search(r'(?<![<>=!])=(?!=)',normalized):
                    sides=re.split(r'(?<![<>=!])=(?!=)',normalized)
                    if len(sides)!=2: raise ExpressionError('Use one equality per expression.')
                    item.update(kind='implicit',tree=parse(f'({sides[0]})-({sides[1]})'))
                else:
                    item['tree']=parse(text) if text else None
                    if isinstance(item['tree'],ast.Compare): item['kind']='inequality'
            except Exception as exc:
                item['error']=str(exc)
            self.items.append(item)

    def evaluate(self,node,local=None,stack=()):
        local={} if local is None else local
        self.steps+=1
        if self.steps>50000 or len(stack)>40:
            raise ExpressionError('Evaluation limit reached; simplify the expression.')
        if isinstance(node,ast.Constant) and type(node.value) in (int,float,complex):
            if abs(node.value)>1e100: raise ExpressionError('Number is too large.')
            return float(node.value) if type(node.value) is int else node.value
        if isinstance(node,ast.Name):
            name=node.id
            if name in local:return local[name]
            if name in CONSTANTS:return CONSTANTS[name]
            if name in self.dataset_values:return self.dataset_values[name]
            if name in stack:raise ExpressionError('Circular dependency: '+' → '.join(stack+(name,)))
            if name in self.definitions:return self.evaluate(self.definitions[name],local,stack+(name,))
            raise ExpressionError(f'Unknown variable: {name}')
        if isinstance(node,(ast.List,ast.Tuple)):
            if len(node.elts)>MAX_MATRIX:raise ExpressionError('Lists support at most 32 entries.')
            a=np.asarray([self.evaluate(n,local,stack) for n in node.elts])
            if a.ndim==2 and not a.size:raise ExpressionError('Empty matrix literals are not supported; nullspace and orth can return empty bases.')
            if a.ndim>2 or a.size>1024:raise ExpressionError('Only vectors and 2D matrices are supported.')
            return matrix(a) if a.ndim == 2 else a.view(VectorValue)
        if isinstance(node,ast.BinOp) and type(node.op) in OPS:
            a=self.evaluate(node.left,local,stack);b=self.evaluate(node.right,local,stack)
            typed=lambda v:isinstance(v,(MatrixValue,VectorValue))
            if isinstance(node.op,ast.Mult) and typed(a) and typed(b) and a.ndim in (1,2) and b.ndim in (1,2) and (a.ndim==2 or b.ndim==2):
                result=matmul(a,b)
            else:result=OPS[type(node.op)](a,b)
            if (isinstance(a,DataColumn) or isinstance(b,DataColumn)) and np.ndim(result)==1:return np.asarray(result).view(DataColumn)
            if isinstance(node.op,(ast.MatMult,ast.Mult)) and (typed(a) or typed(b)):
                if np.ndim(result)==2 and max(np.shape(result))<=MAX_MATRIX:return matrix(result)
                if np.ndim(result)==1 and np.size(result)<=MAX_MATRIX:return np.asarray(result).view(VectorValue)
            return result
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            a=self.evaluate(node.operand,local,stack)
            return -a if isinstance(node.op,ast.USub) else a
        if isinstance(node,ast.Compare):
            a=self.evaluate(node.left,local,stack);result=True
            for op,right in zip(node.ops,node.comparators):
                if type(op) not in COMPS:raise ExpressionError('Unsupported comparison.')
                b=self.evaluate(right,local,stack)
                if not isinstance(op,(ast.Eq,ast.NotEq)) and (np.any(np.imag(a)!=0) or np.any(np.imag(b)!=0)):
                    raise ExpressionError('Complex numbers are not ordered. Compare abs(...), real(...), or imag(...).')
                result=np.logical_and(result,COMPS[type(op)](a,b));a=b
            return result
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
            name=node.func.id
            if name in REDUCTIONS and len(node.args)==4:return self.evaluate_reduction(node,local,stack)
            if name in CALCULUS:return self.evaluate_calculus(node,local,stack)
            args=[self.evaluate(n,local,stack) for n in node.args]
            if name in FUNCTIONS:
                result=FUNCTIONS[name](*args)
                if name!='stats' and any(isinstance(a,DataColumn) for a in args) and np.ndim(result)==1:return np.asarray(result).view(DataColumn)
                if np.ndim(result)==2 and (name in ALGEBRAIC_FUNCTIONS or any(isinstance(a,MatrixValue) for a in args)):
                    return matrix(result)
                if np.ndim(result)==1 and (name in ALGEBRAIC_FUNCTIONS or any(isinstance(a,VectorValue) for a in args)) and np.size(result)<=MAX_MATRIX:
                    return np.asarray(result).view(VectorValue)
                return result
            if name in self.functions:
                if name in stack:raise ExpressionError('Recursive functions are not supported.')
                params,tree=self.functions[name]
                if len(args)!=len(params):raise ExpressionError(f'{name} expects {len(params)} argument(s); received {len(args)}.')
                return self.evaluate(tree,dict(zip(params,args)),stack+(name,))
            raise ExpressionError(f'Unknown function: {name}')
        if isinstance(node,ast.Subscript):
            a=self.evaluate(node.value,local,stack)
            def index(n):
                v=self.evaluate(n,local,stack)
                if np.ndim(v) or int(v)!=v:raise ExpressionError('Indices must be integers (starting at 0).')
                return int(v)
            idx=tuple(index(n) for n in node.slice.elts) if isinstance(node.slice,ast.Tuple) else index(node.slice)
            return a[idx]
        raise ExpressionError('Unsupported syntax. Use numbers, variables, functions, and matrices.')

    def evaluate_reduction(self,node,local,stack):
        expression,variable,lower,upper=node.args
        if not isinstance(variable,ast.Name) or variable.id in CONSTANTS or variable.id in FUNCTIONS or variable.id in CALCULUS:
            raise ExpressionError('The sum/product index must be an unreserved variable name, such as k.')
        def limit(tree):
            value=np.asarray(self.evaluate(tree,local,stack))
            if value.ndim or np.iscomplexobj(value) and value.imag!=0 or not np.isfinite(value) or abs(value)>1e6 or float(value.real)!=int(value.real):
                raise ExpressionError('Sum/product bounds must be integers within ±1,000,000.')
            return int(value.real)
        start,end=limit(lower),limit(upper)
        if end-start+1>10000:raise ExpressionError('Limit sums and products to 10,000 terms.')
        product=node.func.id in ('product','prod');result=1 if product else 0;shape=None
        for index in range(start,end+1):
            value=self.evaluate(expression,{**local,variable.id:float(index)},stack)
            if shape is None:result=value;shape=np.shape(value);continue
            if np.shape(value)!=shape:raise ExpressionError('Sum/product terms must have a consistent shape.')
            operation=ast.Mult() if product else ast.Add()
            combine=ast.BinOp(left=ast.Name(id='_aggregate_a'),op=operation,right=ast.Name(id='_aggregate_b'))
            result=self.evaluate(combine,{'_aggregate_a':result,'_aggregate_b':value},stack)
        return result

    def evaluate_calculus(self,node,local,stack):
        name=node.func.id
        if name=='prime':
            if len(node.args) not in (2,3) or not isinstance(node.args[0],ast.Name) or node.args[0].id not in self.functions:
                raise ExpressionError("Use f'(x) for a defined one-argument function, or diff(expression, variable).")
            function=node.args[0].id;params,_=self.functions[function]
            if len(params)!=1:raise ExpressionError('Prime notation needs a one-argument function. Use diff for partial derivatives.')
            variable=ast.Name(id=params[0]);call=ast.Call(func=ast.Name(id=function),args=[variable],keywords=[])
            derivative=ast.Call(func=ast.Name(id='diff'),args=[call,variable,node.args[1],node.args[2] if len(node.args)==3 else ast.Constant(value=1)],keywords=[])
            return self.evaluate_calculus(derivative,local,stack)
        if name in MULTIVARIABLE or name == 'at':return self.evaluate_multivariable(node,local,stack)
        derivative=name in ('diff','derivative')
        primitive=name=='antiderivative'
        if len(node.args) not in ((2,3,4,5) if derivative else (2,3) if primitive else (4,5,6)):
            raise ExpressionError('Use diff(expression, variable[, point, order, step]) or integrate(expression, variable, lower, upper[, abs_tol, rel_tol]).')
        expression,variable=node.args[:2]
        if not isinstance(variable,ast.Name) or variable.id in CONSTANTS or variable.id in FUNCTIONS or variable.id in CALCULUS:
            raise ExpressionError('The calculus variable must be a variable name, for example x or θ_1.')
        if self.calculus_depth>=3:raise ExpressionError('Limit nested calculus to three operations.')
        self.calculus_depth+=1
        matrix_output=False
        vector_output=False
        def callback(value):
            nonlocal matrix_output, vector_output
            result=self.evaluate(expression,{**local,variable.id:value},stack)
            matrix_output=matrix_output or isinstance(result,MatrixValue) and result.ndim==2
            vector_output=vector_output or isinstance(result,VectorValue) and result.ndim==1
            return result
        try:
            with np.errstate(all='ignore'):
                if derivative:
                    point=self.evaluate(node.args[2],local,stack) if len(node.args)>=3 else self.evaluate(variable,local,stack)
                    order=self.evaluate(node.args[3],local,stack) if len(node.args)>=4 else 1
                    step=self.evaluate(node.args[4],local,stack) if len(node.args)>=5 else None
                    result,diagnostics=differentiate(callback,point,order,step)
                else:
                    if primitive:
                        lower=self.evaluate(node.args[2],local,stack) if len(node.args)==3 else 0.0
                        upper=self.evaluate(variable,local,stack)
                    else:
                        lower=self.evaluate(node.args[2],local,stack);upper=self.evaluate(node.args[3],local,stack)
                    abs_tol=self.evaluate(node.args[4],local,stack) if len(node.args)>=5 else 1e-8
                    rel_tol=self.evaluate(node.args[5],local,stack) if len(node.args)>=6 else 1e-7
                    result,diagnostics=integrate(callback,lower,upper,abs_tol,rel_tol)
                    if primitive:diagnostics['operation']='antiderivative'
            self.calculus_diagnostics.append(diagnostics)
            if len(self.calculus_diagnostics)>20:self.calculus_diagnostics.pop(0)
            if vector_output and result.ndim==1:return np.asarray(result).view(VectorValue)
            return matrix(result) if matrix_output and result.ndim==2 else result
        finally:
            self.calculus_depth-=1

    def calculus_variables(self, node):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            raise ExpressionError('List calculus variables explicitly, for example [x, y, z].')
        if any(not isinstance(v, ast.Name) or v.id in CONSTANTS or v.id in FUNCTIONS or v.id in CALCULUS for v in node.elts):
            raise ExpressionError('Calculus variables must be unreserved names.')
        names = [v.id for v in node.elts]
        if len(set(names)) != len(names):raise ExpressionError('Select distinct calculus variables.')
        return names

    def calculus_point(self, node, names, local, stack):
        # Read a coordinate list without treating it as a worksheet vector.
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self.evaluate(v, local, stack) for v in node.elts]
        else:
            values = self.evaluate(node, local, stack)
        a = np.asarray(values, dtype=complex)
        if a.shape != (len(names),) or not np.all(np.isfinite(a)):
            raise ExpressionError('Supply one finite scalar coordinate for every selected variable.')
        return a.real if np.all(a.imag == 0) else a

    def evaluate_multivariable(self, node, local, stack):
        name = node.func.id
        count = len(node.args)
        if count not in ((3,) if name == 'at' else (3,4,5) if name == 'directional' else (2,3,4)):
            raise ExpressionError('Use op(expression, [variables][, [point], step]); directional adds a direction before the point, and at requires a point.')
        expression = node.args[0]
        names = self.calculus_variables(node.args[1])
        point_index = 3 if name == 'directional' else 2
        point = self.calculus_point(node.args[point_index], names, local, stack) if count > point_index else np.asarray([self.evaluate(ast.Name(id=p),local,stack) for p in names], dtype=complex)
        # at is a binding operation; it does not spend a numerical nesting level.
        if name == 'at':return self.evaluate(expression, {**local, **dict(zip(names,point))}, stack)
        if self.calculus_depth >= 3:raise ExpressionError('Limit nested calculus to three operations.')
        direction = self.calculus_point(node.args[2], names, local, stack) if name == 'directional' else None
        step = self.evaluate(node.args[point_index+1], local, stack) if count > point_index+1 else None
        self.calculus_depth += 1
        try:
            result, diagnostics = multivariable(lambda p:self.evaluate(expression, {**local, **dict(zip(names,p))}, stack), point, MULTIVARIABLE[name], step, direction)
            diagnostics['variables'] = names
            self.calculus_diagnostics.append(diagnostics)
            if len(self.calculus_diagnostics) > 20:self.calculus_diagnostics.pop(0)
            if result.ndim == 2:return matrix(result)
            if result.ndim == 1:return result.view(VectorValue)
            return result
        finally:
            self.calculus_depth -= 1

    def free_names(self,node,bound=frozenset(),seen=frozenset()):
        if node is None:return set()
        if isinstance(node,ast.Name):
            if node.id in bound:return set()
            if node.id in ('x','y'):return {node.id}
            if node.id in self.definitions and node.id not in seen:
                return self.free_names(self.definitions[node.id],bound,seen|{node.id})
            return set()
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            name=node.func.id
            if name=='prime':
                names=set()
                for arg in node.args[1:]:names|=self.free_names(arg,bound,seen)
                if node.args and isinstance(node.args[0],ast.Name) and node.args[0].id in self.functions and node.args[0].id not in seen:
                    params,body=self.functions[node.args[0].id]
                    names|=self.free_names(body,bound|set(params),seen|{node.args[0].id})
                return names
            if name in REDUCTIONS and len(node.args)==4 and isinstance(node.args[1],ast.Name):
                names=self.free_names(node.args[0],bound|{node.args[1].id},seen)
                for arg in node.args[2:]:names|=self.free_names(arg,bound,seen)
                return names
            if (name in MULTIVARIABLE or name == 'at') and len(node.args)>=2 and isinstance(node.args[1],(ast.List,ast.Tuple)):
                variables={v.id for v in node.args[1].elts if isinstance(v,ast.Name)}
                names=self.free_names(node.args[0],bound|variables,seen)
                for arg in node.args[2:]:names|=self.free_names(arg,bound,seen)
                point_index=3 if name=='directional' else 2
                if len(node.args)<=point_index:
                    for v in node.args[1].elts:names|=self.free_names(v,bound,seen)
                return names
            if name in CALCULUS and len(node.args)>=2 and isinstance(node.args[1],ast.Name):
                variable=node.args[1].id
                names=self.free_names(node.args[0],bound|{variable},seen)
                for arg in node.args[2:]:names|=self.free_names(arg,bound,seen)
                if (name in ('diff','derivative') and len(node.args)==2) or name=='antiderivative':
                    names|=self.free_names(node.args[1],bound,seen)
                return names
            names=set()
            for arg in node.args:names|=self.free_names(arg,bound,seen)
            if name in self.functions and name not in seen:
                params,tree=self.functions[name]
                names|=self.free_names(tree,frozenset(params),seen|{name})
            return names
        names=set()
        for child in ast.iter_child_nodes(node):names|=self.free_names(child,bound,seen)
        return names

    def needs_pointwise(self, node, seen=frozenset()):
        """Array entries are algebraic axes, never graph-coordinate axes."""
        if isinstance(node, (ast.List, ast.Tuple)):
            return True
        if isinstance(node, ast.Name) and node.id in self.definitions and node.id not in seen:
            return self.needs_pointwise(self.definitions[node.id], seen | {node.id})
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in ALGEBRAIC_FUNCTIONS | {'summation','product','prod','quartile','quantile','stdev','stdevp','var','varp','cov','covp','mad','corr','spearman','stats','total','min','max','mexican_hat','morlet','haar','normal','poisson','binomial','boltzmann','uniform','exponential','geometric','norm', 'inner', 'det', 'trace', 'rank', 'sum', 'mean', 'ishermitian', 'isunitary'}:
                return True
            if name in self.functions and name not in seen:
                if self.needs_pointwise(self.functions[name][1], seen | {name}):
                    return True
        return any(self.needs_pointwise(child, seen) for child in ast.iter_child_nodes(node))

    def contains_calculus(self, node, seen=frozenset()):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name=node.func.id
            if name in CALCULUS:return True
            if name in self.functions and name not in seen and self.contains_calculus(self.functions[name][1], seen|{name}):return True
        if isinstance(node, ast.Name) and node.id in self.definitions and node.id not in seen:
            return self.contains_calculus(self.definitions[node.id],seen|{node.id})
        return any(self.contains_calculus(child,seen) for child in ast.iter_child_nodes(node))

    def function_slice(self, item, config):
        """Choose one/two plotted inputs; all other real inputs are held fixed."""
        params = item['params']
        if config is None:
            config = {}
        if not isinstance(config, dict) or set(config) - {'axes', 'fixed'}:
            raise ExpressionError('Plot slice must contain axes and fixed input values.')
        axes = config.get('axes', list(params[:2]))
        if not isinstance(axes, list) or not 1 <= len(axes) <= 2 or any(not isinstance(a, str) for a in axes):
            raise ExpressionError('Choose one or two input names for the plot axes.')
        axes = [normalize_notation(a.strip()) for a in axes]
        if len(set(axes)) != len(axes) or any(a not in params for a in axes):
            raise ExpressionError('Plot axes must be distinct arguments of this function.')
        values = config.get('fixed', {})
        if not isinstance(values, dict) or any(not isinstance(k, str) for k in values):
            raise ExpressionError('Fixed inputs must map argument names to real numbers.')
        fixed = {p: 0.0 for p in params if p not in axes}
        seen = set()
        for name, value in values.items():
            name = normalize_notation(name.strip())
            if name not in fixed or name in seen:
                raise ExpressionError('Fixed inputs must name unplotted arguments without duplicate aliases.')
            if type(value) not in (int, float) or not np.isfinite(value) or abs(value) > 1e6:
                raise ExpressionError('Fixed inputs must be finite real numbers within ±1,000,000.')
            seen.add(name)
            fixed[name] = value
        return {'axes': axes, 'fixed': fixed}

    def sample_algebraic(self, item, bounds, domain, curve_range, selection):
        """Bounded scalar-coordinate sampling with a constant output shape."""
        xmin, xmax, ymin, ymax = bounds
        tree = item['tree']
        params = item.get('params', ('x', 'y'))
        surface = len(params) == 2 if item['kind'] == 'function' else 'y' in self.free_names(tree)
        domain = domain and item['kind'] == 'function' and not surface
        grid = surface or domain
        grid_size = 32 if self.contains_calculus(tree) else 60
        xs = np.linspace(xmin, xmax, grid_size) if grid else np.linspace(*(curve_range or [xmin, xmax]), 1000)
        ys = np.linspace(ymin, ymax, grid_size) if grid else None
        coordinates = ((a, b) for b in ys for a in xs) if grid else ((a, None) for a in xs)
        count = len(xs) * (len(ys) if grid else 1)
        output_shape = None
        samples = None
        first_error = None
        total_steps = 0
        for index, (a, b) in enumerate(coordinates):
            self.steps = 0
            local = {**item.get('fixed', {}), params[0]: complex(a, b) if domain else a}
            if surface: local[params[1]] = b
            try:
                with np.errstate(all='ignore'):
                    value = np.asarray(self.evaluate(tree, local), dtype=complex)
            except (ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
                if isinstance(exc, ExpressionError):
                    raise
                first_error = first_error or str(exc)
                value = None
            total_steps += self.steps
            if total_steps > 2000000:
                raise ExpressionError('Function sampling limit reached; simplify the formula or plot a simpler component.')
            if value is None: continue
            if value.ndim > 2 or not value.size or (value.ndim and max(value.shape) > MAX_MATRIX):
                raise ExpressionError('Each function output must be a scalar, a vector up to 32 entries, or a matrix up to 32×32.')
            if output_shape is None:
                output_shape = value.shape
                size = value.size
                selected = selection if type(selection) is int and 0 <= selection < size else 'all'
                indices = [selected] if selected != 'all' else list(range(min(size, 1 if grid else 8)))
                samples = np.full((len(indices), count), np.nan, dtype=complex)
            elif value.shape != output_shape:
                raise ExpressionError('Function output shape changes across the input range; use a fixed-size vector or matrix.')
            samples[:, index] = value.reshape(-1)[indices]
        if output_shape is None:
            raise ExpressionError(first_error or 'Function is undefined throughout this input range.')
        components = []
        for k, flat_index in enumerate(indices):
            value = samples[k].reshape((len(ys), len(xs)) if grid else (len(xs),))
            valid = np.isfinite(value)
            value = np.where(valid, value, complex(np.nan, np.nan))
            result = {'x': xs.tolist(), 'complex': bool(np.any(valid & (value.imag != 0)))}
            if grid:
                result.update(kind='complex_field' if domain else 'surface', y=ys.tolist(),
                              real=clean(value.real), imag=clean(value.imag), magnitude=clean(np.abs(value)), phase=clean(phase(value)))
            else:
                real, imag = value.real.copy(), value.imag.copy()
                for part in (real, imag):
                    part[np.flatnonzero(np.abs(np.diff(part)) > 2*(ymax-ymin))] = np.nan
                result.update(kind='complex_curve' if result['complex'] else 'curve', y=clean(real),
                              imag=clean(imag), magnitude=clean(np.abs(value)), phase=clean(phase(value)))
            if output_shape:
                entry = list(np.unravel_index(flat_index, output_shape))
                result.update(index=flat_index, label='[' + ', '.join(str(i) for i in entry) + ']')
            components.append(result)
        out = dict(components[0])
        out.update(name=item.get('name'), parameters=list(params if surface else params[:1]))
        if output_shape:
            out.update(shape=list(output_shape), components=components, component_count=int(np.prod(output_shape)),
                       selected_component=selected, sampled_pointwise=True)
        return out

    def run(self,bounds,complex_domain=False,curve_range=None):
        xmin,xmax,ymin,ymax=bounds
        x=np.linspace(*(curve_range or [xmin,xmax]),1000)
        gx=np.linspace(xmin,xmax,180);gy=np.linspace(ymin,ymax,180)
        xx,yy=np.meshgrid(gx,gy)
        results=[]
        for row_index, item in enumerate(self.items):
            self.steps=0
            self.calculus_diagnostics=[]
            self.calculus_depth=0
            out={'text':item['text'],'kind':item['kind']}
            if item['kind']=='function':out['function']={'name':item['name'],'parameters':list(item['params']),'body':item['body']}
            if item.get('error'):
                results.append({**out,'error':item['error']});continue
            if item.get('tree') is None:
                results.append({**out,'kind':'empty'});continue
            try:
                tree=item['tree'];kind=item['kind'];names=self.free_names(tree)
                # A bare d/dt(C(t)) can plot t without creating a t slider.
                if kind=='value' and isinstance(tree,ast.Call) and isinstance(tree.func,ast.Name) and tree.func.id in ('diff','derivative','antiderivative','prime') and len(tree.args)>=2 and isinstance(tree.args[1],ast.Name):
                    variable=tree.args[1].id
                    current_point=tree.func.id in ('antiderivative','prime') or len(tree.args)==2 or (len(tree.args)>=3 and isinstance(tree.args[2],ast.Name) and tree.args[2].id==variable)
                    if current_point and variable not in ('x','y') and not names and variable not in self.definitions and variable not in self.dataset_values and variable not in CONSTANTS:
                        item={**item,'kind':'function','params':(variable,)};kind='function';out['plot_parameters']=[variable]

                if kind=='function':
                    names=self.free_names(tree,frozenset(item['params']))|{'x'}
                    plot_slice = self.function_slice(item, self.rows[row_index].get('plot_slice'))
                    out['plot_slice'] = plot_slice
                    item = {**item, 'params': tuple(plot_slice['axes']), 'fixed': plot_slice['fixed']}
                if kind not in ('implicit', 'inequality') and (kind in ('explicit', 'function') or names) and self.needs_pointwise(tree):
                    out.update(self.sample_algebraic(item, bounds, complex_domain, curve_range, self.rows[row_index].get('plot_component', 'all')))
                elif (kind=='function' and len(item['params'])==2) or (kind=='value' and 'y' in names):
                    local={**item.get('fixed', {}), **dict(zip(item['params'],(xx,yy)))} if kind=='function' else {'x':xx,'y':yy}
                    with np.errstate(all='ignore'):field=complex_plot(self.evaluate(tree,local),xx.shape)
                    valid=np.isfinite(field)
                    out.update(kind='surface',name=item.get('name'),parameters=list(item.get('params',('x','y'))),x=gx.tolist(),y=gy.tolist(),
                               real=clean(np.where(valid,field.real,np.nan)),imag=clean(np.where(valid,field.imag,np.nan)),
                               magnitude=clean(np.abs(field)),phase=clean(phase(field)),complex=bool(np.any(valid & (field.imag!=0))))
                elif kind=='function' and complex_domain:
                    with np.errstate(all='ignore'):
                        field=complex_plot(self.evaluate(tree,{**item.get('fixed', {}),item['params'][0]:xx+1j*yy}),xx.shape)
                    out.update(kind='complex_field', name=item['name'], x=gx.tolist(), y=gy.tolist(), magnitude=clean(np.abs(field)), phase=clean(phase(field)))
                elif kind in ('implicit','inequality') or 'y' in names:
                    with np.errstate(all='ignore'):z=self.evaluate(tree,{'x':xx,'y':yy})
                    z=real_plot(z,(180,180))
                    out.update(kind='inequality' if kind=='inequality' else 'implicit',x=gx.tolist(),y=gy.tolist(),z=clean(z))
                elif kind in ('explicit','function') or 'x' in names:
                    local={'x':x}
                    if kind=='function':local={**item.get('fixed', {}),item['params'][0]:x}
                    with np.errstate(all='ignore'):v=self.evaluate(tree,local)
                    v=complex_plot(v,(1000,))
                    is_complex=bool(np.any(np.isfinite(v) & (v.imag != 0)))
                    re,im=v.real.copy(),v.imag.copy()
                    invalid=~np.isfinite(v)
                    re[invalid]=np.nan;im[invalid]=np.nan
                    # Break common poles without modifying the underlying complex values.
                    for component in (re,im):
                        jumps=np.flatnonzero(np.abs(np.diff(component))>2*(ymax-ymin))
                        component[jumps]=np.nan
                    out.update(kind='complex_curve' if is_complex else 'curve',x=x.tolist(),y=clean(re))
                    if is_complex:out.update(imag=clean(im),magnitude=clean(np.abs(v)),phase=clean(phase(v)))
                else:
                    with np.errstate(all='ignore'):v=self.evaluate(tree)
                    if isinstance(v,(wavelets.DiscreteTransform,wavelets.ContinuousTransform)):
                        out.update(kind='wavelet_transform',name=item.get('name'),transform=wavelets.transform_summary(v))
                        results.append(out);continue
                    if isinstance(v, probability.Distribution):
                        out.update(kind='distribution',name=item.get('name'),distribution=probability.describe(v))
                        results.append(out);continue
                    if isinstance(v, PointSeries):
                        valid=np.isfinite(v.x)&np.isfinite(v.y)
                        out.update(kind='data_plot',x=clean(np.where(valid,v.x,np.nan)),y=clean(np.where(valid,v.y.real,np.nan)),imag=clean(np.where(valid,v.y.imag,np.nan)),complex=bool(np.any(valid & (v.y.imag!=0))))
                        results.append(out);continue
                    a=np.asarray(v)
                    if isinstance(v,DataColumn) and a.ndim==1:
                        if a.size>dataset_math.MAX_ROWS:raise ExpressionError('Dataset results support at most 10,000 observations.')
                        valid=np.isfinite(a)
                        out.update(kind='series',name=item.get('name'),shape=list(a.shape),count=int(np.count_nonzero(valid)),missing=int(np.count_nonzero(~valid)),
                                   value=[display(np.asarray(z)) if np.isfinite(z) else None for z in a[:12]],
                                   real=clean(np.where(valid,a.real,np.nan)),imag=clean(np.where(valid,a.imag,np.nan)),complex=bool(np.any(valid & (a.imag!=0))))
                        results.append(out);continue
                    if not np.all(np.isfinite(a)):raise ExpressionError('Result is undefined or non-finite.')
                    out.update(kind='scalar' if a.ndim==0 else 'vector' if a.ndim==1 else 'matrix',value=display(a),shape=list(a.shape))
                    out.update(real=clean(a.real),imag=clean(a.imag),magnitude=clean(np.abs(a)),phase=clean(phase(a)),complex=bool(np.any(a.imag != 0)))
                    if a.ndim==0 and a.imag==0:out['numeric']=float(a.real)
                    if a.ndim==2:
                        a=matrix(a)
                        out['real']=clean(np.real(a));out['complex']=bool(np.any(np.imag(a)!=0))
                        if not a.size:out['empty_basis']=True
                        if a.size and a.shape[0]==a.shape[1]:
                            out['hermitian']=bool(np.allclose(a,a.conj().T,atol=1e-10,rtol=1e-8))
                            out['unitary']=bool(np.allclose(a.conj().T@a,np.eye(len(a)),atol=1e-10,rtol=1e-8))
                            out['details']={'det':display(np.asarray(np.linalg.det(a))),'trace':display(np.asarray(np.trace(a))),'rank':int(np.linalg.matrix_rank(a)),'eigenvalues':display(linear_algebra.eigenpairs(a)[0])}
                    if a.ndim in (1,2):
                        info=quantum.quantum_info(a)
                        if info is not None:out['quantum']=info
                    if kind=='definition':out['name']=item['name']
            except (Exception,RecursionError) as exc:
                out['error']=str(exc) or type(exc).__name__
            if self.calculus_diagnostics:out['calculus']=self.calculus_diagnostics
            results.append(out)
        return results

def complex_plot(value,shape):
    try:return np.array(np.broadcast_to(np.asarray(value),shape),dtype=complex)
    except ValueError as exc:raise ExpressionError('Expected one scalar value for each graph coordinate.') from exc

def real_plot(value,shape):
    a=np.asarray(value)
    if np.iscomplexobj(a) and np.any(np.abs(a.imag)>1e-10):
        raise ExpressionError('Graphs need real values. Use real(...) or imag(...).')
    try:return np.array(np.broadcast_to(a.real,shape),dtype=float)
    except ValueError as exc:raise ExpressionError('Expected one real value for each graph coordinate.') from exc

def clean(a):
    return np.where(np.isfinite(a),a,None).tolist()

def display(a):
    if a.ndim:return [display(np.asarray(v)) for v in a]
    z=complex(a)
    if z.imag==0:return float(z.real)
    return f'{z.real:.7g}{z.imag:+.7g}i'
