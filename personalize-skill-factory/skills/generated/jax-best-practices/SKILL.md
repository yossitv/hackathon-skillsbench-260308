---
name: jax-computing-basics
description: Expert in JAX for computational tasks with file I/O and data processing
---

# JAX Computing Basics

You are an expert in JAX for computational tasks involving file I/O, data processing, and numerical operations.

## Task Execution Framework

### Step 1: Parse Problem Definition
```python
import json
import jax.numpy as jnp
import numpy as np

# Load task definitions
with open('problem.json', 'r') as f:
    problems = json.load(f)
```

### Step 2: Process Each Task
For each problem in the JSON:
1. Read input data using `np.load()` or appropriate loader
2. Convert to JAX arrays with `jnp.array()`
3. Perform computation using JAX operations
4. Save results using `np.save()` (convert back with `np.array()`)

## Essential JAX Operations

### Array Operations
- `jnp.array()` - Convert to JAX array
- `jnp.sum()`, `jnp.mean()`, `jnp.std()` - Reductions
- `jnp.max()`, `jnp.min()`, `jnp.argmax()`, `jnp.argmin()` - Extrema
- `jnp.dot()`, `jnp.matmul()` - Linear algebra
- `jnp.transpose()`, `jnp.reshape()` - Shape manipulation

### Mathematical Functions
- `jnp.exp()`, `jnp.log()`, `jnp.sqrt()` - Element-wise math
- `jnp.sin()`, `jnp.cos()`, `jnp.tan()` - Trigonometric
- `jnp.abs()`, `jnp.sign()` - Utility functions

## File I/O Pattern
```python
# Load input
data = np.load(problem['input'])
jax_data = jnp.array(data)

# Compute (example: sum)
result = jnp.sum(jax_data)

# Save output
np.save(problem['output'], np.array(result))
```

## Common Task Types

### Reduction Operations
- Sum, mean, standard deviation across axes
- Finding maximum/minimum values
- Computing norms and distances

### Linear Algebra
- Matrix multiplication and decomposition
- Solving linear systems
- Computing eigenvalues/eigenvectors

### Element-wise Operations
- Mathematical transformations
- Conditional operations with `jnp.where()`
- Broadcasting operations

## Error Handling

### File Operations
- Check if input files exist before loading
- Handle different data formats (.npy, .npz)
- Ensure output directories exist

### Data Validation
- Verify array shapes and dtypes
- Handle empty or malformed data
- Check for NaN/inf values with `jnp.isnan()`, `jnp.isinf()`

### Computation Edge Cases
- Handle division by zero with `jnp.where()`
- Check for singular matrices in linear algebra
- Validate axis parameters for reductions

## Implementation Template
```python
import json
import jax.numpy as jnp
import numpy as np
import os

# Load problems
with open('problem.json', 'r') as f:
    problems = json.load(f)

for problem in problems:
    try:
        # Load input data
        if not os.path.exists(problem['input']):
            print(f"Input file {problem['input']} not found")
            continue
            
        data = np.load(problem['input'])
        jax_data = jnp.array(data)
        
        # Perform computation based on description
        # (Parse description and implement logic)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(problem['output']), exist_ok=True)
        
        # Save result
        np.save(problem['output'], np.array(result))
        
    except Exception as e:
        print(f"Error processing {problem['id']}: {e}")
```

## Performance Tips
- Use JAX arrays for computation, NumPy for I/O
- Avoid unnecessary data type conversions
- Use vectorized operations instead of loops
- Apply `jax.jit` for repeated computations