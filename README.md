# NMGrapher

A local Flask graphing calculator inspired by the expression-and-graph workflow of Desmos, with matrices, complex numbers, and named probability distributions, plus the complete modern Greek alphabet. It is an independent implementation, not a full Desmos clone.

## Run

Use Python 3.11 or newer. From this extracted folder:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

For Spyder, CodeRunner, PyCharm, or another IDE, install the requirements into the IDE's Python environment, open `app.py`, and run it normally. No command-line arguments are needed. Keep the script running while you use the browser. If port 5000 is occupied, change `port=5000` to `port=5001` at the bottom of `app.py` and open the corresponding address.

This version adds PyWavelets. When upgrading, rerun `python -m pip install -r requirements.txt` in the same Python environment used to run `app.py`.

The frontend and Plotly are served locally; there are no CDN, API key, Node.js, or build-tool requirements. Installing Python dependencies requires internet access unless they are already installed.

## Workspace

Choose **Light** or **Dark** from the header’s **Theme** selector. Drag an equation using its **⋮⋮** handle to change its position.

- **＋ Create graph** creates named Cartesian, parametric, polar, 3D, implicit, surface, contour, scatter, line, bar, histogram, or probability graphs. **My graphs** displays them individually or as 2D/3D overlays.
- **ƒ Built-in functions** opens a searchable insertion palette for calculus, statistics, hyperbolic functions, wavelets, probability, and linear algebra.
- **Wavelets** analyzes recorded signals from imported columns or pasted samples: continuous wavelet power maps, discrete bands, reconstruction, and denoising.
- **Probability** creates distributions, calculates densities/masses, cumulative and interval probabilities, and quantiles, and saves probability graphs.
- Enter one expression per row. Enter adds another row; Shift+Enter adds a line break.
- Import numeric datasets from CSV/TSV or pasted tables, preview columns, plot points/lines, and use named columns in equations.
- Define scalars, functions with any number of named arguments, vectors, and matrices. References can appear before definitions.
- Drag sliders on numeric scalar assignments to update dependent calculations.
- Pan and zoom the graph; use Reset view to return to the initial bounds.
- Colored circles hide or show plots without disabling variable definitions.
- Click **Matrix** to enter cells in a grid; **Edit grid** edits a literal matrix while preserving its cell expressions.
- **Linear algebra** opens a studio for eigenvalues/eigenvectors, decompositions, subspaces, and least-squares solutions. Matrix results also have a **Linear algebra** action.
- **Heatmap** visualizes any matrix, including rectangular matrices. Choose real, imaginary, magnitude, or phase for complex matrices.
- **Qubit** creates a normalized state from complex amplitudes or Bloch angles. The **Qubit** view shows measurement probabilities and, for a single qubit, its Bloch sphere.
- **∫ Calculus** opens Calculus studio: derivatives, mixed partials, gradients, Jacobians, Hessians, divergence, curl, Laplacians, directional derivatives, and integrals, with point previews and numerical controls. Each function also has a Calculus button, and its editor can differentiate or integrate the current formula.
- **ƒ Function** opens the function creator. Edit a definition with its **Edit function** button.
- Subscript/superscript buttons insert editable notation; each expression and the function creator show a formatted preview.
- **Surface** displays two-variable functions in 3D. Choose real, imaginary, magnitude, or phase output; **Input range** changes the sampled input rectangle.
- **Complex plane** plots scalar values, vector entries (including roots/eigenvalues), and function trajectories. Its parameter interval is independent of the viewing bounds.
- **Domain map** evaluates one-argument functions on complex inputs and displays magnitude or phase.
- **αβ Symbols** inserts all 24 Greek letters in both cases and common glyph variants at the cursor, including inside matrix cells.
- **Transform** visualizes a real 2×2 matrix acting on a square grid, unit circle, and basis vectors.
- **Save worksheet** downloads JSON. **Open** restores a saved JSON worksheet. Current work also autosaves in this browser's local storage.
- **PNG** downloads the current plot. **Reference** opens the expression guide.

## Expression examples

```text
a = 2
f(t) = a * sin(t)
y = f(x)
x^2 + y^2 = 9
y < sin(x)
A = [[2, 1], [1, 3]]
B = [[1, -1], [0, 2]]
A @ B
A^2
A^-1
det(A)
eigvals(A)
solve(A, [1, 2])
A[0, 1]
```

Use explicit multiplication: `2*x`, not `2x`. Both `^` and `**` mean powers. Both `A @ B` and `A * B` mean matrix multiplication when both operands are matrices. `A * v` and `v * A` also perform algebraic matrix–vector or vector–matrix multiplication; `@` has the same behavior for these cases. Scalar multiplication is entrywise. `A^n` is an integer matrix power. Vector `*` is entrywise; use `@` for a vector dot product. Matrix indices start at zero.

| Operation | Input |
| --- | --- |
| Transpose | `T(A)` |
| Determinant, inverse, pseudoinverse | `det(A)`, `inv(A)`, `pinv(A)` |
| Trace, rank, norm, eigenvalues | `trace(A)`, `rank(A)`, `norm(A)`, `eigvals(A)` |
| Linear solve | `solve(A, [1, 2])` |
| Identity | `eye(3)` |
| Matrix exponential / logarithm | `expm(A)`, `logm(A)` |
| Entrywise exponential / logarithm | `exp(A)`, `log(A)` |
| Complex number and components | `1 + 2*i`, `real(A)`, `imag(A)`, `conj(A)` |
| Piecewise values | `where(x > 0, x, -x)` |

`log` and `ln` are natural logarithms. Trigonometric functions use radians. `sqrt(-1)` automatically returns `i`, `log(-1)` returns `i*pi`, and negative-base fractional powers use the principal complex branch. Singular inverses return an error; use `pinv` when a pseudoinverse is appropriate.

## Included examples

The Examples menu replaces the current worksheet. Save a worksheet first if you want to retain a portable copy.

- Functions and sliders
- Matrix algebra
- Implicit curves and inequalities
- Mexican hat wavelet with scale and translation
- CTMC transitions using `P = expm(t * Q)` and a row probability vector `p @ P`

For the CTMC example, the generator rows sum to zero. `t` must use the same time unit as the generator rates. `expm(t*Q)` is the matrix exponential, whereas `exp(t*Q)` is entrywise and is not a CTMC transition matrix.

## Project structure

```text
NMGrapher/
    app.py                   Flask routes and local entry point
    engine.py                Restricted numeric AST interpreter
    symbols.py               Greek alphabet and canonical glyph aliases
    notation.py              Subscript and superscript normalization
    calculus_notation.py     Integral and derivative notation parser
    math_preview.py          Safe semantic MathML preview trees
    linear_algebra.py        Eigenpairs, decompositions, subspaces, diagnostics
    graphing.py              Bounded sampling for named graphs and data charts
    probability.py           Distributions, probability queries, seeded samples
    wavelets.py              Wavelet functions, CWT, DWT, and signal preparation
    static/wavelet-tools.js  Signal controls, validation, CSV and dataset outputs
    resident_math.py          Additional statistics, hyperbolic functions, logarithms
    static/function-catalog.js  Built-in function palette and insertion templates
    static/graph-tools.js    Graph definitions, validation, and Plotly traces
    static/math-preview.js  Offline MathML rendering and preview requests
    calculus.py              Numerical differentiation and adaptive integration
    quantum.py               Quantum states, gates, probabilities, reduced states
    array_types.py           Distinguish worksheet vectors/matrices from graph grids
    requirements.txt         Runtime dependencies
    templates/index.html     Calculator workspace
    static/app.js            Editing, plotting, saving, themes, equation reordering
    static/theme-init.js     Apply appearance before the first paint
    static/style.css          Responsive styling
    static/plotly.min.js      Bundled plotting library
    tests/test_engine.py      Calculation and HTTP checks
    THIRD_PARTY_NOTICES.md
    LICENSE-plotly.txt
```

`POST /api/evaluate` accepts:

```json
{
  "expressions": [{"text": "A = [[2,1],[1,3]]"}, {"text": "det(A)"}],
  "bounds": [-10, 10, -7, 7]
}
```

Optional `complex_domain: true` evaluates function definitions on a complex grid. Optional `curve_range: [0, 6.283185307179586]` sets the real parameter interval independently of graph bounds. `GET /api/symbols` returns the Greek symbol catalog.

The response has one `results` entry per expression, containing its value or sampled plot data, or an individual error. Definitions are resolved recursively. Matrix values are distinguished from sampled graph-coordinate arrays so matrix multiplication and powers retain their intended meaning.

## Scope and numerical limits

This version supports numeric 2D curves, implicit equalities, inequalities, scalar parameters, functions with any number of named arguments, complex-plane trajectories, complex function domain maps, and matrix calculations. It does not implement Desmos's full notation, symbolic differentiation/integration, regression tables, animation playback, cloud collaboration, or arbitrary Python execution. Vector- and matrix-valued functions support scalar calls and sampled plots of their entries, including one- and two-variable definitions.

Curves use 1,000 samples and implicit/inequality plots use a 180×180 grid, resampled after zooming. Non-finite curve values become gaps; a large-jump heuristic also breaks common poles. This does not guarantee detection of every discontinuity or very small feature. Heatmaps and matrix results are numerical, not exact symbolic calculations.

Limits: 40 rows per worksheet, 1,200 characters and 300 syntax nodes per expression, matrix dimensions up to 32×32, and 2 MB per request. The visual matrix editor supports up to 12×12; larger matrices can be typed. Circular definitions, unknown names, incompatible shapes, and unsupported syntax produce row-level errors.

The interpreter uses an allowlist of AST nodes and numeric functions, without `eval` or `exec`. The Flask server binds to loopback and disables debugging. This package is designed for local personal use; deploying a shared service would require a separate production serving and resource-isolation design.

## Verification

Install `pytest` separately if you want to run the bundled checks:

```bash
python -m pip install pytest
python -m pytest -q
```

Checks cover linear algebra, CTMC row probabilities, dependency resolution, curves and inequalities, complex results, invalid expressions, request validation, and local assets. JavaScript syntax was checked with `node --check static/app.js` during development. Automated browser interaction and visual rendering were not tested in this environment.


## Complex mathematics upgrade

Type either `i` or `j` for the imaginary unit. Numeric coefficients accept `3i`, `3*i`, or Python-style `3j`. Ordinary variable multiplication still needs `*`: use `α*i`, not `αi` (which is a variable name).

```text
ζ = 2 + 3i
sqrt(-1)
log(-1)
(-1)^0.5
abs(ζ)
arg(ζ)
polar(2, pi/3)
roots(1, 5)
ψ(θ) = 2 * exp(i*θ)
Α = [[2, i], [-i, 3]]
H(Α)
U = expm(i*Α)
isunitary(U)
inner([1, i], [1, i])
```

