# Source: https://gist.github.com/rasmusab/fb69de0333fff80bb06c

# Prior to the tutorial make sure that the script below runs without error on your python installation.
# What you need is a working installation of Stan: http://mc-stan.org/ .
# For installation instructions, see here: 
# http://mc-stan.org/interfaces/pystan.html

# After installation you should be able to run this script which should output
# some summary statistics and some pretty plots, :)

# Fitting a simple binomial model using Stan
import pystan 

model_string = """
data {
  int n;
  int y[n];
}

parameters {
  real<lower=0, upper=1> theta;
}

model {
  y ~ bernoulli(theta);
}
"""

y = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
data_list = {'y' : y, 'n' : len(y)}

# Compiling and producing posterior samples from the model.
stan_samples = pystan.stan(model_code = model_string, data = data_list)

# Plotting and summarizing the posterior distribution
print(stan_samples)
stan_samples.plot()