'use strict';
(() => {
 const groups={
 'Vector fields':[
 ['Field definition','F(r)=[-r[1],r[0]]','Define a planar rotation field with a position-vector argument.'],
 ['Force −∇U','force({{U}},[1,2])','Negative gradient of a scalar potential.'],
 ['Field Jacobian','field_jacobian({{F}},[1,2])','Rows are field components, columns are spatial coordinates.'],
 ['Field divergence','field_divergence({{F}},[1,2])','Local expansion: trace of the field Jacobian.'],
 ['Field curl','field_curl({{F}},[1,2])','Signed scalar curl in 2D; vector curl for a 3D position.'],
 ['Field Laplacian','field_laplacian({{F}},[1,2])','Componentwise sum of spatial second derivatives.'],
 ['Field gradient','field_gradient({{U}},[1,2])','Gradient of a scalar spatial function.'],
 ['Field Hessian','field_hessian({{U}},[1,2])','Second derivatives of a scalar spatial function.'],
 ['Field directional','field_directional({{F}},[1,2],[1,0])','Direction is used as entered, without normalization.'],
 ['Convective derivative','field_convective({{F}},[1,2])','Jacobian times field: (F·∇)F.'],
 ['Work integral','work({{F}},r,0,2*pi)','Line integral along a defined vector path r(t).']
 ],
 'Random arrays':[
 ['Uniform vector','random_vector({{3}},42)','Repeatable uniform entries in [0,1); size 1–32.'],
 ['Uniform matrix','random_matrix({{3}},3,42)','Rows, columns, seed.'],
 ['Normal vector','normal_vector({{3}},42)','Independent standard normal entries.'],
 ['Normal matrix','normal_matrix({{3}},3,42)','Independent standard normal entries.'],
 ['Activate entries','activate({{[1,2,3]}},0.5,42)','Independently retain each entry with probability p; otherwise zero.'],
 ['Activate object','random_gate({{[1,2,3]}},0.5,42)','One Bernoulli gate for the entire vector or matrix.'],
 ['Stochastic matrix','stochastic_matrix({{3}},42)','Nonnegative matrix with each row summing to one.']
 ],
 'Trajectories & algorithms':[
 ['GBM paths','gbm({{100}},0.05,0.2,1,252,8,42)','Trajectory object: initial value, drift, volatility, horizon, steps, path count, seed.'],
 ['Parametric trajectory','trajectory({{r}},0,6.283185307179586,400)','Sample a defined scalar/vector function r(t); animate or export its path.'],
 ['Sequential algorithm','iterate({{G}},[1,0],400,0.01)','Iterate a defined update G(s,k,t,dt): initial state, steps, positive step size.'],
 ['Trajectory times','trajectory_times({{G}})','Full time column of a generated trajectory.'],
 ['Trajectory path','trajectory_path({{G}},0,0)','Full coordinate column: trajectory, zero-based path index, zero-based state component.'],
 ['GBM mean','gbm_mean({{100}},0.05,t)','Theoretical E[S(t)] for a GBM: initial value, drift per time unit, nonnegative time.']
 ],
 'Energy models':[
 ['RBM','rbm({{[[2,-2],[2,-2]]}},[-1,-1],[-2,2])','Binary restricted Boltzmann model: visible × hidden weights, visible biases, hidden biases, optional temperature.'],
 ['Boltzmann machine','boltzmann_machine({{[[0,3],[3,0]]}},[-1.5,-1.5])','Fully visible binary BM: symmetric weights with zero diagonal, biases, optional temperature.'],
 ['Joint energy','energy({{M}},[1,0],[0,1])','RBM joint energy. For a fully visible BM omit the hidden-state argument.'],
 ['Free energy','free_energy({{M}},[1,0])','RBM visible free energy after summing hidden states; also accepts continuous coordinates for relaxation plots.'],
 ['State probability','energy_probability({{M}},[1,0])','Exact probability of a binary visible state; up to 12 visible units. M([1,0]) also works.'],
 ['Log partition','log_partition({{M}})','Exact log Z, including hidden states for an RBM; up to 12 visible units.'],
 ['Hidden activations','hidden_probabilities({{M}},[1,0])','RBM hidden probabilities conditioned on visible input.'],
 ['Reconstruct','reconstruct({{M}},[1,0])','Mean-field RBM visible reconstruction probabilities.'],
 ['Gibbs samples','energy_sample({{M}},8,42)','Binary sample rows: count up to 32, seed, optional burn-in sweeps and thinning.'],
 ['Binary state','energy_state({{3}},4)','Binary vector for index 0 to 2^n−1; most significant bit first.'],
 ['Model weights','energy_weights({{M}})','Return the weight matrix for further linear algebra.'],
 ['Visible biases','energy_bias({{M}})','Return visible biases.'],
 ['Hidden biases','hidden_bias({{M}})','Return RBM hidden biases.']
 ],
 'Quantum / Dirac notation':[
 ['|0⟩','|{{0}}⟩','Computational basis ket; binary labels support 1–5 qubits.'],
 ['|ψ⟩','|{{ψ}}⟩','Named ket, or a state-valued function such as |ψ(t)⟩.'],
 ['Define ket','|{{ψ}}⟩=(|0⟩+i|1⟩)/sqrt(2)','Define a named state with its actual amplitudes.'],
 ['⟨ψ|','⟨{{ψ}}|','Conjugate-transpose bra of a named ket.'],
 ['⟨φ|ψ⟩','⟨{{φ}}|ψ⟩','Inner product; conjugates the first state.'],
 ['|ψ⟩⟨φ|','|{{ψ}}⟩⟨φ|','Outer product (dyad); conjugates the bra amplitudes.'],
 ['⟨ψ|A|ψ⟩','⟨{{ψ}}|pauliZ()|ψ⟩','Matrix element; normalized ψ gives an expectation value.'],
 ['|+⟩','|+⟩','( |0⟩ + |1⟩ ) / sqrt(2). Also |-⟩, |+i⟩ and |-i⟩.'],
 ['Tensor kets','|{{0}}⟩ ⊗ |1⟩','Tensor product; adjacent kets |0⟩|1⟩ also work.'],
 ['Bell ket','(|00⟩+|11⟩)/sqrt(2)','Normalized two-qubit Bell state.'],
 ['ket','ket({{[1,i]}})/sqrt(2)','Convert amplitudes to a ket column without normalizing.'],
 ['Bloch vector','bloch({{|ψ⟩}})','Bloch coordinates of a normalized one-qubit state.']
 ],
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