- `arg` / `phase` return the principal angle in radians, in [-π, π]. Phase at zero is undefined: `arg(0)` reports an error and phase-map zero entries are gaps.
- `polar(r, θ)` constructs `r*exp(i*θ)` with nonnegative real radius and real angle; `cis(θ)` is its unit-radius form.
- `roots(z, n)` returns all n roots of a scalar, with multiplicities, for integer n from 1 to 32.
- `H(A)` is the conjugate transpose, while `T(A)` is the ordinary transpose.
- `inner(u, v)` conjugates the first vector; `u @ v` does not conjugate it.
- `sqrtm(A)` computes a matrix square root. `sqrt(A)` applies scalar roots entrywise. `A^n` continues to require an integer matrix exponent.
- `ishermitian(A)` and `isunitary(A)` return 1 or 0, using numerical tolerance (absolute 1e-10, relative 1e-8).
- Complex function outputs in Graph view show solid real and dashed imaginary curves. Complex plane shows the corresponding trajectory for a real parameter; Domain map instead samples the full complex input plane.
- Domain maps display magnitude or phase, not a 3D surface or a combined hue/brightness domain-coloring image. They resample after zooming. Singularities become gaps; branch cuts and narrow features are subject to the sampling resolution.
- Ordered comparisons of non-real complex values are rejected. Compare `abs(z)`, `real(z)`, or `imag(z)` instead. Implicit equalities and shaded inequalities still require real-valued results.
- Tiny imaginary components are retained. Floating-point calculations may show small residuals, for example in `exp(i*pi)`.

The Complex numbers, Complex functions, Complex matrices, and Greek notation examples are available in the Examples menu. Existing version-1 worksheet JSON files remain supported; new saves preserve the view, heatmap component, and trajectory parameter interval.

## Greek notation

All modern Greek letters are usable as variable, function, argument, and matrix names, except lowercase `π`, which is the built-in pi constant. Uppercase `Π` remains available. Names are case-sensitive; Greek `Α` and Latin `A` are different names, as are Greek iota `ι` and the imaginary unit `i`.

`Σ` and `Π` are ordinary names, not summation/product operators. This upgrade adds the 24-letter modern alphabet and common mathematical variants; it does not implement every historical character in the Unicode Greek blocks or new symbolic operators.

| Name | Lowercase | Uppercase |
| --- | --- | --- |
| Alpha | α | Α |
| Beta | β | Β |
| Gamma | γ | Γ |
| Delta | δ | Δ |
| Epsilon | ε | Ε |
| Zeta | ζ | Ζ |
| Eta | η | Η |
| Theta | θ | Θ |
| Iota | ι | Ι |
| Kappa | κ | Κ |
| Lambda | λ | Λ |
| Mu | μ | Μ |
| Nu | ν | Ν |
| Xi | ξ | Ξ |
| Omicron | ο | Ο |
| Pi | π | Π |
| Rho | ρ | Ρ |
| Sigma | σ | Σ |
| Tau | τ | Τ |
| Upsilon | υ | Υ |
| Phi | φ | Φ |
| Chi | χ | Χ |
| Psi | ψ | Ψ |
| Omega | ω | Ω |

Glyph variants are canonical aliases, so defining both an alias and its canonical spelling in one worksheet reports a duplicate name. Unicode compatibility forms are normalized.

| Variant | Canonical name |
| --- | --- |
| ϐ | β |
| ϵ | ε |
| ϑ | θ |
| ϰ | κ |
| ϖ | π |
| ϱ | ρ |
| ς | σ |
| ϕ | φ |
| ϴ | Θ |

Verification after the resident-functions, transforms, and graph-naming upgrade: **300 backend/API tests passed**. Checks cover the displayed statistics, hyperbolic functions, custom logarithm bases, prime derivatives, bounded sums/products, local index binding, Greek name compatibility, wavelet transform objects and inverses, imported signal reuse, and prior regressions. Node checks passed for palette coverage/insertion/search, graph names and titles, and the prior graph, wavelet, preview, calculus, dataset, and Greek controls. Frontend JavaScript syntax, Flask homepage rendering, and static UI targets were checked. Browser interaction and visual rendering were not tested.


## Two-variable functions and formatted notation

```text
α_1 = 2
f₁(x₁, x₂) = α_1 * exp(-(x₁² + x₂²)/4)
f_1(1, 2)
g(t) = f_1(t, 0)
ψ(x, y) = exp(i*x) * cos(y)
```

1. Click **ƒ Function**. Enter a name, a comma-separated argument list, and the formula. The formatted preview updates while you type.
2. Use **xₙ** to insert a subscript or **xⁿ** to insert a power. The inserted number is selected so you can replace it. Greek symbols can be inserted into all creator fields.
3. Apply the function. Definitions with at least two arguments open the **Surface** view, initially plotting the first two inputs and holding the rest at zero. Expand **Plot inputs** below the equation to choose axes and fixed values. Drag to rotate and scroll to zoom. Use **Input range** to change either argument's domain.
4. Choose the output component: real, imaginary, magnitude, or phase. Input axes follow the plot-input selection, initially the argument order. Two-variable surfaces sample *real* arguments; they do not represent a four-dimensional domain of two complex inputs.
5. Use `f_1(1, 2)` for a point calculation, `f_1(x, 0)` for a curve, or `(f_1(x,y)) = 0` for an implicit level set. Parentheses disambiguate the last expression from a function definition. Writing `f_1(x,y) = 0` by itself means a function definition and reports a duplicate if that function already exists.

In **Graph**, two-variable function definitions and bare expressions involving both graph coordinates appear as real-part level curves. **Surface** displays one selected field at a time; its component selector also supports complex-valued outputs. Scalar surface sampling uses a 180×180 grid (60×60 for vector/matrix operations, or 32×32 for array-dependent calculus), with non-finite values left as gaps. Zooming/rotating the camera does not change the input domain; use the Input range controls to resample.

One-argument functions retain their original curve and complex-domain behavior. Every function call must supply exactly its declared number of inputs. Inputs can be scalar, complex, or matrix values when used in ordinary numeric calls. Automatic previews accept fixed-size scalar, vector, or matrix outputs at each input point. Functions that require matrix inputs may still show a scalar-input preview error while explicitly supplied matrix calls evaluate.

| Typed form | Equivalent form | Meaning |
| --- | --- | --- |
| `x₁`, `x_{1}` | `x_1` | A subscripted variable name |
| `f₁(x₁, x₂)` | `f_1(x_1, x_2)` | A subscripted two-argument function |
| `α₁` | `α_1` | A Greek subscripted name |
| `x²` | `x^2` | A power |
| `x⁻²` | `x^(-2)` | A negative power |
| `x^{n+1}` | `x^(n+1)` | A compound exponent |
| `A_1[0,1]` | unchanged | Matrix entry indexing, separate from name subscripts |

`x₁` and `x1` are distinct names; `x₁` and `x_1` are aliases. ASCII `_name` and `_{name}` support multi-character subscript names. Unicode subscript digits and common available subscript letters are supported. Unicode superscripts support digits, signs, parentheses, `n`, and `i`; use `^(...)` for arbitrary exponents. Write `sin(x)^2`, not `sin²(x)`.

This is numeric notation support and a formatted preview, not a complete LaTeX editor or symbolic tensor-index system. Subscripts label variables; they do not imply summation, differentiation, or matrix indexing. Existing worksheet files remain compatible.


## Derivatives and integration

Use the **∫ Calculus** button, or **Calculus** under any function definition. Choose a derivative, multivariable differential operator, or integral. Select the calculus variables; unselected arguments stay fixed during that calculation. Evaluate a test point before adding a reusable function or a point result. The generated expression is shown before you add it. Definite integration removes the integrated argument from the result function; a one-variable definite integral produces a scalar result.

The function creator also has **Differentiate formula** and **Integrate formula** buttons. Expand **Calculus variable and integral bounds** to choose the variable and lower/upper bounds, including parameter-dependent bounds. Defaults use the first argument and integrate from zero to that argument. The draft remains editable before applying it.

### Derivative syntax

```text
f(x) = sin(x)
d_1(x) = diff(f(x), x)
d_2(x) = diff(f(x), x, x, 2)
diff(f(x), x, pi/4)
diff(f(x), x, pi/4, 1, 0.001)
```

`diff(expression, variable[, point, order, step])` takes two through five arguments. `derivative` is an alias. If the point is omitted, it uses the variable's current value, including sampled graph coordinates. Order is 1 or 2 and defaults to 1. The optional step must be a positive finite real scalar.

```text
f(x, y) = x^2 * y + sin(y)
d_x(x, y) = diff(f(x,y), x)
d_y(x, y) = diff(f(x,y), y)
d_xy(x, y) = diff(diff(f(x,y), x), y)
d_x(2, 3)
```

Here `d_x(2,3)` is approximately 12. Subscripted and Greek variables work as calculus variables, for example `diff(θ₁³, θ₁, 2)`.

### Integral syntax

```text
integrate(x^2, x, 0, 1)
integrate(sin(t), t, 0, pi)
F(x) = integrate(sin(t), t, 0, x)
f(x, y) = x^2 + y
G(y) = integrate(f(x,y), x, 0, 1)
integrate(integrate(x*y, y, 0, 1), x, 0, 1)
```

`integrate(expression, variable, lower, upper[, abs_tol, rel_tol])` computes a definite integral. `integral` is an alias. Lower and upper limits must be finite and real; reversed limits reverse the sign. The integration variable is local to the integrand, so it does not overwrite a worksheet variable with the same name. Bounds are evaluated outside that local binding.

Accumulated integrals supply numerical antiderivative curves with a chosen basepoint: `F(x) = integrate(f(t), t, 0, x)` has `F(0)=0` where the integral is defined. This does not produce a symbolic indefinite-integral formula or an arbitrary integration constant.

### Complex and matrix outputs

```text
integrate(exp(i*t), t, 0, pi)
diff(exp(i*x), x, 0)
A = [[1, 0], [0, 2]]
diff(expm(t*A), t, 0)
integrate(t*A, t, 0, 1)
```

Complex-valued integrals integrate real and imaginary components together over a real interval. Derivatives at complex points use a real-direction perturbation; this is not a test of holomorphicity. Matrix-valued outputs can be differentiated or integrated entry by entry with respect to a scalar parameter; they retain matrix arithmetic afterward. This is not differentiation with respect to an entire matrix, a Jacobian API, or contour integration along a complex path.

### Numerical method and limits

