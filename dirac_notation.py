"""Translate bounded Dirac notation to the calculator's restricted AST calls.

Kets are column vectors, bras are conjugate rows. No Python code is evaluated
here. ASCII angle delimiters are recognized only where an operand may begin.
"""
import re

RIGHT = '⟩〉>'
LEFT = '⟨〈<'


def _delimiter(text, start, choices):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for i in range(start, len(text)):
        c = text[i]
        if not stack and c in choices:
            return i
        if c in '([{':
            stack.append(c)
        elif c in ')]}':
            if not stack or stack.pop() != pairs[c]:
                return None
        elif not stack and c in LEFT:
            return None
    return None


def _state(label):
    label = label.strip()
    if not label:
        raise ValueError('A ket or bra needs a state label, such as |0⟩ or |ψ⟩.')
    bits = re.sub(r'\s+', '', label)
    if bits.isdecimal():
        if not re.fullmatch('[01]{1,5}', bits):
            raise ValueError('Basis kets use 1–5 binary digits, for example |0⟩ or |101⟩. Use basis(index, qubits) for a decimal index.')
        return f'ketbasis({int(bits, 2)},{len(bits)})'
    special = {'+': 'ketplus', '-': 'ketminus', '−': 'ketminus',
               '+i': 'ketplusi', '-i': 'ketminusi', '−i': 'ketminusi'}
    if bits in special:
        return special[bits] + '()'
    if any(c in label for c in '|⟨⟩〈〉'):
        raise ValueError('Use a named state or an amplitude vector inside a ket.')
    return f'ket({label})'


def _atom(text, start):
    """Return (kind, code, state-code, raw-label, end) or None."""
    c = text[start]
    if c == '|':
        end = _delimiter(text, start + 1, RIGHT + '|')
        if end is None or text[end] == '|':
            raise ValueError('Close the ket with ⟩ or >, for example |ψ⟩. Use abs(x) for absolute values.')
        label = text[start + 1:end]
        state = _state(label)
        return 'ket', state, state, label, end + 1
    if c not in LEFT:
        return None
    if c == '<':
        previous = text[:start].rstrip()
        if previous and previous[-1] not in '(,=+-*/@⟩〉>':
            return None  # Preserve ordinary inequalities such as x < y.
    bar = _delimiter(text, start + 1, '|')
    if bar is None:
        if c == '<':
            return None
        raise ValueError('Close a bra with |, for example ⟨ψ|.')
    label = text[start + 1:bar]
    state = _state(label)
    rest = text[bar + 1:].lstrip()
    # Standalone bra before an operator or an explicitly opened next ket.
    if rest and rest[0] not in '|@*/=,)' and rest[0] not in LEFT:
        end = _delimiter(text, bar + 1, RIGHT)
        if end is not None:
            middle = text[bar + 1:end]
            split = _delimiter(middle, 0, '|')
            if split is None:
                right = _state(middle)
                return 'value', f'braket({state},{right})', None, None, end + 1
            operator, right_label = middle[:split].strip(), middle[split + 1:].strip()
            if not operator or not right_label:
                raise ValueError('Use ⟨φ|A|ψ⟩ for a matrix element.')
            right = _state(right_label)
            return 'value', f'matrix_element({state},({operator}),{right})', None, None, end + 1
    return 'bra', f'bra({state})', state, label, bar + 1


def normalize_dirac(text, preserve_lhs=False):
    if not any(c in text for c in '|⟨〈⊗'):
        return text
    if len(text) > 7200:
        raise ValueError('Dirac expression is too long.')
    text = text.replace('\\langle', '⟨').replace('\\rangle', '⟩')
    # Ket definitions name the same variables/functions as ordinary definitions.
    leading = len(text) - len(text.lstrip())
    if leading < len(text) and text[leading] == '|':
        first = _atom(text, leading)
        tail = text[first[4]:].lstrip()
        if tail.startswith('=') and not tail.startswith('=='):
            label = first[3].strip()
            if not re.fullmatch(r'[^\W\d]\w*(?:_\{[^{}]+\})?(?:\([^|⟨⟩]*\))?', label):
                raise ValueError('Define a named ket, for example |ψ⟩=(|0⟩+|1⟩)/sqrt(2).')
            if not preserve_lhs:
                text = label + '=ket((' + tail[1:].strip() + '))'
    parts = []
    i = 0
    while i < len(text):
        atom = _atom(text, i) if text[i] in '|' + LEFT else None
        if atom is None:
            if text[i] == '⊗':
                raise ValueError('Use tensor(a,b) for general tensor products, or |0⟩ ⊗ |1⟩ for basis kets.')
            parts.append(text[i]); i += 1; continue
        kind, code, state, label, end = atom
        # Pair contiguous Dirac atoms before inserting ordinary multiplication.
        while kind in ('ket', 'bra'):
            next_at = end
            while next_at < len(text) and text[next_at].isspace():next_at += 1
            operator = ''
            if next_at < len(text) and text[next_at] in '*@⊗':
                operator = text[next_at]; next_at += 1
                while next_at < len(text) and text[next_at].isspace():next_at += 1
            other = (_atom(text, next_at) if next_at < len(text) and text[next_at] in '|' + LEFT else None)
            if other is None or other[0] not in ('ket', 'bra'):
                break
            other_kind, other_code, other_state, _, other_end = other
            if kind == other_kind == 'ket' and operator in ('', '⊗'):
                code = state = f'tensor({code},{other_code})'
            elif kind == 'ket' and other_kind == 'bra' and operator != '⊗':
                code = f'ketbra({state},{other_state})'; kind = 'value'
            elif kind == 'bra' and other_kind == 'ket' and operator != '⊗':
                code = f'braket({state},{other_state})'; kind = 'value'
            else:
                break
            end = other_end
        previous = ''.join(parts).rstrip()
        if previous and (previous[-1].isalnum() or previous[-1] in '_)]'):
            parts.append('*')
        parts.append(code)
        next_at = end
        while next_at < len(text) and text[next_at].isspace():next_at += 1
        if next_at < len(text) and (text[next_at].isalnum() or text[next_at] in '_(['):
            parts.append('*')
        i = end
    return ''.join(parts)
