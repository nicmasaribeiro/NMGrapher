"""Presentation MathML trees from the same restricted syntax used for evaluation."""
import ast
import re
from engine import parse
from notation import normalize_notation


def element(tag, *children, text=None, **attrs):
    node={'tag':tag}
    if children:node['children']=list(children)
    if text is not None:node['text']=str(text)
    if attrs:node['attrs']=attrs
    return node


def row(*children):return element('mrow',*children)
def op(text):return element('mo',text=text)
def fenced(node, left='(',right=')'):return row(op(left),node,op(right))
def joined(nodes, separator=','):return row(*[item for i,node in enumerate(nodes) for item in ([op(separator),node] if i else [node])])


def name(value, upright=False):
    if '_' in value:
        base,index=value.split('_',1)
        return element('msub',name(base,upright),element('mn' if index.isdecimal() else 'mi',text=index))
    return element('mi',text=value,**({'mathvariant':'normal'} if upright else {}))


def same(a,b):return ast.dump(a)==ast.dump(b)


def known_ket_label(node):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
        function=node.func.id;args=node.args
        if function=='ket' and len(args)==1:return render(args[0])
        labels={'ket0':'0','ket1':'1','ketplus':'+','ketminus':'−','ketplusi':'+i','ketminusi':'−i'}
        if function in labels and not args:return element('mi',text=labels[function])
        if function=='ketbasis' and len(args) in (1,2) and all(isinstance(a,ast.Constant) and type(a.value) is int for a in args):
            index=args[0].value;count=args[1].value if len(args)==2 else 1
            if 1<=count<=5 and 0<=index<2**count:return element('mn',text=format(index,f'0{count}b'))
    return None


def ket_label(node):
    label=known_ket_label(node)
    return label if label is not None else render(node)

def at_point(value,variables,points):
    vs=variables.elts if isinstance(variables,(ast.List,ast.Tuple)) else [variables]
    ps=points.elts if isinstance(points,(ast.List,ast.Tuple)) else [points]
    if len(vs)!=len(ps):return row(value,op('|'),fenced(render(points)))
    conditions=joined([row(render(v),op('='),render(p)) for v,p in zip(vs,ps)])
    return row(fenced(value),element('msub',op('|'),conditions))