Derivatives use five-point centered finite differences, compare steps h and h/2, and report a Richardson-style error estimate. Default h scales with the evaluation point and machine precision. A comparison of one-sided slopes flags obvious cusps or unstable samples. Flagged/non-finite plot samples become gaps; an undefined scalar produces a row error. These checks are heuristic: sharp features, cancellation, noise, branch cuts, and high-frequency functions can require a user-selected step. Error estimates are not guaranteed mathematical bounds.

Integrals use SciPy adaptive Gauss–Kronrod quadrature through `quad_vec`, with absolute tolerance 1e-8, relative tolerance 1e-7, a maximum of 100 subdivisions, and the max norm for vector outputs. Finite intervals are mapped to [0,1], which also supports arrays of upper limits for accumulated-integral plots. A non-finite interior sample or non-convergence produces a row error. Some integrable endpoint singularities converge, but infinite bounds, principal-value integrals, and automatic singularity splitting are not supported; split difficult intervals explicitly.

The row displays an error estimate for the most recent outer calculus operation. The API includes a `calculus` diagnostics list (up to the last 20 operations) with the estimated error, derivative order/undefined-sample count, or quadrature evaluation count. Nested calculus is limited to three operations, and the existing expression evaluation budget remains in force. Expensive nested integrals may need to be split into simpler calculations.

The **Derivatives & integrals** and **Partial derivatives** examples are available in the Examples menu. All existing worksheet formats remain compatible. Browser interaction and visual rendering have not been tested in this environment.


## Light/dark mode and equation ordering

The header’s **Theme** selector switches the entire interface between light and dark, including dialogs, matrix editors, plot backgrounds, axis labels, and 3D surfaces. The preference is saved separately in this browser; on the first visit, the application uses your device’s light/dark preference. Worksheet imports do not override it. PNG exports use the current plot appearance.

To reorder an equation, drag its **⋮⋮** handle on the left. A line marks the drop position, and the equation list scrolls when you drag near its top or bottom edge. Release to drop; press Escape or release outside the list to cancel. Pointer events support mouse, touch, and pen input.

For keyboard control, Tab to a handle, then use **Up/Down** to move one position or **Home/End** to move to the beginning/end. The moved handle retains focus and its new position is announced for screen readers.

Equation text, colors, visibility, and slider settings move together. The new order autosaves and is included in exported worksheet JSON; colors also survive reopening a saved worksheet. Unique definitions still resolve regardless of their order. Reordering invalidates pending calculation responses and remaps completed results by row identity, so a result does not become attached to another equation while recalculation is pending.

Validation for this interface update: both frontend JavaScript files passed syntax checks. The Python calculation engine was unchanged. Browser interaction and visual rendering remain untested in this environment.


## Qubit mathematics

A pure qubit is a complex two-component state with unit norm:

```math
|ψ⟩ = α|0⟩ + β|1⟩,       |α|² + |β|² = 1
P(0) = |α|²,              P(1) = |β|²
```

