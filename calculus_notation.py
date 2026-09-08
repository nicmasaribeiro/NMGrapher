"""Translate a small, explicit calculus notation into restricted calculator calls."""
import re
from symbols import GREEK_KEYWORDS

NAME = r'[^\W\d]\w*(?:_\{[^{}]+\})?'
DERIVATIVE = re.compile(r'(?<![\w])d\s*(?P<order>²|\^\{?2\}?)?\s*/\s*d\s*(?P<variable>'+NAME+r')')
DIFFERENTIAL = re.compile(r'd\s*('+NAME+r')')


def differential_at(text, position):
    # Adjacent one-letter differentials (dydx, dzdydx), plus delimited
    # multiletter/subscript names such as dtheta_1 or d x_1.
    match=DIFFERENTIAL.match(text,position)
    if not match:return None
    variable=match[1]
    if re.fullmatch(r'[^\W\d](?:d[^\W\d])+',variable):
        return variable[0], position+2
    return variable,match.end()


def skip_space(text, position):
    while position < len(text) and text[position].isspace(): position += 1
    return position


def group(text, position):
    if position >= len(text) or text[position] not in '({[':
        raise ValueError('Put the calculus operand in parentheses, for example d/dx(f(x)).')
    stack=[];start=position
    pairs={')':'(', '}':'{', ']':'['}
    while position<len(text):
        char=text[position]
        if char in '({[': stack.append(char)
        elif char in ')}]':
            if not stack or stack.pop()!=pairs[char]:raise ValueError('Check matching brackets in the calculus expression.')
            if not stack:return text[start+1:position],position+1
        position+=1
    raise ValueError('Close the parentheses or braces in the calculus expression.')


def bound(text, position):
    position=skip_space(text,position)
    if position<len(text) and text[position] in '{(':
        value,end=group(text,position)
    else:
        match=re.match(r'[+-]?(?:\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|'+NAME+r')',text[position:])
        if not match:raise ValueError('Specify an integral bound; use braces for compound bounds.')
        value=match[0];end=position+len(value)
    if not value.strip():raise ValueError('Integral bounds cannot be empty.')
    return value,end


def integral_at(text, start, depth):
    if depth>20:raise ValueError('Calculus notation is nested too deeply.')
    position=skip_space(text,start+1);lower=upper=None
    if position<len(text) and text[position]=='_':
        lower,position=bound(text,position+1);position=skip_space(text,position)
        if position>=len(text) or text[position]!='^':raise ValueError('A definite integral needs both lower and upper bounds: ∫_{0}^{x} (f(t)) dt.')
        upper,position=bound(text,position+1)
    body_start=skip_space(text,position);position=body_start;stack=[];nested_end=None
    pairs={')':'(', '}':'{', ']':'['}
    while position<len(text):
        char=text[position]
        if not stack and char=='∫':
            _,position=integral_at(text,position,depth+1);nested_end=position;continue
        if not stack and char=='d' and (position==body_start or position==nested_end or text[position-1].isspace() or text[position-1] in ')]}'):
            match=differential_at(text,position)
            if match:
                variable,end=match;after=skip_space(text,end)
                if after==len(text) or text[after] in '+-*/@,)]}' or (text[after]=='d' and differential_at(text,after)):
                    body=text[body_start:position].strip()
                    if not body:raise ValueError('An integral needs an integrand before its differential.')
                    body=normalize_calculus(body,depth+1)
                    if lower is None:return f'antiderivative({body}, {variable})',end
                    return f'integrate({body}, {variable}, {normalize_calculus(lower,depth+1)}, {normalize_calculus(upper,depth+1)})',end
        if char in '({[':stack.append(char)
        elif char in ')}]':
            if not stack:break
            if stack.pop()!=pairs[char]:raise ValueError('Check matching brackets in the integral.')
        position+=1
    raise ValueError('End the integral with its differential, for example ∫_{0}^{x} (f(t)) dt.')



