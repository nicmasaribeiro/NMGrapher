'use strict';
(() => {
 const groups={
 'Calculus':[
 ['exp','exp({{x}})','Exponential e^x.'],['ln','ln({{x}})','Natural logarithm.'],['log','log10({{x}})','Common logarithm (base 10). Inserts log10; existing log(x) remains natural log.'],['logₐ','log_{{2}}(x)','Logarithm with a positive base other than 1.'],
 ['d/dx','d/dx({{f(x)}})','Numerical derivative of an expression.'],['f′',"{{f}}'(x)",'Derivative of a defined one-argument function. Two primes give the second derivative.'],['∫','∫_{0}^{x} ({{f(t)}}) dt','Definite integral or integral-defined function.'],['∫∫','∫_{0}^{1} ∫_{0}^{y} ({{x+y}}) dxdy','Double integral; inner bounds may depend on outer variables.'],['∫∫∫','integrate({{x+y+z}}, [x,y,z], [0,0,0], [1,1,1])','Triple integral, variables in differential order.'],['∑','∑_{k=1}^{10} ({{k^2}})','Finite sum with an integer index.'],['∏','∏_{k=1}^{5} ({{k}})','Finite ordered product.'],
 ['gradient','grad({{x^2+y^2}},[x,y])','Gradient of a scalar function.'],['jacobian','jacobian({{[x*y,sin(x)]}},[x,y])','Jacobian of vector or matrix entries.'],['hessian','hessian({{x^2+x*y+y^2}},[x,y])','Matrix of second partial derivatives.']
 ],
 'Statistics':[
 ['mean','mean({{[1,2,3]}})','Arithmetic mean; distributions also supported.'],['median','median({{[1,2,3]}})','Median.'],['min','min({{[1,2,3]}})','Minimum of a list, or entrywise minimum of two inputs.'],['max','max({{[1,2,3]}})','Maximum of a list, or entrywise maximum of two inputs.'],
 ['quartile','quartile({{[1,2,3,4]}},1)','Position 0–4, using linear interpolation.'],['quantile','quantile({{[1,2,3,4]}},0.25)','Data quantile or distribution inverse CDF.'],['stdev','stdev({{[1,2,3]}})','Sample standard deviation, denominator n−1.'],['stdevp','stdevp({{[1,2,3]}})','Population standard deviation, denominator n.'],['var','var({{[1,2,3]}})','Sample variance.'],['varp','varp({{[1,2,3]}})','Population variance.'],
 ['cov','cov({{[1,2,3]}},[2,4,6])','Sample covariance of aligned observations.'],['covp','covp({{[1,2,3]}},[2,4,6])','Population covariance.'],['mad','mad({{[1,2,3]}})','Mean absolute deviation from the mean.'],['corr','corr({{[1,2,3]}},[2,4,6])','Pearson correlation.'],['spearman','spearman({{[1,2,3]}},[2,4,6])','Rank correlation with average ranks for ties.'],['stats','stats({{[1,2,3,4]}})','Five-number summary: minimum, Q1, median, Q3, maximum.'],['count','count({{[1,2,3]}})','Number of finite observations; existing missing-data convention is retained.'],['total','total({{[1,2,3]}})','Sum of entries. Missing values propagate.']
 ],
 'Hyperbolic trig functions':[
 ['sinh','sinh({{x}})','Hyperbolic sine.'],['cosh','cosh({{x}})','Hyperbolic cosine.'],['tanh','tanh({{x}})','Hyperbolic tangent.'],['csch','csch({{x}})','Reciprocal of sinh.'],['sech','sech({{x}})','Reciprocal of cosh.'],['coth','coth({{x}})','Reciprocal of tanh.']
 ],
 'Wavelet functions':[
 ['Mexican hat','mexican_hat({{x}},1,0)','Unit-energy Mexican hat: input, scale, shift.'],['Morlet','morlet({{x}},1,0,6)','Complex zero-mean Morlet: input, scale, shift, angular frequency.'],['Haar','haar({{x}},1,0)','Haar mother wavelet: input, scale, shift.'],
 ['DWT','dwt({{signal}},0,2)','Reusable discrete transform. Level 0 is automatic; wavelet IDs: Haar 0, db2 1, db4 2, sym4 3, coif1 4.'],['Inverse DWT','idwt({{W}})','Reconstruct a DWT result.'],['CWT','cwt({{signal}},[4,8,16],0,1)','Multiscale continuous transform: signal, scales, wavelet ID, sample spacing.'],['Coefficients','wavelet_coeffs({{W}},0)','Coefficient sequence at a zero-based band/scale index.'],['Band','wavelet_band({{W}},0)','Reconstructed full-length DWT band.'],['Power','wavelet_power({{W}},0)','Squared magnitude of coefficients for one band/scale.'],['Scales','wavelet_scales({{W}})','Scales from a multiscale CWT.'],['Frequencies','wavelet_frequencies({{W}})','Mapped frequencies from a multiscale CWT.'],
 ['Denoise','wavelet_denoise({{signal}},1,2,0)','Denoise observations: strength, wavelet ID, level.'],['Approximation','wavelet_approx({{signal}},2,0)','Reconstructed approximation at a DWT level.'],['Detail','wavelet_detail({{signal}},2,0)','Reconstructed detail at a DWT level.'],['Single-scale CWT','wavelet_cwt({{signal}},8,0)','Full-resolution coefficients at one scale.']
 ],
 'Trigonometry':[['sin','sin({{x}})','Sine in radians.'],['cos','cos({{x}})','Cosine in radians.'],['tan','tan({{x}})','Tangent in radians.'],['asin','asin({{x}})','Inverse sine.'],['acos','acos({{x}})','Inverse cosine.'],['atan','atan({{x}})','Inverse tangent.']],
 'Probability':[['normaldist.pdf','normaldist(0,1).pdf({{x}})','Use a distribution density as a function.'],['D(x)','{{D}}(x)','Call a named distribution D=normal(0,1).'],['normal','normal({{0}},1)','Mean and standard deviation.'],['poisson','poisson({{4}})','Poisson mean.'],['binomial','binomial({{10}},0.5)','Trials and success probability.'],['boltzmann','boltzmann({{[0,1,2]}},1)','Energy levels and temperature.'],['pdf','pdf({{D}},x)','Continuous density.'],['pmf','pmf({{D}},2)','Discrete mass.'],['cdf','cdf({{D}},x)','Cumulative probability.'],['prob','prob({{D}},-1,1)','Interval probability.']],
 'Linear algebra':[['det','det({{A}})','Determinant.'],['inverse','inv({{A}})','Inverse matrix.'],['eigenvalues','eigvals({{A}})','Eigenvalues.'],['eigenvectors','eigvecs({{A}})','Matching eigenvectors in columns.'],['solve','solve({{A}},[1,2])','Solve a square linear system.'],['SVD','svdU({{A}})','SVD U factor; use svdS and svdVh for the other factors.']]
 };
 const entries=Object.entries(groups).flatMap(([category,items])=>items.map(([label,template,description])=>({category,label,template,description})));
 function insertion(template,selected=''){
  let text='',start=null,end=null,last=0;for(const m of template.matchAll(/\{\{([\s\S]*?)\}\}/g)){text+=template.slice(last,m.index);const value=start===null&&selected?selected:m[1];if(start===null){start=text.length;end=start+value.length;}text+=value;last=m.index+m[0].length;}text+=template.slice(last);return {text,start:start??text.length,end:end??text.length};
 }
 function search(query){query=query.toLowerCase().trim();return entries.filter(e=>(e.label+' '+e.category+' '+e.template+' '+e.description).toLowerCase().includes(query));}
 const api={entries,insertion,search};if(typeof window!=='undefined')window.FunctionCatalog=api;if(typeof module!=='undefined')module.exports=api;
})();
