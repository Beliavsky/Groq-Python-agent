# Groq-Python-agent
Python script that uses Groq to create Python programs, iterating until they run to completion. Sample output:

```
prompt:
Write a Python function that fits a finite mixture of normals with a
specified # of components to univariate data, using the EM algorithm,
and write a main program that tests it for data simulated from a known
mixture distribution. Write a function to display the parameters in a
formatted table. Use the function to display the true and estimated
parameters. Use numpy if helpful. Use the print function to
display results, using to_string() for a pandas dataframe.
Only output Python code. Do not give commentary.

model: qwen-2.5-coder-32b

Code ran successfully after 1 attempt (generation time: 2.349 seconds, LOC=55)!

Output:
  Component  True Weight  True Mean  True Covariance  Estimated Weight  Estimated Mean  Estimated Covariance
         0          0.4          0                1          0.400835        0.057349              1.097366
         1          0.6          5                1          0.599165        5.049657              0.943687


Total generation time: 2.349 seconds across 1 attempt

Run command: python main.py
```
The code generated is
```python
# Generated from prompt file: prompt_mix.txt
# Model used: qwen-2.5-coder-32b
# Time generated: 2025-03-08 16:45:03
# Generation time: 2.349 seconds
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.special import logsumexp

def fit_mixture_of_normals(data, k, max_iter=100, tol=1e-6):
    n = len(data)
    np.random.seed(0)
    means = np.random.choice(data, k)
    covariances = np.random.rand(k)
    weights = np.ones(k) / k
    r = np.zeros((n, k))
    
    for _ in range(max_iter):
        # Expectation step
        for i in range(k):
            r[:, i] = weights[i] * norm.pdf(data, means[i], np.sqrt(covariances[i]))
        r /= r.sum(axis=1, keepdims=True) 
        
        # Maximization step
        s = r.sum(axis=0)
        means = (r * data.reshape(-1, 1)).sum(axis=0) / s
        covariances = ((r * (data.reshape(-1, 1) - means)**2).sum(axis=0) / s).clip(min=1e-6)
        weights = s / n
        
        if (r.sum(axis=1) > 1 + tol).any() or (r.sum(axis=1) < 1 - tol).any():
            raise ValueError("Row normalization failed")
    
    return weights, means, covariances

def display_parameters(true_params, estimated_params):
    true_weights, true_means, true_covariances = true_params
    est_weights, est_means, est_covariances = estimated_params
    
    true_df = pd.DataFrame({
        'Component': range(len(true_weights)),
        'True Weight': true_weights,
        'True Mean': true_means,
        'True Covariance': true_covariances
    })
    
    est_df = pd.DataFrame({
        'Estimated Weight': est_weights,
        'Estimated Mean': est_means,
        'Estimated Covariance': est_covariances
    })
    
    result_df = pd.concat([true_df, est_df], axis=1)
    print(result_df.to_string(index=False))

def main():
    true_weights = np.array([0.4, 0.6])
    true_means = np.array([0, 5])
    true_covariances = np.array([1, 1])
    n_samples = 1000
    
    data = np.concatenate([
        np.random.normal(true_means[0], np.sqrt(true_covariances[0]), int(true_weights[0] * n_samples)),
        np.random.normal(true_means[1], np.sqrt(true_covariances[1]), int(true_weights[1] * n_samples))
    ])
    
    estimated_weights, estimated_means, estimated_covariances = fit_mixture_of_normals(data, len(true_weights))
    
    true_params = (true_weights, true_means, true_covariances)
    estimated_params = (estimated_weights, estimated_means, estimated_covariances)
    
    display_parameters(true_params, estimated_params)

if __name__ == "__main__":
    main()
```