The angle constructor uses `α = cos(θ/2)` and `β = exp(iφ) sin(θ/2)`. The density matrix is `ρ = |ψ⟩⟨ψ|`. Its Bloch coordinates are `[Tr(ρX), Tr(ρY), Tr(ρZ)]`, equivalently `[2 Re(conj(α)β), 2 Im(conj(α)β), |α|²−|β|²]` for a pure state. Pure states lie on the sphere; mixed states lie inside it. Global phase does not change the Bloch point or probabilities. These conventions follow [IBM Quantum's Bloch-sphere treatment](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere).

```text
θ = 1.5707963267948966
φ = 0
ψ = blochstate(θ, φ)
χ = hadamard() @ ψ
probabilities(χ)
density(χ)
bloch(χ)
expect(pauliZ(), χ)
```

Click **Qubit** to create a state. Angle mode adds θ/φ slider variables; amplitude mode accepts expressions such as `1` and `i` and normalizes the pair. The Qubit view lets you select any physically valid state result, including normalized ordinary vectors or valid density matrices. It displays computational-basis probabilities, purity, entropy, and (for one qubit) a Bloch sphere. This is a numerical simulator with exact-state probabilities, not a connection to quantum hardware or a random-shot measurement/collapse tool.

### State and gate functions

| Expression | Meaning |
| --- | --- |
| `qubit(α, β)` | Normalize two nonzero-together amplitudes |
| `blochstate(θ, φ)` | Construct a pure qubit from scalar real angles, in radians |
| `ket0()`, `ket1()` | Computational basis vectors `[1,0]`, `[0,1]` |
| `basis(k, n)` | Basis vector with index k for an n-qubit register; n defaults to 1 |
| `state(v)` | Normalize a vector with 2, 4, 8, 16, or 32 amplitudes |
| `normalize(v)` | Normalize any nonzero vector up to 32 entries |
| `density(ψ)`, `projector(ψ)` | Form `ψ ψ†`; an already valid density matrix is accepted unchanged |
| `probabilities(ψ)` | Computational-basis probabilities |
| `bloch(ψ)` | One-qubit Bloch vector; accepts a density matrix too |
| `hadamard()` | Hadamard gate `(X+Z)/sqrt(2)` |
| `pauliX()`, `pauliY()`, `pauliZ()` | Pauli gate matrices |
| `Sgate()`, `Tgate()` | Phase gates `diag(1,i)` and `diag(1,exp(i*pi/4))` |
| `Rx(θ)`, `Ry(θ)`, `Rz(θ)` | Rotation `cos(θ/2)I − i sin(θ/2)σ` |
| `CNOT()` | Two-qubit controlled-X with the leftmost qubit as control |
| `expect(O, ψ)` | Operator expectation `Tr(ρ O)`; use Hermitian O for an observable |
| `purity(ψ)` | `Tr(ρ²)` |
| `entropy(ψ)` | Von Neumann entropy in bits |
| `fidelity(ψ, χ)` | Pure-state fidelity `abs(inner(ψ,χ))^2` |
| `reduced(ψ, k)` | Trace out all qubits except k; leftmost qubit is index 0 |
| `evolve(ψ, H_0, t)` | Evolution by `exp(-i*t*H_0)`; H_0 must be Hermitian, ℏ=1 |

`H(A)` still means conjugate transpose; use `hadamard()` for the Hadamard gate. Apply a gate to a vector with `U @ ψ`; apply it to a density matrix with `U @ ρ @ H(U)`. The `evolve` function handles either representation. Gate angles and evolution times are evaluated as scalars at each plot coordinate, so time-dependent vector and matrix functions can be plotted; worksheet sliders also remain available.

### Bell states and tensor ordering

```text
ψ = CNOT() @ tensor(hadamard() @ ket0(), ket0())
probabilities(ψ)
ρ_0 = reduced(ψ, 0)
ρ_1 = reduced(ψ, 1)
entropy(ρ_0)
```

The result is `( |00⟩ + |11⟩ )/sqrt(2)` with probabilities `[0.5, 0, 0, 0.5]`. Each reduced qubit is `I/2`: its Bloch vector is at the center, purity is 0.5, and entropy is 1 bit. A multi-qubit register is shown as a probability chart; use `reduced` to visualize individual qubits.

`tensor(a,b)` places a on the left: `tensor(ket0(),ket1())` is `|01⟩`. This matches the left/right tensor-factor convention in [IBM's tensor-product examples](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/qiskit-implementation). This app indexes retained qubits from the left and labels basis states in ascending binary order; do not assume another framework's qubit-index convention when copying circuits.

A register is limited to five qubits (32 amplitudes); matrices remain limited to 32×32. Non-normalized inputs to physical-state operations are rejected: use `state(v)` explicitly. Density matrices must be finite, Hermitian, positive semidefinite, and trace-one within tolerance 1e-9. Zero vectors, incompatible operator dimensions, invalid density matrices, and oversized tensor products produce row errors. Dirac notation in the UI is descriptive; it is not additional expression syntax.

## Multiplying vectors and matrices

```text
A = [[1, 2], [3, 4]]
v = [2, 1]
A * v
v @ A
outer(v, v)
bra([1, i]) @ col([1, i])
```

These give `[4,10]`, `[5,8]`, `[[4,2],[2,1]]`, and `[[2]]`, respectively.

| Input | Operation |
| --- | --- |
| `A @ B` or `A * B` | Matrix product |
| `A @ v` or `A * v` | Matrix times a flat vector, interpreted as a column for multiplication |
| `v @ A` or `v * A` | Flat vector times matrix, interpreted as a row for multiplication |
| `u @ v` or `dot(u,v)` | Bilinear dot product, no conjugation |
| `inner(u,v)` | Complex inner product, conjugating u |
| `u * v` | Entrywise multiplication of two flat vectors, preserving existing behavior |
| `hadamard_product(A,B)` | Entrywise product of equal-shape matrices or vectors |
| `outer(u,v)` | Outer product `u vᵀ`, no conjugation; use `outer(u,conj(v))` for `u v†` |
| `tensor(u,v)` or `kron(u,v)` | Kronecker product of two vectors, or of two matrices |
| `col(v)`, `row(v)` | Explicit column or row matrix |
| `bra(v)` | Conjugated row matrix |
| `matmul(a,b)` | Explicit vector/matrix multiplication with shape validation |
| `2 * v`, `2 * A` | Scalar scaling |

Mixed-rank tensor products require an explicit shape, such as `tensor(A,col(v))`. The tensor size is checked before allocation. Vectors are tagged separately from graph-coordinate arrays so these algebra rules do not change sampled scalar graph multiplication.

The **Qubit & gates**, **Bell state**, and **Vector–matrix products** examples are available in the Examples menu. Light/dark mode, equation reordering, Greek notation, and calculus remain available. Browser interaction and visual rendering remain untested in this environment.


## Vector and matrix functions

Use the **Function** creator's formula templates, or type definitions directly:

```text
φ_1 = [1, i]
w(t) = exp(i*t)
Φ_1(t) = φ_1 * w(t)
v(t) = [cos(t), sin(t)]
R(t) = [[cos(t), -sin(t)], [sin(t), cos(t)]]
q(t) = R(t) @ v(t)
q(0)
M(s, t) = [[s, t], [-t, s]]
M(1, 2)
g(t) = M(t, 1)[0, 1]
```

A function infers its output shape from its formula. References, complex coefficients, mixed constant/variable entries, matrix products, integer matrix powers, matrix exponentials, and scalar contractions all compose with user functions. Direct scalar calls display the resulting vector or matrix; matrix results retain Heatmap and other applicable actions. Calculus applies to entries, for example `d(t) = diff(v(t), t)` and `F(t) = integrate(v(s), s, 0, t)`.

Each sampled vector/matrix function displays a **plot entry** selector below its equation. Indices start at zero: `[0]` is the first vector entry and `[0, 1]` is matrix row zero, column one. Graph and Complex plane show all entries up to eight by default; larger outputs show the first eight. Select any individual entry, including entries beyond the initial eight. Plot legends identify the equation and entry; real and imaginary graph curves use solid and dashed lines. Two-variable Surface and complex Domain map display one selected entry at a time. Their Real/Imaginary/Magnitude/Phase selector controls the selected entry's complex component. Saved worksheets preserve entry selection.

Vector/matrix expressions are evaluated at scalar coordinates, keeping graph samples separate from algebraic dimensions. Curves use 1,000 points; array-dependent surfaces and domain maps use a 60×60 grid, reduced to 32×32 when calculus is involved. Scalar-only functions keep their faster vectorized sampler. Outputs must have a fixed shape throughout the sampled range: up to 32 vector entries or 32×32 matrix entries. Sampling has a two-million evaluation-node budget per row in addition to the per-point interpreter limit. Expensive composed functions can reach this limit. Invalid numeric values create gaps; shape changes and structural expression errors are reported on the row. Function component plots do not represent a geometric vector field or animate a Bloch sphere.

The **Vector & matrix functions** example reproduces the previously failing `Φ_1(t) = φ_1 * w(t)` expression and demonstrates a rotating vector.

## Resizing the equation pane

Drag the vertical divider between the worksheet and plot to adjust the equation pane. Focus the divider and use Left/Right arrows for 24-pixel adjustments, Home/End for the available limits, or double-click to restore 390 pixels. Escape cancels an active drag. The plot resizes with the pane. Width is saved in this browser separately from worksheet files and clamped to leave room for the plot; narrow screens retain the stacked layout.


## Functions with any number of inputs

Functions are no longer limited to two arguments. For example:

```text
f(x, y, z, t) = sin(x) * cos(y) + z^2 + t
f(1, 2, 3, 4)
v(a, b, c, d) = [a+b, c*d]
M(a, b, c, d) = [[a, b], [c, d]]
d(x, y, z, t) = diff(f(x, y, z, t), z)
```

Use the Function editor's **Arguments (comma-separated)** field, or type the definition directly. Function calls require exactly the declared number of arguments. Arguments must be distinct valid names after notation/Greek normalization and cannot use reserved constants or built-in function names. At least one argument is required. There is no separate argument-count cap; existing 1,200-character expression, 300-AST-node, request-size, and evaluation limits still apply.

A graph can show one or two changing inputs at a time. By default, a many-input function plots its first two arguments and fixes the others at zero. Expand **Plot inputs** beneath its equation to select any two arguments for a real surface, or choose **None — curve / domain** for the second axis to plot just one argument. Enter real numeric values for every remaining input. Fixed values do not use same-named worksheet variables automatically. They are saved with the worksheet and do not alter ordinary function calls. Input ranges control the selected axes. Domain map uses a complex value for the one selected argument and holds all others at their real fixed values.

The same selections work for scalar-, vector-, and matrix-valued functions. Output-entry controls continue to select which vector/matrix entries to draw. The calculus creator accepts the full argument list and lets you differentiate or integrate with respect to any one argument. For ordinary calls, arguments may also be complex scalars, vectors, or matrices when the formula accepts them.

The API accepts an optional per-expression `plot_slice`:

```json
{
  "expressions": [{
    "text": "f(a,b,c,d)=a+2*b+3*c+4*d",
    "plot_slice": {"axes": ["d", "b"], "fixed": {"a": 5, "c": 7}}
  }],
  "bounds": [-2, 2, -2, 2]
}
```

Use one or two distinct declared names in `axes`. Omitted fixed inputs default to zero; fixed values must be finite real numbers within ±1,000,000. `function.parameters` contains every declared input; `plot_slice` describes the effective selection and fixed values. For surfaces, `parameters` lists the two plotted inputs. Invalid selections produce an error on the affected row.

## Automatic Greek keywords

All 24 English Greek-letter names automatically become their lowercase symbols. English keyword matching is case-insensitive: `alpha`, `Alpha`, and `ALPHA` all become `α`. Actual Greek uppercase symbols such as `Α` stay uppercase.

```text
alpha_1 = 2                 → α_1 = 2
omega(theta) = alpha_1*theta → ω(θ) = α_1*θ
lambda = 3                 → λ = 3
```

Conversion happens when a keyword is completed by a delimiter, pasted, or the field loses focus. Waiting for word completion lets you type identifiers such as `alphabet` normally. Greek conversion works in equation rows, function/calculus fields, matrix cells, and qubit names/amplitudes. Cursor and text-selection positions are adjusted after replacement. Function arguments and subscripted bases are recognized: `theta_1`, `theta_{1}`, and `theta₁` refer to `θ_1` after normalization. Longer identifiers such as `alphabet`, `alpha2`, and `my_alpha` are unchanged; a Greek base followed by an underscore is converted, as in `alpha_rate` → `α_rate`.

Backend parsing applies the same keyword aliases to API requests and imported worksheets. English and Greek spellings therefore name the same value; defining both `alpha` and `α` is a duplicate. `pi` converts to the reserved constant `π`; use the actual uppercase `Π` for a separate variable. `GET /api/symbols` includes a `keywords` mapping alongside the existing alphabet and variants. To run the frontend conversion checks, use `node tests/test_greek_input.js`.


## Calculus studio: multivariable and vector calculus

Open **∫ Calculus**, or click **Calculus** below a function. The studio includes:

- Operation-specific instructions and checkboxes for calculus variables, in argument order.
- **Evaluate at point**, which previews a scalar, vector, or matrix and its estimated error before adding a row.
- **Add as → Reusable function / expression** or **Value at a point**. Point coordinates follow the full argument list, including arguments not being differentiated.
- An optional derivative step, absolute integration tolerance, and relative integration tolerance under **Numerical controls**.
- Preservation of a source function's plot-input selection and fixed values when adding a derived function. Matrix point results open Heatmap.

All operators below are numerical. In the formulas, `vars=[x,y,z]` specifies coordinate order, and `point=[1,2,3]` optionally supplies values in that same order. If `point` is omitted, current function arguments or worksheet definitions supply the values. Multivariable operators accept 1–32 selected coordinates; the original function can still have more arguments.

| Syntax | Meaning and output |
| --- | --- |
| `grad(f, vars[, point, step])` / `gradient(...)` | Scalar gradient: ∇f = [∂f/∂x₁, …, ∂f/∂xₙ] |
| `jacobian(F, vars[, point, step])` | Matrix J with J[i,j] = ∂F[i]/∂x[j]; scalar output has one row |
| `hessian(f, vars[, point, step])` | Scalar Hessian H[i,j] = ∂²f/(∂x[i]∂x[j]) |
| `mixed_diff(f, [x,y][, point, step])` | Scalar mixed partial ∂²f/(∂x∂y); exactly two distinct variables |
| `divergence(F, vars[, point, step])` | ∇·F = sum of ∂F[i]/∂x[i]; vector length must match coordinate count |
| `curl(F, [x,y,z][, point, step])` | Three-component curl in right-handed coordinate order |
| `laplacian(f, vars[, point, step])` | Sum of second coordinate derivatives, applied to each output entry |
| `directional(f, vars, direction[, point, step])` | Dᵥf = Jv along a real direction, without normalizing v |
| `at(expression, vars, point)` | Evaluate an expression with all listed variables bound to the supplied coordinates |

The Jacobian flattens matrix outputs in row-major order and supports up to 32 output entries, giving at most a 32×32 matrix. Gradients and Hessians require scalar outputs. Directional derivatives and Laplacians support scalar, vector, and matrix outputs. Curl requires exactly three variables and a three-component vector. Its components are `[dFz/dy-dFy/dz, dFx/dz-dFz/dx, dFy/dx-dFx/dy]`.

### Energy example

```text
E(x,y,z) = x^2 + 2*y^2 + 3*z^2 + x*y
g(x,y,z) = grad(E(x,y,z), [x,y,z])
g(1,2,3)
hessian(E(x,y,z), [x,y,z], [1,2,3])
laplacian(E(x,y,z), [x,y,z], [1,2,3])
directional(E(x,y,z), [x,y,z], [1,0,0], [1,2,3])
```

The gradient at `[1,2,3]` is approximately `[4,9,18]`. The Hessian is `[[2,1,0],[1,4,0],[0,0,6]]`, the Laplacian is 12, and the derivative along `[1,0,0]` is 4. This example is included under **Energy gradient & Hessian**. A **Vector calculus** example demonstrates a Jacobian, divergence, and curl.

### Complex, matrix, and point calculations

```text
grad(y*exp(i*x), [x,y], [1,2])
jacobian([[x,y],[x*y,x^2]], [x,y], [2,3])
at(diff(a*x^2+b*y, x), [a,b,x,y], [2,3,4,5])
at(grad(a*x^2+b*y, [x,y]), [a,b,x,y], [2,3,4,5])
at(mixed_diff(x^3*y^2, [x,y]), [x,y], [2,3])
integrate([[t^2,i*t],[0,sin(t)]], t, 0, 1, 1e-10, 1e-9)
```

The first point-binding derivative above equals approximately 16. The gradient equals `[16,3]`; the mixed partial equals 72. Complex outputs use real-direction coordinate perturbations, including at complex coordinates. These are not Wirtinger derivatives or a test of holomorphicity. `at` creates local bindings and does not modify worksheet definitions.

### Numerical behavior and limits

First and repeated-coordinate second derivatives retain the five-point central stencils with two step sizes. Gradients, Jacobians, divergence, curl, and Laplacians assemble the corresponding coordinate derivatives. Hessians use those second derivatives on the diagonal and centered mixed differences at two step sizes off the diagonal, with Richardson extrapolation. Symmetric Hessian entries share the same calculation. Repeated function samples are cached within each multivariable calculation.

Diagnostics include the most recent operation, selected variables, estimated error, number of distinct evaluations, and undefined-entry count. Matrix Jacobian diagnostics also record the original output shape. Errors are numerical estimates, not certified bounds; cancellations, branch cuts, nonsmooth functions, and noisy inputs can defeat the checks. Steps too small to change the evaluation point are rejected. Choose a larger step or rescale poorly conditioned inputs.

`integrate` now optionally accepts absolute and relative tolerances after the upper bound. Defaults remain `1e-8` and `1e-7`. Absolute tolerance must lie between `1e-12` and `1`, and relative tolerance between `0` and `1`. Integration still requires finite real bounds and uses adaptive quadrature, including for complex and array outputs. Nested integrals can express multiple integrals within the existing depth and evaluation budgets; there is no automatic improper-integral or singularity-splitting solver.

Plots involving array-dependent calculus use a 32×32 surface/domain grid and 1,000 curve samples. Other sampling resolutions are unchanged. Existing row budgets and a maximum of three nested numerical calculus operations remain in force; `at` is a local binding operation and does not add a numerical nesting level. Large Hessian fields or nested integrals may exceed the sampling budget; evaluate at a point or reduce the expression. This studio does not add symbolic differentiation, symbolic antiderivatives, or arbitrary-order derivative stencils.

Run `python -m pytest -q`, `node tests/test_calculus_editor.js`, and `node tests/test_greek_input.js` for the supplied checks. Browser interaction and visual rendering were not tested in this environment.


## Importing datasets

Click **Import data** in the header. Choose a UTF-8 CSV/TSV file, or paste a table, then click **Preview table**. CSV files are previewed automatically after choosing a file. Configure the comma, semicolon, or tab separator; automatic detection is the default. Turn off **First row contains headers** for files containing only values. Decimal commas are supported with semicolon/tab separation.

For example, paste this table:

```csv
time,value
0,1
1,2
2,4
3,8
```

1. Review the first eight rows. Select numeric columns to import and adjust their variable names.
2. Name the dataset, for example `data_1`. Its columns become `data_1_time` and `data_1_value`. Greek names and subscripts are supported.
3. Select an X column (or zero-based row index), up to eight Y columns, and points, lines, or lines with points.
4. Click **Import dataset**. The Graph view overlays the data with equations and fits the selected points when they are within the graph's supported range.

The **Datasets** section above the equation list provides visibility, X/Y column selections, plot style, fit, and removal controls. Click a column's variable name to add an equation using it. A standalone column plots against row index; use `points(x_column, y_column)` for a transformed XY dataset. Lines follow file row order and do not sort X values.

### Calculations with imported columns

```text
mean(data_1_value)
median(data_1_value)
std(data_1_value)
variance(data_1_value)
count(data_1_value)
f(t) = 2*t + 1
f(data_1_value)
points(data_1_time, 2*data_1_value)
points(data_1_time, f(data_1_value))
s(t) = interp(t, data_1_time, data_1_value)
s(1.5)
integrate(s(t), t, 0, 3)
```

`std` and `variance` use population statistics (ddof=0). Dataset columns are observation sequences, separate from algebraic vectors and matrices, so the matrix size limit does not restrict them to 32 rows. Arithmetic and compatible scalar functions operate entry by entry; indexing uses zero-based indices. Column results display a short value preview, finite count, and missing/undefined count.

`interp(t, x_column, y_column)` builds piecewise-linear interpolation over strictly increasing, finite real X values with matching finite Y values. It requires at least two points, preserves complex Y values produced by equations, and returns gaps outside the data range. Repeated/unsorted X values or missing values are rejected. Calculus applied to an interpolant remains numerical: slopes can be discontinuous at data knots, and derivatives at those knots may be flagged.

### Missing values and validation

Blank cells remain missing (`null` in saved JSON and NaN during calculation). X/Y points with either coordinate missing are omitted together, and line plots break at those rows. Zero is a valid observation. Fully blank lines are ignored. Columns containing nonnumeric text, dates, infinities, or NaN strings are shown in the preview but disabled for numeric import. Blank-only columns are also disabled. Nonnumeric values are not silently coerced to zero.

Statistics such as `mean` and `sum` propagate missing values. To exclude missing/non-finite observations explicitly, use `mean(dropna(data_1_value))`. `count(column)` counts finite observations. Do not independently drop missing values from paired columns, since doing so can misalign rows; the dataset plots and `points` preserve pairing automatically.

Malformed quoting and inconsistent row widths report an import error. Imported column names cannot overwrite existing equation/function definitions. Removing a dataset leaves equations in place; references to its removed columns then show unknown-variable errors.

### Saving and limits

**Save worksheet** embeds datasets and plot selections in version-5 worksheet JSON. **Open** restores them; older worksheets without datasets remain compatible. Browser autosave includes imported values and reports a storage-capacity failure with a prompt to download the worksheet. Files are sent only to the running Flask application for parsing; the app does not store uploaded source files on its server.

Limits are 1 MB per CSV/TSV import, 10,000 data rows, 32 columns per dataset, eight datasets, and 50,000 dataset cells across the worksheet. Worksheet/API requests may be up to 2 MB. Import supports finite real numeric cells within ±1e100, but graph bounds remain within ±1,000,000 with a maximum span of 1,000,000. Scale very large values in a `points(...)` expression to display them. Existing 32×32 algebraic matrix limits remain in force; imported data does not bypass them. Excel workbooks, date-axis parsing, and regression fitting are not included in this import feature.

### Dataset API

`POST /api/datasets/preview` accepts `text`, optional `delimiter` (`auto`, `,`, `;`, or a tab), `header` (boolean), and `decimal` (`.` or `,`). It returns the detected delimiter, row count, preview cells, and columns with suggested names, numeric values, missing counts, and invalid counts.

Pass the chosen columns in the `datasets` array on **every** `/api/evaluate` request, including function/calculus validation calls:

```json
{
  "datasets": [{
    "id": "dataset-1",
    "name": "data_1",
    "columns": [
      {"name": "time", "label": "Time", "values": [0, 1, 2]},
      {"name": "value", "label": "Value", "values": [1, null, 4]}
    ],
    "x": "time",
    "y": ["value"],
    "style": "markers",
    "visible": true
  }],
  "expressions": [{"text": "mean(dropna(data_1_value))"}],
  "bounds": [-1, 3, -1, 5]
}
```

The evaluation API remains stateless. Column results use `kind: series`; `points(...)` results use `kind: data_plot`. Dataset validation errors return HTTP 400; equation errors remain local to their rows. Run the additional frontend checks with `node tests/test_dataset_tools.js`.


## Integral functions and mathematical previews

Equation rows and the function editor render native MathML with stacked fractions, integral limits, subscripts, superscripts, and matrix brackets. Previews support both the new notation and existing `integrate(...)` / `diff(...)` calls. They update while you type and show the source text when a draft is incomplete. Rendering is offline and depends on your browser's MathML support.

For the integral-function example, enter each definition on its own row:

```text
S_1(x) = x
Q_1(t,x,φ) = -t*x + i*φ
π_1(t,θ,φ) = ∫_{0}^{θ} (S_1(x)*exp(Q_1(t,x,φ))) dx
π_1(0,2,0)
C(t) = t^3
d/dt(C(t))
```

The point result is approximately 2. The preview displays the integrand's `exp(...)` as a power of e. Function arguments remain independent of the local integration variable: here `x` is integrated out and `t`, `θ`, and `φ` are parameters. Use **Plot inputs** to choose which parameters vary.

| Input | Meaning |
| --- | --- |
| `∫_{a}^{b} (f(t)) dt` | Definite integral with explicit limits |
| `F(x) = ∫_{0}^{x} (sin(t)) dt` | Integral-defined function with a variable upper limit |
| `F(x) = ∫ (sin(x)) dx` | Numerical primitive anchored at zero |
| `F(x) = antiderivative(sin(x), x, 1)` | Numerical primitive anchored at 1 |
| `d/dx(f(x))` | First numerical derivative at the current x |
| `d^2/dx^2(f(x))` or `d²/dx²(f(x))` | Second numerical derivative |
| `g(t) = d/dt(C(t))` | Reusable derivative function |
| `diff(C(t), t, 2)` | Derivative evaluated at t = 2 |

A bare `d/dt(C(t))` plots against `t` when `t` is unbound; a defined `t` supplies a point value. The **∫** and **d/dx** insert buttons provide editable templates. Calculus studio includes **Integral function (primitive)** with an editable base point. An integral without written bounds means a specific numerical primitive, with value zero at its base point; its preview displays those bounds. Add your own constant for another member of the antiderivative family.

Use explicit multiplication and parentheses around compound integrands. Bounds may use braces, and nested integrals are supported within the existing calculus budgets. Limited pasted LaTeX integral/Greek/derivative commands are normalized, but this is not a general LaTeX input editor. Calculations remain numerical with finite real integration bounds; formatting does not add symbolic calculus.

`POST /api/preview` accepts `{"expressions": ["F(x)=∫_{0}^{x} (sin(t)) dt"]}` and returns a `previews` array of MathML trees or per-expression errors. It only parses notation and does not evaluate expressions.

## Linear algebra studio

Click **Linear algebra**, or the matching action below a matrix result. Enter a matrix literal, a worksheet matrix name such as `A`, or a matrix-valued function call such as `M(1,2)`. Choose a view and click **Analyze**. Optionally supply a right-hand side `b`. **Add to worksheet** inserts an editable expression for any displayed factor or solution.

The studio supports real and complex matrices up to 32×32. Rectangular matrices support SVD, QR, LU, subspaces, and least-squares; eigenpairs and Cholesky require square matrices.

| Worksheet expression | Result |
| --- | --- |
| `eigvals(A)` / `eigenvalues(A)` | Eigenvalues ordered by real, then imaginary part |
| `eigvecs(A)` / `eigenvectors(A)` | Matching unit-length eigenvectors in columns |
| `diag(v)` / `diag(A)` | Diagonal matrix from a vector / diagonal entries from a matrix |
| `svdU(A)`, `svdS(A)`, `svdVh(A)` | Economy SVD factors with `A ≈ U @ S @ Vh` |
| `singular_values(A)` | Singular values in descending order |
| `qrQ(A)`, `qrR(A)` | Reduced QR factors with `A ≈ Q @ R` |
| `luP(A)`, `luL(A)`, `luU(A)` | Pivoted LU factors with `A ≈ P @ L @ U` |
| `cholesky(A)` | Lower triangular L with `A ≈ L @ H(L)` for Hermitian positive-definite A |
| `nullspace(A)` | Orthonormal basis of the null space, in columns |
| `orth(A)` | Orthonormal basis of the column space, in columns |
| `rank(A)`, `nullity(A)` | Numerical rank / number of null-space basis vectors |
| `cond(A)` | 2-norm condition number; reports an error for numerical rank deficiency |
| `lstsq(A,b)` | Minimum-norm least-squares solution for a vector or matrix right-hand side |
| `solve(A,b)` | Existing direct square-system solver |

Example:

```text
A = [[2,1],[1,3]]
λ = eigvals(A)
V = eigvecs(A)
A @ V - V @ diag(λ)
B = [[1,2,3],[2,4,6]]
N = nullspace(B)
B @ N
svdU(B) @ svdS(B) @ svdVh(B)
lstsq(B, [1,2])
```

The eigenpair residual and `B @ N` should be close to zero. The SVD product reconstructs `B`. For an m×n matrix with k = min(m,n), economy factors have shapes m×k, k×k, and k×n. `H` denotes the conjugate transpose, including for complex matrices.

The studio reports rank, nullity, norm, condition number, and reconstruction residuals. Square matrices also show trace, determinant, Hermitian/unitary checks, and whether the returned eigenvectors form a complete basis at numerical tolerance. A defective matrix can have a small eigenpair residual without an invertible eigenvector basis; the studio flags this. Repeated eigenvalues can have different valid bases, and eigenvectors are only defined up to scale/phase. Exactly Hermitian input uses a Hermitian eigensolver. Numerical rank, conditioning, and diagonalizability diagnostics are floating-point assessments, not symbolic proofs.

A zero-dimensional subspace is displayed as an empty basis: for example, `nullspace(eye(2))` is a 2×0 matrix. Computed empty bases can participate in compatible matrix products; empty matrix literals remain unsupported. Least-squares reports the residual norm and whether the system is consistent within numerical tolerance. Reconstruction residuals use `norm(A-reconstruction)/max(1,norm(A))`.

`POST /api/linear-algebra` accepts `matrix`, optional `rhs`, and the worksheet's `expressions` and `datasets`, returning an `analysis` object. For example:

```json
{"matrix":"A", "rhs":"[1,2]", "expressions":[{"text":"A=[[2,1],[1,3]]"}]}
```

The **Eigenvectors & decompositions** and **Integral functions & d/dt** examples are included in the Examples menu. Additional frontend preview checks run with `node tests/test_math_preview.js`.


## Creating various graphs

Click **＋ Create graph**. Select a graph type, give it a name and color, enter the formulas or data, and choose a sampling range. Defaults provide an editable example of every graph type. **Create graph** checks the formulas against your current worksheet before saving the graph.

| Graph type | Fields and example |
| --- | --- |
| Cartesian curve | y(x): `sin(x)`; x range: −6 to 6 |
| Parametric curve | x(t): `2*cos(t)`; y(t): `sin(t)`; t: 0 to `6.283185307179586` |
| Polar curve | r(θ): `2*cos(3*θ)`; θ: 0 to `6.283185307179586` |
| 3D parametric curve | x(t): `cos(t)`; y(t): `sin(t)`; z(t): `t/4` |
| Implicit curve | `x^2+y^2=4` or the zero-level expression `x^2+y^2-4` |
| 3D surface | z(x,y): `sin(x)*cos(y)` |
| Contour map | f(x,y): `x^2+y^2` |
| Scatter plot | X: `data_1_time`; Y: `data_1_value` |
| Line chart | X: `[0,1,2,3]`; Y: `[1,3,2,4]` |
| Bar chart | X: `[1,2,3,4]`; heights: `[3,7,4,6]` |
| Histogram | Values: `sample(normal(0,1),1000,42)`; 20 bins |
| Probability distribution | `D` or `normal(0,1)`; density/mass or CDF; x range |

Range inputs take numeric values; formula fields accept mathematical expressions and Greek names. Parametric formulas use the name in **Parameter**, even if the example label shows t. Polar angles are in radians; negative radii are allowed. Polar curves are rendered in Cartesian coordinates using x = r cos(θ), y = r sin(θ).

Coordinate formulas can call existing functions or select vector/matrix entries. For a worksheet definition `v(t)=[cos(t),sin(t)]`, use `v(t)[0]` and `v(t)[1]` as parametric coordinates. Surface and contour formulas can use slices of any many-input function, such as `f(x,y,2,0)`. Changing a worksheet parameter or dataset recalculates dependent graphs.

Created graphs appear in the **My graphs** collection below the toolbar. Each card provides visibility, Rename, editing, and deletion controls. Click its name to display it individually, or select **All 2D graphs** / **All 3D graphs** in the plot toolbar to overlay compatible graphs. 2D and 3D groups use separate coordinate systems. Legend clicks temporarily toggle traces; the card checkbox saves visibility in the worksheet. Multiple surface overlays use partial transparency.

Pan/zoom in My graphs changes the viewing range. Edit a graph to change its sampling domain. **Reset view** fits the sampled 2D data or resets the 3D camera. **PNG** exports the current plot. Worksheet JSON and browser autosave include graph definitions, colors, visibility, and the selected graph/group. Worksheets from earlier versions remain supported.

Data charts accept numeric vectors or dataset columns, including transformed columns. Leave X blank to use zero-based row indices. Line charts preserve input order. Missing X/Y observations are omitted together; line gaps remain gaps. Histograms omit non-finite observations and report their count. Bar-chart X values are numeric; category-string axes are not part of this version.

Graphs support 12 saved definitions, 50–1,000 samples per curve, 60×60 grids (32×32 for calculus), 1–100 histogram bins, and up to 10,000 data observations. Each graph has a 500,000 interpreter-node sampling budget plus the existing per-evaluation budget. Non-finite or non-real curve/grid samples create gaps; select `real(...)`, `imag(...)`, or `abs(...)` explicitly for complex outputs. Sampling does not guarantee detection of every pole or narrow feature; a line can bridge a discontinuity between finite samples.

`POST /api/graphs` accepts `graphs`, worksheet `expressions`, and `datasets`. Each result is keyed by graph `id`; formula errors are isolated per graph, while invalid specification structure returns HTTP 400. For example:

```json
{
  "graphs": [{
    "id": "ellipse", "name": "Ellipse", "type": "parametric",
    "color": "#2864d7", "visible": true,
    "parameter": "t", "range": [0, 6.283185307179586], "samples": 400,
    "x": "2*cos(t)", "y": "sin(t)"
  }],
  "expressions": [], "datasets": []
}
```

## Probability suite

Click **Probability** to select a family and edit its parameters. The **Distribution expression** field can also reference an existing distribution or use worksheet parameters. Select a calculation, enter its arguments, and click **Calculate**. The studio displays the result, summary statistics, and a density or mass plot. **Add definition** saves a named distribution; **Probability** below a distribution row reopens it for editing. **Save density / mass graph** and **Save CDF graph** add editable graphs to My graphs.

| Constructor | Parameters and convention |
| --- | --- |
| `D = normal(μ, σ)` | Mean μ, positive standard deviation σ; defaults 0 and 1 |
| `P = poisson(λ)` | Event rate / mean λ ≥ 0; support 0, 1, 2, … |
| `B = binomial(n, p)` | Integer trial count n ≥ 0 and success probability 0 ≤ p ≤ 1 |
| `Q = boltzmann([E_0,E_1,...], T)` | Finite real energy vector and positive temperature; default T = 1 |
| `U = uniform(a,b)` | Continuous uniform distribution with a < b; defaults 0 and 1 |
| `E = exponential(λ)` | Positive rate λ; mean 1/λ; default rate 1 |
| `G = geometric(p)` | First-success trial number, starting at 1, with 0 < p ≤ 1 |

Use positional arguments. Invalid parameters produce errors instead of silently changing the distribution. Named distributions can be used in other expressions and functions, including `f(t)=pdf(normal(t,1),0)`.

```text
D = normal(0,1)
pdf(D,0)
cdf(D,1)
prob(D,-1,1)
quantile(D,0.975)
mean(D)
variance(D)
std(D)
median(D)
entropy(D)
N = poisson(4)
pmf(N,2)
B = binomial(10,0.5)
prob(B,3,7)
f(x) = pdf(D,x)
integrate(pdf(D,t),t,-1,1)
```

Here `pdf(D,0)` is approximately 0.3989423, `prob(D,-1,1)` is approximately 0.6826895, and `quantile(D,0.975)` is approximately 1.959964. Normal's second argument is **standard deviation**, not variance. A continuous density is not a point probability and may exceed 1.

| Operator | Meaning |
| --- | --- |
| `pdf(D,x)` | Continuous probability density |
| `pmf(D,k)` | Discrete point probability; noninteger k has mass zero |
| `cdf(D,x)` | P(X ≤ x) |
| `sf(D,x)` | P(X > x), using the survival function for tail accuracy |
| `prob(D,a,b)` | P(a ≤ X ≤ b); both endpoints included for discrete outcomes |
| `quantile(D,q)` | Quantile for 0 ≤ q ≤ 1; endpoint values can be non-finite |
| `mean(D)`, `variance(D)`, `std(D)`, `median(D)` | Distribution statistics |
| `entropy(D)` | Entropy in nats; differential entropy for continuous distributions |
| `sample(D,n,seed)` | Reproducible numeric observations; seed defaults to 0 |
| `probabilities(Q)` | Complete finite Boltzmann state-probability vector |
| `expected_energy(Q)` | Mean energy of a Boltzmann distribution |

Probability functions accept real scalar or array coordinates in worksheet expressions. The studio's query inputs are scalar. `pdf` rejects discrete distributions and `pmf` rejects continuous ones. Use the probability graph type for discrete plots so masses are sampled at integer outcomes and CDFs are drawn as steps. Direct equation curves continue to use the worksheet's real-valued sampling grid.

The existing array/dataset `mean`, `variance`, `std`, and `median` operations retain their behavior. Quantum `entropy` and `probabilities` retain their existing meanings when given quantum states.

### Boltzmann states

For energy levels E₀, …, Eₙ₋₁, the suite uses

```math
P(K=k)=\frac{\exp(-E_k/T)}{\sum_j\exp(-E_j/T)},\qquad T>0,\quad k_B=1.
```

```text
Q = boltzmann([0,1,2],1)
probabilities(Q)
pmf(Q,0)
expected_energy(Q)
entropy(Q)
```

The probabilities are approximately `[0.665241, 0.244728, 0.090031]`. Energies are shifted by their minimum before exponentiation for numerical stability. Repeated energy entries are distinct states, so repetition can represent degeneracy. `mean(Q)` and `variance(Q)` concern the **state index**, while `expected_energy(Q)` concerns its energy. The energy list may contain 1–32 entries. This is a finite Gibbs/Boltzmann distribution, not a continuous Maxwell–Boltzmann speed distribution.

### Samples, plots, and limits

```text
D = normal(0,1)
observations = sample(D,1000,42)
mean(observations)
std(observations)
```

Samples are observation sequences, so they support up to 10,000 entries without the algebraic vector limit of 32. The same seed reproduces the same sample in the same environment, without changing the global random-number generator. Use `observations` in a histogram or scatter graph. Samples are regenerated from their saved expressions; sampled values are not automatically copied into imported datasets.

Default probability plots cover quantiles 0.001–0.999, with padding for degenerate distributions. Continuous plots use 500 samples; discrete plots allow at most 2,000 integer outcomes. Large-support distributions may need a narrower manual plotting range. The displayed plot is a window of the distribution; tail probability outside the window is not discarded from calculations.

Positive scale/rate/temperature parameters are bounded to 1e-12–1e12, except the Poisson rate, which allows 0–1,000,000. Binomial trials are limited to 1,000,000. Quantile endpoints can produce non-finite results, which the studio labels explicitly; ordinary scalar worksheet results report them as non-finite. This suite does not fit distributions to data or perform hypothesis testing.

`POST /api/probability` accepts a `distribution` expression, optional worksheet `expressions`/`datasets`, optional numeric `range`, and an optional query. Query arguments are mathematical-expression strings:

```json
{
  "distribution": "binomial(10,0.5)",
  "query": {"operation": "prob", "arguments": ["3", "7"]}
}
```

The response contains statistics, plot samples, and the query result. The **Probability distributions** worksheet example is included. Run `node tests/test_graph_tools.js` for graph-control checks alongside the existing frontend checks.

## Wavelet analysis of actual signals

Click **Wavelets** in the toolbar, or **Wavelets** on an imported dataset card. The studio analyzes measured numeric observations, rather than only drawing the wavelet's shape.

1. Use **Import data** to load a CSV/TSV containing your signal. Numeric columns can represent sensor readings, recorded amplitudes, prices, returns, or another measured sequence. Select the signal column in **Choose imported signal**.
2. Supply a numeric time column, or enter the sample spacing Δt. For 128 samples per second, use Δt = `0.0078125` and **Seconds**. The displayed frequencies are then in Hz. For daily observations counted by trading session, use Δt = `1` and **Samples**; frequencies are cycles per observation rather than calendar-day frequencies.
3. Set missing-data and detrending options. Missing values are rejected by default. **Interpolate interior gaps** fills values without deleting their time positions. Missing first/last values must be fixed or trimmed beforehand.
4. Choose the continuous wavelet and scales for a time–scale power map. Choose the discrete wavelet, levels, and threshold controls for reconstruction and denoising.
5. Click **Analyze signal**. Inspect the raw signal and reconstructed/denoised curves, the wavelet power map, average power by scale, and reconstructed approximation/detail bands.
6. Select an output and click **Add output as dataset** to reuse it in equations and graphs. **Save worksheet** preserves that result dataset. Download a full signal/band CSV, analysis JSON, or power-map PNG from the studio.

The signal can also be a worksheet expression, for example `data_1_value`, `real(data_1_value)`, `data_1_value - mean(data_1_value)`, or a vector of at least eight values. Use **Paste signal values** for a single column of numbers without headers, separated by spaces, commas, semicolons, or newlines. Pasted samples take precedence over the expression field. They are transient until exported or added as an output dataset; use CSV/TSV import to retain the complete raw input in a saved worksheet.

No measured recording is bundled. **Load synthetic demo** produces a clearly labeled, reproducible 512-sample signal: a 6 Hz oscillation changes to 20 Hz halfway through, with a persistent 2 Hz component and seeded noise. It is sampled at 128 Hz and is intended to demonstrate time localization.

### Sampling and preparation

Time must be finite, strictly increasing, and match the signal length. If time is supplied, its spacing determines Δt. Duplicate or reversed times produce an error. Small floating-point spacing differences are tolerated; irregular sampling requires the explicit **Resample irregular times linearly** option. Resampling creates the same number of points uniformly between the first and last timestamps. It changes the signal through interpolation; it is not a nonuniform wavelet transform. Numeric elapsed times are supported; date strings and audio containers such as WAV/MP3 must first be converted to numeric samples.

For **Mean** detrending, the mean is removed before the transforms. **Linear trend** removes a fitted straight line. Reconstruction and denoised outputs restore the removed baseline, so they remain in the input signal's units. The **prepared** output and individual DWT bands exclude the baseline. Raw observations and their original time coordinates remain available in the JSON export. Interpolation and resampling are reported in the analysis summary.

### Continuous wavelet transform

The CWT uses scaled and translated wavelets to locate oscillations in time. In sample-index coordinates, its convention is approximately

```math
W(a,b)\approx\frac{1}{\sqrt{a}}\sum_n x_n\,\overline{\psi\!\left(\frac{n-b}{a}\right)},\qquad a>0.
```

The implementation uses PyWavelets' FFT CWT. The studio supports complex Morlet (`cmor1.5-1.0`), real Morlet (`morl`), Mexican hat (`mexh`), and the first Gaussian derivative (`gaus1`). Scale a is measured in samples. Frequencies are mapped from scale using the chosen wavelet's center frequency and Δt. Changing Δt changes the physical frequency labels; PyWavelets' coefficient values themselves use the sample-coordinate normalization. See the [PyWavelets CWT reference](https://pywavelets.readthedocs.io/en/latest/ref/cwt.html).

**Wavelet power** is `abs(W)^2`. The default view displays log₁₀ power; zero power becomes an empty log cell. This is raw wavelet power, not a calibrated power spectral density or a probability. **Average power by scale** compares the time-averaged coefficient power; its peak depends on wavelet normalization and the selected scales, so it is not a guarantee of the signal's fundamental frequency.

The transform is calculated at every input sample. To bound browser payloads, the displayed power map averages full-resolution power into at most 800 time bins. The global-power curve uses every original transform sample. JSON includes the displayed power, scales, frequency/period labels, and average-power curves; it does not include the full complex multi-scale coefficient array. Use `wavelet_cwt(signal,scale)` in the worksheet to obtain full-resolution coefficients for one scale.

CWT processing uses zero extension outside the record. Edge coefficients therefore depend on unobserved values. Dotted lines use the implemented wavelet support to mark a conservative interior at each scale. The **Interior only** average excludes these edge regions and has gaps where no interior remains. These lines are support-based guides, not a statistical significance test or a universal cone-of-influence definition.

Default scales range from 4 to `min(128, N/4)`, spaced logarithmically. Minimum scales below 2 are rejected; maximum scale is capped at `min(1024,N/2)`. A scale's mapped frequency cannot exceed the Nyquist frequency. Very short signals may require Haar for DWT and a smaller valid CWT scale range. Near-Nyquist wavelet filters can still suffer discretization effects; use scales appropriate to the signal rather than assuming all allowed scales have equal accuracy.

### Discrete wavelets, reconstruction, and denoising

The discrete transform supports **Haar**, **Daubechies 2**, **Daubechies 4**, **Symlet 4**, and **Coiflet 1**. It returns a coarse approximation and successive detail bands. In the original sample coordinates,

```math
x_{\mathrm{prepared}}[n]=A_J[n]+\sum_{j=1}^{J}D_j[n].
```

The displayed bands are reconstructed signals of the same length as the input, rather than the shorter coefficient arrays. For a J-level transform, JSON also records the coefficient arrays in the order `A_J, D_J, ..., D_1`. Inverse reconstruction uses matching boundary extension and trims an extra sample when needed for odd-length inputs. See the [PyWavelets inverse-transform reference](https://pywavelets.readthedocs.io/en/latest/ref/idwt-inverse-discrete-wavelet-transform.html).

**Symmetric** extension reflects the signal at its endpoints. **Periodization** treats the boundaries periodically; choose it only when that interpretation is appropriate. The automatic level is at most five and never exceeds the filter-length-dependent useful level, with a hard cap of ten. A signal too short for the selected filter produces an error rather than silently selecting another filter.

The detail band's approximate frequency range is `[f_s/2^(j+1), f_s/2^j]`. The approximation covers roughly `[0, f_s/2^(J+1)]`. Actual wavelet filters overlap and are not ideal brick-wall bands. Coefficient shares are squared-coefficient sums divided by their total; symmetric extension and padded lengths can prevent their interpretation as an exact partition of input energy.

Denoising keeps the approximation coefficients and thresholds the detail coefficients. The noise estimate and threshold are

```math
\hat\sigma=\frac{\operatorname{median}(|D_1-\operatorname{median}(D_1)|)}{0.67448975},\qquad
\lambda=k\hat\sigma\sqrt{2\log N}.
```

Here `D_1` denotes the finest coefficient array and k is the **Threshold multiplier**. The noise estimate is a Gaussian-noise heuristic. **Soft** thresholding both removes small coefficients and shrinks retained coefficients toward zero; **Hard** thresholding removes small coefficients and preserves larger ones. Set k = 0 to disable thresholding and check reconstruction. These modes follow the [PyWavelets thresholding definitions](https://pywavelets.readthedocs.io/en/latest/ref/thresholding-functions.html).

Reconstruction RMSE measures numerical transform/inverse accuracy. Removed-residual RMS measures how much denoising changed the signal; it is not a measurement of the true noise or an improvement score. Denoising can remove actual high-frequency structure. These are offline transforms using the full signal and two-sided filters, not causal forecasting filters.

### Wavelet formulas in equations

```text
ψ(t) = mexican_hat(t,2,0)
χ(t) = morlet(t,1,0,6)
η(t) = haar(t,1,0)
A = wavelet_approx(data_1_value,3,2)
D = wavelet_detail(data_1_value,3,2)
s = wavelet_denoise(data_1_value,1,2,3)
W = wavelet_cwt(data_1_value,8,0)
abs(W)^2
```

`mexican_hat(t,scale,shift)` is the unit-energy negative second Gaussian derivative wavelet. `morlet(t,scale,shift,omega)` uses a zero-mean correction and unit-energy normalization; omega defaults to 6. Its analytic shape is distinct from PyWavelets' parameterized complex Morlet used in the studio. `haar(t,scale,shift)` is +1 on the first half of its normalized support and −1 on the second half, with scale normalization. Scale is positive and shift is a real scalar.

| Worksheet function | Meaning |
| --- | --- |
| `wavelet_approx(values,level,wavelet_id)` | Reconstructed approximation A at the requested level |
| `wavelet_detail(values,level,wavelet_id)` | Reconstructed detail D at the requested level |
| `wavelet_denoise(values,strength,wavelet_id,level)` | Denoised signal, symmetric extension and soft thresholding; level 0 chooses automatically |
| `wavelet_cwt(values,scale,wavelet_id)` | Full-resolution CWT coefficients at one scale, possibly complex |

DWT IDs are `0=Haar`, `1=db2`, `2=db4`, `3=sym4`, `4=coif1`. Approximation/detail functions default to level 1 and Haar. Denoising defaults to strength 1, db4, and automatic level. CWT IDs are `0=complex Morlet`, `1=real Morlet`, `2=Mexican hat`, `3=Gaussian derivative`. Numeric IDs keep the expression interpreter free of arbitrary string evaluation; the studio displays the readable names.

These functions return observation sequences, retaining up to 10,000 samples rather than using the matrix/vector size limit of 32. Their inputs must be finite real samples; preprocessing controls are available in the studio. The worksheet functions themselves do not detrend or interpolate. For exact additive reconstruction, combine `wavelet_approx(s,J,id)` with `wavelet_detail(s,j,id)` for every j from 1 to J, using the same wavelet.

### Exports, persistence, and API

CSV export contains uniform time, observed/interpolated signal, prepared signal, baseline, reconstruction, denoised output, removed residual, and every reconstructed band. JSON additionally contains original coordinates and missing values, DWT coefficients, transform settings, scale/frequency mappings, and power-map data. Band outputs exclude the removed baseline; reconstruction and denoised outputs restore it.

**Add output as dataset** saves one selected output alongside its time coordinates. The regular dataset limits still apply: eight datasets and 50,000 total cells per worksheet. A 10,000-sample output uses 20,000 cells. Source expressions and studio settings are saved in version-5 worksheet JSON; older worksheets remain compatible. A full analysis report is saved through its JSON download, not embedded automatically in worksheet autosave.

Limits: 8–10,000 samples, 8–96 CWT scales, a maximum of 800 display time bins, and up to ten useful DWT levels. Short-signal restrictions depend on the wavelet filter. Sample spacing must be between 1e-12 and 1e12 in the chosen time unit. Larger records must be segmented externally; the studio does not silently truncate recordings.

`POST /api/wavelets` accepts a signal expression or a numeric sample array, optional time expression/array, worksheet definitions/datasets, and an options object. Missing numeric-array samples may use JSON null. For an imported signal:

```json
{
  "signal": "sensor_value",
  "time": "sensor_time",
  "datasets": ["...same dataset objects supplied to /api/evaluate..."],
  "expressions": [],
  "options": {
    "cwt_wavelet": "cmor1.5-1.0",
    "dwt_wavelet": "db4",
    "detrend": "mean",
    "missing": "reject",
    "resample": false,
    "min_scale": 4,
    "max_scale": 64,
    "scale_count": 48,
    "level": 4,
    "boundary": "symmetric",
    "threshold_mode": "soft",
    "strength": 1
  }
}
```

Replace the illustrative dataset placeholder with the actual dataset objects. The response has an `analysis` object containing preparation metadata, time series, and `cwt`/`dwt` results. Invalid inputs return HTTP 400 with a descriptive error. Run `node tests/test_wavelet_tools.js` alongside the existing tests to check the frontend data and export helpers.

## Built-in function palette

Click **ƒ Built-in functions** in the header or function editor. The palette includes every function in the supplied Calculus, Statistics, and Hyperbolic Trig screenshots, plus the resident wavelet functions and transforms. Search by name or category and click a tile to insert an editable template. A selection in the current equation/formula becomes the first argument; the inserted argument remains selected so you can replace it. Hover over a tile for its syntax and conventions.

The six hyperbolic functions are `sinh`, `cosh`, `tanh`, `csch`, `sech`, and `coth`. Reciprocal hyperbolic functions use `1/sinh`, `1/cosh`, and `1/tanh` respectively, including complex values. Singular inputs become undefined values or plot gaps.

### Statistics

| Input | Result |
| --- | --- |
| `mean(L)`, `median(L)` | Mean and median |
| `min(L)`, `max(L)` | List extrema; two arguments retain entrywise behavior |
| `quartile(L,q)` | Linear-interpolated quantile at q/4, with q between 0 and 4 |
| `quantile(L,p)` | Linear-interpolated data quantile; p between 0 and 1 |
| `stdev(L)`, `var(L)` | Sample standard deviation and variance, denominator n−1 |
| `stdevp(L)`, `varp(L)` | Population standard deviation and variance, denominator n |
| `cov(X,Y)`, `covp(X,Y)` | Sample/population covariance of aligned pairs |
| `mad(L)` | Mean absolute deviation from the mean |
| `corr(X,Y)` | Pearson correlation |
| `spearman(X,Y)` | Spearman correlation with average ranks for ties |
| `stats(L)` | `[minimum, Q1, median, Q3, maximum]` |
| `count(L)` | Finite-observation count |
| `total(L)` | Sum of entries |

The naming follows the [Desmos supported-functions reference](https://help.desmos.com/hc/en-us/articles/212235786-Supported-Functions), with the explicit compatibility conventions below. `mad` is mean absolute deviation; the wavelet studio's noise estimator separately uses **median** absolute deviation.

Existing `std` and `variance` remain population statistics. Existing `count` still counts finite observations, excluding missing values. Other statistics propagate missing observations rather than independently deleting paired entries. For one-column statistics, `dropna(L)` explicitly removes missing values. Paired inputs must have the same length; clean pairs together before importing. Constant lists make correlation undefined. Sample variance/covariance need at least two observations. The new order statistics, covariance, and correlations accept real lists/dataset columns up to 10,000 observations; use a component of complex data explicitly.

`quantile(D,p)` still computes distribution quantiles when D is a distribution. Existing distribution statistics and quantum `entropy`/`probabilities` remain available. List quartiles use NumPy's linear quantile convention; no claim of matching every external calculator's quartile interpolation method is made.

### Logarithms, prime derivatives, sums, and products

The palette's **ln** button inserts `ln(x)`. Its **log** button inserts `log10(x)` for the common logarithm. For compatibility with existing worksheets, `log(x)` continues to mean the natural logarithm. Use `log(x,base)`, `logbase(x,base)`, or subscript notation for another base:

```text
log10(100)
ln(exp(1))
log_2(8)
log₂(8)
a = 2
log_{a+1}(27)
f(t) = t^3
f'(2)
f′(x)
f''(t)
```

Log bases must be positive real values different from 1. Prime notation applies to defined one-argument functions and supports first/second numerical derivatives. A bare prime derivative with an unbound parameter such as `f''(t)` produces a curve; an explicit numeric argument produces a value. For built-in expressions or partial derivatives, use `d/dx(expression)` or `diff(expression,variable)`. Prime derivatives share the existing derivative stencils and numerical limits.

```text
∑_{k=1}^{4}(k^2)
∏_{k=1}^{4}(k)
summation(k^2,k,1,4)
sum(k^2,k,1,4)
product(k,k,1,4)
S(x) = sum(x^k,k,0,5)
```

The first two results are 30 and 24. Bounds are inclusive integers; the index is local and does not overwrite a same-named worksheet variable. Use an unreserved index such as k or n; i and j remain imaginary-unit constants. Parenthesize the operand in displayed ∑/∏ notation. Uppercase Greek Σ/Π also act as bounded operators when followed by an index assignment, while names such as `Σ_1` and `Π_1` remain ordinary variables.

Each reduction is limited to 10,000 terms, integer bounds within ±1,000,000, and the existing evaluation budgets. Reversed bounds give an empty sum of 0 or empty product of 1. Terms must have a consistent shape. Products preserve worksheet multiplication semantics: scalar multiplication, entrywise vector multiplication, and ordered matrix multiplication. `product(L)` / `prod(L)` with one input instead multiply its numeric entries. Formatted previews display sum/product bounds, prime marks, and logarithm bases.

## Resident wavelet transforms

Wavelet transforms now have reusable worksheet results, in addition to the signal studio and single-scale helpers:

```text
W = dwt(sensor_value,3,2)
restored = idwt(W)
coarse_coefficients = wavelet_coeffs(W,0)
coarse_signal = wavelet_band(W,0)
C = cwt(sensor_value,[4,8,16],0,0.01)
wavelet_scales(C)
wavelet_frequencies(C)
wavelet_coeffs(C,1)
wavelet_power(C,1)
```

Replace `sensor_value` with your imported signal column or a finite real vector. All mother-wavelet functions (`mexican_hat`, `morlet`, `haar`), approximation/detail helpers, denoising, coefficient extraction, and transform functions have palette entries.

| Function | Behavior |
| --- | --- |
| `dwt(signal,level,wavelet_id)` | Discrete transform object; defaults: level 0 (automatic), wavelet ID 2 (db4) |
| `wavelet_transform(...)` | Alias of `dwt` |
| `idwt(W)` / `wavelet_reconstruct(W)` | Reconstruct a DWT object to its exact original sample count |
| `cwt(signal,scales,wavelet_id,dt)` | Multiscale CWT object when scales is a list; defaults: wavelet ID 0, dt 1 |
| `cwt(signal,scale,wavelet_id)` | Single-scale coefficient sequence when scale is scalar |
| `wavelet_coeffs(W,index)` | Coefficient sequence at a zero-based band/scale index |
| `wavelet_band(W,index)` | Full-length reconstructed DWT band |
| `wavelet_power(W,index)` | Squared coefficient magnitudes at that index |
| `wavelet_scales(C)` / `wavelet_frequencies(C)` | Scale and frequency sequences from a multiscale CWT |

For DWT, index 0 is A_J, then indices 1 through J select D_J through D_1. For CWT, indices follow the supplied scale list. DWT reconstruction uses symmetric extension. The sum of every reconstructed DWT band equals the input up to floating-point error. `wavelet_coeffs` returns the shorter coefficient sequence for a DWT band; `wavelet_band` returns the reconstructed full-length signal. The transform result row offers shortcuts for coefficients, reconstruction, power, or frequencies.

CWT supports up to 96 scales supplied as an observation sequence; literal lists retain the calculator's 32-entry limit. Scales must lie between 2 and `min(1024,N/2)` and map no higher than Nyquist. Scalar-scale CWT output uses sample-coordinate normalization, so dt does not change its coefficient values; multiscale output records physical frequency labels. `idwt` explicitly rejects CWT objects: an inverse CWT has not been added. Wavelet ID mappings and signal limits are the same as the Wavelet studio section above.

Transform objects are kept in the evaluated worksheet context. Worksheet files save their defining expressions and input datasets, so they are recomputed when reopened. They do not expand into arbitrary-size algebraic matrices; coefficient/frequency accessors return observation sequences.

## Naming graphs

- **Saved graphs:** enter a name in **Create graph**, or click **Rename** on a card under **My graphs**. Names may contain spaces and Greek symbols, with a maximum of 80 characters. When displaying one saved graph, its name appears as the plot title; overlays use the names in their legend.
- **Equation graphs:** fill in **Plot name** below a plotted equation or function. This labels the graph independently of its mathematical variable/function name. Curve legends, surface/domain selectors, and applicable plot titles use that label. Clear the field to return to automatic labeling.

Names are included in **Save worksheet** and browser autosave, alongside graph definitions and settings. Renaming changes the label without changing the equation or its numeric results. Earlier worksheets without plot names remain compatible.