def operator_operand(text,position):
    if position>=len(text):raise ValueError('Enter an expression after the calculus operator.')
    if text[position] in '({[':return group(text,position)
    start=position;stack=[];pairs={')':'(',']':'[','}':'{'}
    while position<len(text):
        char=text[position]
        if not stack and (char in ',)]}' or (char=='d' and position>start and (text[position-1].isspace() or text[position-1] in ')]}') and differential_at(text,position))):break
        if char in '([{':stack.append(char)
        elif char in ')]}':
            if not stack or stack.pop()!=pairs[char]:raise ValueError('Check matching brackets in the operator operand.')
        position+=1
    operand=text[start:position].strip()
    if not operand:raise ValueError('Enter an expression after the calculus operator.')
    return operand,position


def normalize_calculus(text, depth=0):
    if depth>20:raise ValueError('Calculus notation is nested too deeply.')
    # Common pasted notation only; this is not a general LaTeX interpreter.
    text=re.sub(r'\\(int|sum|prod)(?![A-Za-z])',lambda m:{'int':'∫','sum':'∑','prod':'∏'}[m[1]],text)
    text=re.sub(r'\\(left|right)\b','',text)
    text=text.replace(r'\cdot','*').replace(r'\,',' ')
    text=re.sub(r'\\([A-Za-z]+)(?![A-Za-z])',lambda m:GREEK_KEYWORDS.get(m[1].lower(),m[0]),text)
    text=re.sub(r'\\frac\s*\{d\}\s*\{d\s*('+NAME+r')\}',lambda m:'d/d'+m[1],text)
    output=[];position=0
    while position<len(text):
        if text[position] in '∑Σ∏Π' and re.match(r'\s*_\s*[{(][^{}()]*=',text[position+1:]):
            value,position=aggregate_at(text,position,depth);output.append(value);continue
        if text[position]=='∫':
            value,position=integral_at(text,position,depth);output.append(value);continue
        match=DERIVATIVE.match(text,position)
        if match:
            variable=match['variable'];order=2 if match['order'] else 1;end=match.end()
            if order==2:
                if variable.endswith('²'):variable=variable[:-1]
                else:
                    power=re.match(r'\s*\^\{?2\}?',text[end:])
                    if not power:raise ValueError('Write second derivatives as d^2/dx^2(expression).')
                    end+=len(power[0])
            elif variable.endswith('²'):
                raise ValueError('Derivative orders in the numerator and denominator must match.')
            end=skip_space(text,end)
            operand,end=operator_operand(text,end)
            operand=normalize_calculus(operand,depth+1)
            output.append(f'diff({operand}, {variable}'+(f', {variable}, 2)' if order==2 else ')'))
            position=end;continue
        output.append(text[position]);position+=1
    return normalize_function_notation(''.join(output))


def aggregate_at(text,start,depth):
    position=skip_space(text,start+1)
    lower,position=bound(text,position+1)
    match=re.fullmatch(r'\s*('+NAME+r')\s*=\s*(.+)',lower,re.S)
    if not match:raise ValueError('Write the index and starting value, for example ∑_{k=1}^{5}(k^2).')
    variable,lower=match.groups();position=skip_space(text,position)
    if position>=len(text) or text[position]!='^':raise ValueError('A sum/product needs an upper bound.')
    upper,position=bound(text,position+1);position=skip_space(text,position)
    body,end=operator_operand(text,position)
    function='summation' if text[start] in '∑Σ' else 'product'
    return f'{function}({normalize_calculus(body,depth+1)}, {variable}, {normalize_calculus(lower,depth+1)}, {normalize_calculus(upper,depth+1)})',end


def normalize_function_notation(text,depth=0):
    if depth>20:raise ValueError('Function notation is nested too deeply.')
    output=[];position=0
    prime=re.compile(r'('+NAME+r")\s*(''|'|′|″|’)\s*(?=\()")
    while position<len(text):
        if position==0 or not (text[position-1].isalnum() or text[position-1]=='_'):
            if text.startswith('log_',position):
                base,end=bound(text,position+4);end=skip_space(text,end)
                if end<len(text) and text[end]=='(':
                    operand,end=group(text,end)
                    output.append(f'logbase({normalize_function_notation(operand,depth+1)}, {normalize_function_notation(base,depth+1)})');position=end;continue
            match=prime.match(text,position)
            if match:
                body,end=group(text,match.end());order=2 if match[2] in ("''",'″') else 1
                output.append(f'prime({match[1]}, ({normalize_function_notation(body,depth+1)}), {order})');position=end;continue
        output.append(text[position]);position+=1
    return ''.join(output)
