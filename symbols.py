"""Modern Greek alphabet and common mathematical glyph variants."""
import unicodedata
import re

GREEK_LETTERS = [
    ('Alpha','α','Α'), ('Beta','β','Β'), ('Gamma','γ','Γ'),
    ('Delta','δ','Δ'), ('Epsilon','ε','Ε'), ('Zeta','ζ','Ζ'),
    ('Eta','η','Η'), ('Theta','θ','Θ'), ('Iota','ι','Ι'),
    ('Kappa','κ','Κ'), ('Lambda','λ','Λ'), ('Mu','μ','Μ'),
    ('Nu','ν','Ν'), ('Xi','ξ','Ξ'), ('Omicron','ο','Ο'),
    ('Pi','π','Π'), ('Rho','ρ','Ρ'), ('Sigma','σ','Σ'),
    ('Tau','τ','Τ'), ('Upsilon','υ','Υ'), ('Phi','φ','Φ'),
    ('Chi','χ','Χ'), ('Psi','ψ','Ψ'), ('Omega','ω','Ω'),
]
GREEK_VARIANTS = [
    ('Variant beta','ϐ','β'), ('Variant epsilon','ϵ','ε'),
    ('Variant theta','ϑ','θ'), ('Variant kappa','ϰ','κ'),
    ('Variant pi','ϖ','π'), ('Variant rho','ϱ','ρ'),
    ('Final sigma','ς','σ'), ('Variant phi','ϕ','φ'),
    ('Variant capital theta','ϴ','Θ'),
]
TRANSLATION = str.maketrans({glyph:canonical for _,glyph,canonical in GREEK_VARIANTS})

GREEK_KEYWORDS = {name.lower(): lower for name, lower, _ in GREEK_LETTERS}

def normalize_greek_keywords(text):
    # Only complete names or the base before a subscript: alphabet stays alphabet.
    def replace(match):
        base, separator, suffix = match[0].partition('_')
        return GREEK_KEYWORDS.get(base.lower(), base) + separator + suffix
    return re.sub(r'[^\W\d]\w*', replace, text)

def normalize_symbols(text):
    return normalize_greek_keywords(unicodedata.normalize('NFKC', text.translate(TRANSLATION)))

def symbol_catalog():
    return {'keywords':GREEK_KEYWORDS, 'letters':[{'name':n,'lower':l,'upper':u} for n,l,u in GREEK_LETTERS],
            'variants':[{'name':n,'symbol':s,'canonical':c} for n,s,c in GREEK_VARIANTS]}
