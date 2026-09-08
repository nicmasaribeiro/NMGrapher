"""Normalize readable subscripts/powers before Unicode compatibility folding."""
import re
from symbols import normalize_symbols
from calculus_notation import normalize_calculus, normalize_function_notation
from dirac_notation import normalize_dirac

SUBSCRIPT = dict(zip('₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓᵦᵧᵨᵩᵪ',
                     '0123456789aehijklmnoprstuvxβγρφχ'))
SUPERSCRIPT = dict(zip('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁽⁾ⁿⁱ', '0123456789+-()ni'))

def normalize_notation(text, preserve_ket_lhs=False):
    text = normalize_dirac(text, preserve_lhs=preserve_ket_lhs)
    text = normalize_calculus(text)
    # x₁ and x_{1} both name x_1; A[0,1] remains element indexing.
    text = re.sub('['+''.join(SUBSCRIPT)+']+',
                  lambda m:'_'+''.join(SUBSCRIPT[c] for c in m[0]),text)
    text = re.sub(r'_\{([^{}]+)\}',lambda m:'_'+m[1].strip(),text)
    # x², x⁻² and x^{n+1} are powers, never identifier suffixes.
    text = re.sub('['+''.join(SUPERSCRIPT)+']+',
                  lambda m:'^('+''.join(SUPERSCRIPT[c] for c in m[0])+')',text)
    text = re.sub(r'\^\{([^{}]+)\}',lambda m:'^('+m[1]+')',text)
    return normalize_function_notation(normalize_symbols(text))
