import numpy as np

class PoissonRegression:

    def __init__(self, y, X, β):
        self.X = X
        self.n, self.k = X.shape
        # Reshape y as a n_by_1 column vector
        self.y = y.reshape(self.n,1)
        # Reshape β as a k_by_1 column vector
        self.β = β.reshape(self.k,1)

    def μ(self):
        return np.exp(self.X @ self.β)

    def logL(self):
        y = self.y
        μ = self.μ()
        return np.sum(y * np.log(μ) - μ - np.log(factorial(y)))

    def G(self):
        y = self.y
        μ = self.μ()
        return X.T @ (y - μ)

    def H(self):
        X = self.X
        μ = self.μ()
        return -(X.T @ (μ * X))

class MultivariateNormal(object):
    def __init__(self):
        self.u = None
        self.sig = None
    
    @staticmethod
    def redimx(x):
        return  x[..., np.newaxis] if x.ndim ==2 else x
        
    def fit(self, x):
        x = self.redimx(x)
        self.u_ = x.mean(0)
        self.sig_ = np.einsum('ijk, ikj->jk', x-self.u_, x-self.u_)/(x.shape[0]-1)
        
    def prob(self, x):
        x = self.redimx(x)

        factor1 = (2*np.pi)**(-self.u_.shape[0]/2)*np.linalg.det(self.sig_)**(-1/2)
        factor2 = np.exp((-1/2)*np.einsum('ijk,jl,ilk->ik', x-self.u_, np.linalg.inv(self.sig_), x-self.u_))
        return factor1 * factor2

    
class GaussianMLE(object):
    # http://www.sciencedirect.com/science/article/pii/0024379585900497
    def __init__(self, X):
        # X is a numpy array of size (observations) x (variables)
        self.X = X
        self.N = X.shape[1]
        self.M = X.shape[0]
        self.mu = np.zeros(X.shape[1], dtype=np.float)
        self.sigma = np.zeros((X.shape[1],X.shape[1]), dtype=np.float)
        self.fit = False
        # index mask for conditional probability
        self.mask = np.ones(X.shape[1], dtype=bool)
        self.reverse_mask = np.zeros(X.shape[1], dtype=bool)
        self.conditional_fit = False

    def _mean(self):
        # estimate the sample mean for each variable
        mean = np.mean(self.X, axis=0, dtype=np.float)
        self.mu = mean
        return mean

    def _sigma(self):
        # estimate the variance covariance matrix
        diffs = self.X - self.mu
        dot = np.dot(diffs.T, diffs)
        sigma = dot/self.M
        self.sigma = sigma
        return sigma

    def estimate(self):
        # estimate the distribution
        self._mean()
        self._sigma()
        print('Multivariate Gaussian distribution fit with MLE')
        print('The mean vector shape is:')
        print(self.mu.shape)
        print('The variance-covariance matrix shape is:')
        print(self.sigma.shape)
        self.fit = True

    def draw(self, size=1):
        # generate a random draw from the estimated distribution
        if not self.fit:
            self.estimate()
        return np.random.multivariate_normal(self.mu, self.sigma, size)

    def _conditional_sigma(self):
        # want to partition the variance covariance matrix into
        # dependent and indepenedent var covar parts

        ind_ind = self.sigma[self.mask, :][:, self.mask]
        dep_dep = self.sigma[self.reverse_mask, :][:, self.reverse_mask]
        ind_dep = self.sigma[self.mask, :][:, self.reverse_mask]
        dep_ind = self.sigma[self.reverse_mask, :][:, self.mask]

        # pseudo inverse
        invert_ind_ind = np.linalg.pinv(ind_ind)

        self.conditional_sigma = dep_dep - np.dot(dep_ind, np.dot(invert_ind_ind, ind_dep))
        return self.conditional_sigma

    def _conditional_mean(self, independent):
        # create conditional mean

        # partition means
        dep_means = self.mu[self.reverse_mask]
        ind_means = self.mu[self.mask]

        # slice var covar
        dep_ind = self.sigma[self.reverse_mask, :][:, self.mask]
        ind_ind = self.sigma[self.mask, :][:, self.mask]
        # pseudo inverse
        invert_ind_ind = np.linalg.pinv(ind_ind)

        diff = independent - ind_means

        cond_mean = dep_means + np.dot(dep_ind, np.dot(invert_ind_ind, diff))
        self.conditional_mu = cond_mean
        return cond_mean

    def conditional_estimate(self, dependent, independent):
        # estimate a conditional distribution
        # <dependent> is the list of indices of variables that are to be drawn
        # <independent> is np array of realizations of the variables that <dependent>
        # are being conditioned on

        assert len(independent) + len(dependent) == self.N

        self.mask[dependent] = False
        self.reverse_mask = np.logical_xor(np.ones(self.X.shape[1], dtype=bool), self.mask)

        if not self.fit:
            self.estimate()

        self._conditional_sigma()
        self._conditional_mean(independent)

        print('The conditional distribution estimated. The conditional means are:')
        print(self.conditional_mu)
        print('The conditional var-covar matrix is:')
        print(self.conditional_sigma)

        self.conditional_fit = True

    def conditional_draw(self, size=1):
        # generate a random draw from the estimated conditional distribution
        if not self.conditional_fit:
            raise RuntimeError('Conditional distribution not estimated yet')
        return np.random.multivariate_normal(self.conditional_mu, self.conditional_sigma, size)