def render(node, parent=0):
    if isinstance(node,ast.Constant) and type(node.value) in (int,float,complex):
        return element('mn',text=str(node.value).replace('j','i'))
    if isinstance(node,ast.Name):return name(node.id)
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        result=row(op('−' if isinstance(node.op,ast.USub) else '+'),render(node.operand,25))
        return fenced(result) if parent>25 else result
    if isinstance(node,ast.BinOp):
        if isinstance(node.op,ast.Pow):return element('msup',render(node.left,31),render(node.right))
        if isinstance(node.op,ast.Div):return element('mfrac',render(node.left),render(node.right))
        symbols={ast.Add:'+',ast.Sub:'−',ast.Mult:'·',ast.MatMult:'·',ast.Mod:'mod'}
        if type(node.op) not in symbols:raise ValueError('Unsupported math operator.')
        precedence=10 if isinstance(node.op,(ast.Add,ast.Sub)) else 20
        result=row(render(node.left,precedence),op(symbols[type(node.op)]),render(node.right,precedence+1))
        return fenced(result) if parent>precedence else result
    if isinstance(node,(ast.List,ast.Tuple)):
        if node.elts and all(isinstance(n,(ast.List,ast.Tuple)) for n in node.elts):
            table=element('mtable',*[element('mtr',*[element('mtd',render(c)) for c in n.elts]) for n in node.elts])
            return fenced(table,'[',']')
        return fenced(joined([render(n) for n in node.elts]),'[',']')
    if isinstance(node,ast.Subscript):return row(render(node.value),fenced(joined([render(v) for v in node.slice.elts]) if isinstance(node.slice,ast.Tuple) else render(node.slice), '[',']'))
    if isinstance(node,ast.Compare):
        symbols={ast.Lt:'<',ast.LtE:'≤',ast.Gt:'>',ast.GtE:'≥',ast.Eq:'=',ast.NotEq:'≠'}
        parts=[render(node.left)]
        for operation,right in zip(node.ops,node.comparators):parts.extend([op(symbols[type(operation)]),render(right)])
        return row(*parts)
    if isinstance(node,ast.Attribute):
        from probability import METHODS
        if node.attr not in METHODS:raise ValueError('Unsupported distribution operation.')
        return row(render(node.value),op('.'),name(node.attr,True))
    if isinstance(node,ast.Call) and not isinstance(node.func,ast.Name) and not node.keywords:
        return row(render(node.func),fenced(joined([render(a) for a in node.args])))
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
        function=node.func.id;args=node.args
        if function in ('field_gradient','field_jacobian','field_hessian','field_divergence','field_curl','field_laplacian','force') and len(args) in (2,3):
            source=render(args[0])
            if function=='field_jacobian':symbol=element('msub',name('J'),source)
            elif function=='field_hessian':symbol=element('msub',name('H'),source)
            elif function=='field_laplacian':symbol=row(element('msup',op('∇'),element('mn',text='2')),source)
            else:symbol=row(*( [op('−')] if function=='force' else []),op('∇'),*( [op('·')] if function=='field_divergence' else [op('×')] if function=='field_curl' else []),source)
            return row(fenced(symbol),fenced(render(args[1])))
        if function=='work' and 4<=len(args)<=6:
            parameter=name('t');path=row(render(args[1]),fenced(parameter))
            integrand=row(render(args[0]),fenced(path),op('·'),element('msup',render(args[1]),op('′')),fenced(parameter))
            return row(element('msubsup',op('∫'),render(args[2]),render(args[3])),integrand,name('d',True),parameter)
        if function=='ket' and len(args)==1:return fenced(render(args[0]),'|','⟩')
        if function in ('ketbasis','ket0','ket1','ketplus','ketminus','ketplusi','ketminusi'):
            label=known_ket_label(node)
            if label is not None:return fenced(label,'|','⟩')
        if function=='bra' and len(args)==1:return fenced(ket_label(args[0]),'⟨','|')
        if function=='braket' and len(args)==2:return row(op('⟨'),ket_label(args[0]),op('|'),ket_label(args[1]),op('⟩'))
        if function=='ketbra' and len(args)==2:return row(fenced(ket_label(args[0]),'|','⟩'),fenced(ket_label(args[1]),'⟨','|'))
        if function=='matrix_element' and len(args)==3:return row(op('⟨'),ket_label(args[0]),op('|'),render(args[1]),op('|'),ket_label(args[2]),op('⟩'))
        if function in ('tensor','kron') and len(args)==2:
            return row(render(args[0],21),op('⊗'),render(args[1],21))
        if function in ('sum','summation','product','prod') and len(args)==4:
            symbol=element('msubsup',op('∏' if function in ('product','prod') else '∑'),row(render(args[1]),op('='),render(args[2])),render(args[3]))
            value=row(symbol,fenced(render(args[0])))
            return fenced(value) if parent else value
        if function=='prime' and len(args) in (2,3):
            order=args[2].value if len(args)==3 and isinstance(args[2],ast.Constant) else 1
            return row(element('msup',render(args[0]),op('″' if order==2 else '′')),fenced(render(args[1])))
        if function=='logbase' and len(args)==2:return row(element('msub',name('log',True),render(args[1])),fenced(render(args[0])))
        if function in ('integrate','integral') and 4<=len(args)<=6:
            if isinstance(args[1],(ast.List,ast.Tuple)):
                from engine import Calculator
                return render(Calculator([]).expand_integral(node),parent)
            symbol=element('msubsup',op('∫'),render(args[2]),render(args[3]))
            value=row(symbol,render(args[0]),element('mspace',width='0.2em'),name('d',True),render(args[1]))
            return fenced(value) if parent else value
        if function=='antiderivative' and len(args) in (2,3):
            symbol=element('msubsup',op('∫'),render(args[2]) if len(args)==3 else element('mn',text='0'),render(args[1]))
            value=row(symbol,render(args[0]),element('mspace',width='0.2em'),name('d',True),render(args[1]))
            return fenced(value) if parent else value
        if function in ('diff','derivative') and 2<=len(args)<=5:
            order=args[3] if len(args)>=4 else ast.Constant(value=1)
            second=isinstance(order,ast.Constant) and order.value==2
            if not (isinstance(order,ast.Constant) and order.value in (1,2)):
                return row(name(function,True),fenced(joined([render(a) for a in args])))
            numerator=element('msup',name('d',True),element('mn',text='2')) if second else name('d',True)
            denominator=row(name('d',True),element('msup',render(args[1]),element('mn',text='2')) if second else render(args[1]))
            value=row(element('mfrac',numerator,denominator),fenced(render(args[0])))
            if len(args)>=3 and not same(args[1],args[2]):value=at_point(value,args[1],args[2])
            return fenced(value) if parent else value
        if function=='at' and len(args)==3:return at_point(render(args[0]),args[1],args[2])
        if function=='sqrt' and len(args)==1:return element('msqrt',render(args[0]))
        if function=='exp' and len(args)==1:return element('msup',name('e'),render(args[0]))
        if function=='abs' and len(args)==1:return fenced(render(args[0]),'|','|')
        return row(name(function,function in {'sin','cos','tan','log','ln','expm','real','imag','conj','det','trace','norm'}),fenced(joined([render(a) for a in args])))
    raise ValueError('Incomplete or unsupported expression.')


def preview(source):
    normalized=normalize_notation(source.strip(),preserve_ket_lhs=True)
    if not normalized:return {'tree':row()}
    def line_preview(line):
        pieces=re.split(r'(?<![<>=!])=(?!=)',line)
        return joined([render(parse(piece)) for piece in pieces],'=')
    try:return {'tree':line_preview(normalized)}
    except ValueError:
        if '\n' not in normalized:raise
    lines=[line_preview(line) for line in normalized.splitlines() if line.strip()]
    return {'tree':element('mtable',*[element('mtr',element('mtd',n)) for n in lines])}
