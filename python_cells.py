"""Compile a bounded mathematical Python subset to the calculator's numeric AST.

Never executes Python, imports modules, or exposes Python objects to user code.
"""
import ast
import copy
import keyword


class PythonCellError(ValueError):pass


def compile_cell(source, reserved):
    try: module=ast.parse(source)
    except SyntaxError as exc:raise PythonCellError(f'Python line {exc.lineno}: {exc.msg}') from exc
    if len(source)>1200 or sum(1 for _ in ast.walk(module))>400:
        raise PythonCellError('Python cell exceeds the 1200-character / 400-node limit.')
    exports=[];aliases={};work=[0]
    def name(n, local=False):
        if not isinstance(n,str) or not n.isidentifier() or n.startswith('_') or keyword.iskeyword(n) or (n in reserved and not local):
            raise PythonCellError(f'Invalid or reserved Python name: {n}')
        return n
    class Expression(ast.NodeTransformer):
        def __init__(self, env):self.env=env
        def visit_Name(self,node):
            if node.id.startswith('_'):raise PythonCellError('Private names are not supported.')
            return copy.deepcopy(self.env.get(node.id,node))
        def visit_Attribute(self,node):
            if isinstance(node.value,ast.Name) and node.value.id in aliases:
                mapping={'array':'array','asarray':'array','pi':'pi','e':'e','arcsin':'asin','arccos':'acos','arctan':'atan'}
                target=mapping.get(node.attr,node.attr)
                if target not in reserved:raise PythonCellError(f'Unsupported mathematical function: {node.attr}')
                return ast.Name(id=target,ctx=ast.Load())
            if node.attr.startswith('_'):raise PythonCellError('Private attributes are not supported.')
            return self.generic_visit(node)
    allowed=(ast.Constant,ast.Name,ast.Load,ast.List,ast.Tuple,ast.BinOp,ast.UnaryOp,ast.Compare,ast.Call,ast.Attribute,ast.Subscript,ast.IfExp,ast.BoolOp,
             ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow,ast.MatMult,ast.Mod,ast.UAdd,ast.USub,ast.Not,ast.And,ast.Or,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq)
    def expr(node,env):
        out=Expression(env).visit(copy.deepcopy(node))
        nodes=list(ast.walk(out));work[0]+=len(nodes)
        if len(nodes)>4000 or work[0]>20000:raise PythonCellError('Python expansion is too complex; reduce loop count or intermediate expressions.')
        for child in nodes:
            if not isinstance(child,allowed):raise PythonCellError(f'Unsupported Python expression: {type(child).__name__}')
            if isinstance(child,ast.Constant) and type(child.value) not in (int,float,complex,bool):raise PythonCellError('Only numeric Python values are supported.')
        return out
    def block(statements,env,need_return=False):
        env=dict(env)
        for index,s in enumerate(statements):
            if isinstance(s,ast.Assign) and len(s.targets)==1 and isinstance(s.targets[0],ast.Name):
                env[name(s.targets[0].id,True)]=expr(s.value,env)
            elif isinstance(s,ast.AugAssign) and isinstance(s.target,ast.Name):
                if s.target.id not in env:raise PythonCellError('Assign a local value before updating it.')
                env[name(s.target.id,True)]=expr(ast.BinOp(left=ast.Name(id=s.target.id),op=s.op,right=s.value),env)
            elif isinstance(s,ast.Return) and need_return:
                if s.value is None:raise PythonCellError('Return a numeric expression.')
                return env,expr(s.value,env)
            elif isinstance(s,ast.If):
                test=expr(s.test,env)
                left,lr=block(s.body,env,need_return);right,rr=block(s.orelse,env,need_return)
                if lr is not None or rr is not None:
                    if lr is None:_,lr=block(statements[index+1:],left,need_return)
                    if rr is None:_,rr=block(statements[index+1:],right,need_return)
                    if lr is None or rr is None:raise PythonCellError('Every function branch must return a value.')
                    return env,expr(ast.IfExp(test=test,body=lr,orelse=rr),{})
                for key in left.keys()|right.keys():
                    if key not in left or key not in right:raise PythonCellError('Assign branch variables in both branches.')
                    env[key]=expr(ast.IfExp(test=test,body=left[key],orelse=right[key]),{})
            elif isinstance(s,ast.For) and isinstance(s.target,ast.Name) and isinstance(s.iter,ast.Call) and isinstance(s.iter.func,ast.Name) and s.iter.func.id=='range' and not s.iter.keywords and not s.orelse:
                args=[]
                for arg in s.iter.args:
                    a=expr(arg,env)
                    if isinstance(a,ast.UnaryOp) and isinstance(a.op,ast.USub) and isinstance(a.operand,ast.Constant):a=ast.Constant(value=-a.operand.value)
                    if not isinstance(a,ast.Constant) or type(a.value) is not int:raise PythonCellError('range bounds must be literal integers or assigned integer constants.')
                    args.append(a.value)
                if not 1<=len(args)<=3:raise PythonCellError('Use range(stop) or range(start, stop[, step]).')
                try: values=range(*args)
                except ValueError as exc:raise PythonCellError(str(exc)) from exc
                if len(values)>32:raise PythonCellError('Python loops support at most 32 iterations.')
                for value in values:
                    env[name(s.target.id,True)]=ast.Constant(value=value)
                    env,ret=block(s.body,env,False)
            elif isinstance(s,ast.Pass):continue
            else:raise PythonCellError(f'Python line {s.lineno}: unsupported {type(s).__name__}. Use assignments, def, if, return, and bounded for loops.')
        return env,None
    topenv={}
    for s in module.body:
        if isinstance(s,ast.Import):
            for item in s.names:
                if item.name not in ('numpy','math'):raise PythonCellError('Only mathematical numpy/math aliases are supported; arbitrary imports are unavailable.')
                alias=item.asname or item.name
                name(alias);aliases[alias]=item.name
        elif isinstance(s,ast.FunctionDef):
            name(s.name);a=s.args
            if s.decorator_list or s.returns or a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or a.defaults or any(p.annotation for p in a.args):raise PythonCellError('Use plain named function parameters without decorators, annotations, or defaults.')
            params=tuple(name(p.arg) for p in a.args)
            if not params or len(set(params))!=len(params):raise PythonCellError('Use distinct named parameters.')
            _,result=block(s.body,{p:ast.Name(id=p) for p in params},True)
            if result is None:raise PythonCellError(f'Function {s.name} needs return.')
            exports.append((s.name,params,result))
        else:
            topenv,_=block([s],topenv,False)
    exports.extend((name(key),None,value) for key,value in topenv.items())
    if len(exports)>40 or len({n for n,_,_ in exports})!=len(exports):raise PythonCellError('Use at most 40 distinct exported names per cell; put repeated updates inside a function.')
    return exports
