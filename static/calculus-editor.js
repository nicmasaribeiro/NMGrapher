'use strict';
(() => {
 const operations={
  first:{label:'First derivative',help:'Differentiate a scalar, vector, or matrix with respect to one argument.'},
  second:{label:'Second derivative',help:'Take the second derivative with respect to one argument.'},
  mixed_diff:{label:'Mixed partial derivative',multi:true,help:'Select exactly two distinct variables. The expression must be scalar.'},
  grad:{label:'Gradient ∇f',multi:true,help:'A scalar expression produces a vector in the selected variable order.'},
  jacobian:{label:'Jacobian J',multi:true,help:'Rows follow output entries; columns follow selected variables. Matrix outputs are flattened row by row (up to 32 entries).'},
  hessian:{label:'Hessian H',multi:true,help:'A scalar expression produces its symmetric matrix of second partial derivatives.'},
  divergence:{label:'Divergence ∇·F',multi:true,help:'The vector must have one component per selected variable. Returns a scalar.'},
  curl:{label:'Curl ∇×F',multi:true,help:'Select three variables in coordinate order and supply a three-component vector.'},
  laplacian:{label:'Laplacian ∇²f',multi:true,help:'Sum second partial derivatives over selected variables; supports scalar, vector, and matrix outputs.'},
  directional:{label:'Directional derivative',multi:true,help:'Differentiate along the supplied real direction. The direction is used as entered, without normalization.'},
  primitive:{label:'Integral function (primitive)',primitive:true,help:'Create a numerical antiderivative equal to zero at the lower/base point. Add a constant separately for the general family.'},
  multiple:{label:'Double / triple integral',multi:true,integral:true,multiple:true,help:'Select two or three variables in differential order (innermost first). Each variable has its own bounds; inner bounds may depend on outer variables. Unselected arguments remain parameters.'},
  definite:{label:'Definite integral',integral:true,help:'Integrate over finite bounds. Other arguments remain parameters; reverse the bounds to reverse the sign.'},
  accumulated:{label:'Accumulated integral',integral:true,help:'Integrate from the lower bound to the selected argument, creating an accumulation function.'}
 };
 function draft(c){
  const spec=operations[c.operation];if(!spec)throw Error('Choose a calculus operation.');
  const args=c.args;if(!args.length||args.some(a=>!a)||new Set(args).size!==args.length)throw Error('Enter distinct, comma-separated argument names.');
  const variables=spec.multi?c.variables:[c.variable];
  if(!variables.length||variables.some(v=>!args.includes(v))||new Set(variables).size!==variables.length)throw Error('Select calculus variables from the argument list.');
  if(spec.multi&&variables.length>32)throw Error('Select at most 32 calculus variables per operation.');
  if(spec.multiple&&(variables.length<2||variables.length>3))throw Error('Select two or three integration variables.');
  if(c.operation==='mixed_diff'&&variables.length!==2)throw Error('Select exactly two variables for a mixed partial.');
  if(c.operation==='curl'&&variables.length!==3)throw Error('Select exactly three variables for curl.');
  if(!c.expression.trim())throw Error('Enter an expression to calculate.');
  const variable=variables[0],vars='['+variables.join(', ')+']';
  let body;
  if(spec.multiple){
   const limits=variables.map(variable=>c.integrationBounds?.find(v=>v.variable===variable)||{lower:c.lower,upper:c.upper});
   if(limits.some(v=>!v.lower?.trim()||!v.upper?.trim()))throw Error('Enter lower and upper bounds for every integration variable.');
   body=`integrate(${c.expression}, ${vars}, [${limits.map(v=>v.lower).join(', ')}], [${limits.map(v=>v.upper).join(', ')}], ${c.absTol||'1e-8'}, ${c.relTol||'1e-7'})`;
  }else if(spec.primitive){
   if(!c.lower.trim())throw Error('Enter a base point for the integral function.');
   body=`antiderivative(${c.expression}, ${variable}, ${c.lower})`;
  }else if(spec.integral){
   if(!c.lower.trim()||(c.operation==='definite'&&!c.upper.trim()))throw Error('Enter the integration bounds.');
   body=`integrate(${c.expression}, ${variable}, ${c.lower}, ${c.operation==='accumulated'?variable:c.upper}, ${c.absTol||'1e-8'}, ${c.relTol||'1e-7'})`;
  }else if(spec.multi){
   if(c.operation==='directional'&&!c.direction.trim())throw Error('Enter a direction in the selected variable order.');
   body=`${c.operation}(${c.expression}, ${vars}${c.operation==='directional'?', ['+c.direction+']':''}${c.step?', '+vars+', '+c.step:''})`;
  }else body=`diff(${c.expression}, ${variable}, ${variable}, ${c.operation==='second'?2:1}${c.step?', '+c.step:''})`;
  const remaining=spec.multiple?args.filter(a=>!variables.includes(a)):c.operation==='definite'?args.filter(a=>a!==variable):args;
  const pointText=`at(${body}, [${args.join(', ')}], [${c.point}])`;
  if(c.resultMode==='point'&&!c.point.trim())throw Error('Enter coordinates in argument order.');
  const text=c.resultMode==='point'?pointText:remaining.length?`${c.name}(${remaining.join(', ')}) = ${body}`:body;
  if(c.resultMode!=='point'&&remaining.length&&!c.name.trim())throw Error('Enter a result function name.');
  return {text,body,remaining,variables,pointText};
 }
 const api={operations,draft};if(typeof window!=='undefined')window.CalculusEditor=api;if(typeof module!=='undefined')module.exports=api;
})();
