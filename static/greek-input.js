// Keep this keyword table aligned with symbols.GREEK_KEYWORDS.
'use strict';
(() => {
 const keywords = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "omicron": "ο", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω"};
 function replacements(text,deferAt=null){
  const changes=[];
  for(const match of text.matchAll(/[\p{L}_][\p{L}\p{N}_]*/gu)){
   const word=match[0],split=word.search(/[_₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓᵦᵧᵨᵩᵪ⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ]/u);
   const base=split<0?word:word.slice(0,split),symbol=Object.hasOwn(keywords,base.toLowerCase())?keywords[base.toLowerCase()]:null;
   // Wait for a delimiter or blur before replacing a word at the typing caret.
   if(!symbol||(split<0&&match.index+word.length===deferAt))continue;
   changes.push({start:match.index,end:match.index+base.length,value:symbol});
  }
  return changes;
 }
 function convert(text,deferAt=null){
  let out='',start=0;
  for(const change of replacements(text,deferAt)){out+=text.slice(start,change.start)+change.value;start=change.end;}
  return out+text.slice(start);
 }
 function apply(input,force=false){
  const source=input.value,start=input.selectionStart??source.length,end=input.selectionEnd??start;
  const changes=replacements(source,force?null:start);
  if(!changes.length)return false;
  const map=position=>{let delta=0;for(const c of changes){if(position<=c.start)break;if(position<c.end)return c.start+delta+c.value.length;delta+=c.value.length-(c.end-c.start);}return position+delta;};
  input.value=convert(source,force?null:start);
  input.setSelectionRange?.(map(start),map(end),input.selectionDirection||'none');
  return true;
 }
 const api={keywords,normalize:convert,apply};
 if(typeof window!=='undefined')window.GreekInput=api;
 if(typeof module!=='undefined')module.exports=api;
})();
