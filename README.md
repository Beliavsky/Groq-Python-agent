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
