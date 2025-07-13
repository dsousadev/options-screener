"""
Black-Scholes-Merton Option Pricing Model

This module implements the standard Black-Scholes-Merton formula for pricing
European call and put options, along with the Greeks (Delta, Gamma, Vega, Theta, Rho).
"""

import numpy as np
from scipy.stats import norm
from typing import Tuple, Optional


class BlackScholesModel:
    """
    Black-Scholes-Merton option pricing model implementation.
    
    This class provides methods to price European options and calculate Greeks
    using the Black-Scholes-Merton formula with dividend yield adjustment.
    """
    
    def __init__(self):
        """Initialize the Black-Scholes model."""
        pass
    
    def _d1_d2(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> Tuple[float, float]:
        """
        Calculate d1 and d2 parameters for Black-Scholes formula.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Tuple of (d1, d2)
        """
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2
    
    def price_call(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Price a European call option using Black-Scholes-Merton formula.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)
        
        d1, d2 = self._d1_d2(S, K, T, r, q, sigma)
        
        call_price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price
    
    def price_put(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Price a European put option using Black-Scholes-Merton formula.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)
        
        d1, d2 = self._d1_d2(S, K, T, r, q, sigma)
        
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        return put_price
    
    def delta_call(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Delta for a call option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Delta for call option
        """
        if T <= 0:
            return 1.0 if S > K else 0.0
        
        d1, _ = self._d1_d2(S, K, T, r, q, sigma)
        return np.exp(-q * T) * norm.cdf(d1)
    
    def delta_put(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Delta for a put option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Delta for put option
        """
        if T <= 0:
            return -1.0 if S < K else 0.0
        
        d1, _ = self._d1_d2(S, K, T, r, q, sigma)
        return np.exp(-q * T) * (norm.cdf(d1) - 1)
    
    def gamma(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Gamma (same for calls and puts).
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Gamma
        """
        if T <= 0:
            return 0.0
        
        d1, _ = self._d1_d2(S, K, T, r, q, sigma)
        return np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    def vega(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Vega (same for calls and puts).
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Vega
        """
        if T <= 0:
            return 0.0
        
        d1, _ = self._d1_d2(S, K, T, r, q, sigma)
        return S * np.exp(-q * T) * np.sqrt(T) * norm.pdf(d1)
    
    def theta_call(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Theta for a call option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Theta for call option
        """
        if T <= 0:
            return 0.0
        
        d1, d2 = self._d1_d2(S, K, T, r, q, sigma)
        
        theta = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                - r * K * np.exp(-r * T) * norm.cdf(d2) 
                + q * S * np.exp(-q * T) * norm.cdf(d1))
        return theta
    
    def theta_put(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Theta for a put option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Theta for put option
        """
        if T <= 0:
            return 0.0
        
        d1, d2 = self._d1_d2(S, K, T, r, q, sigma)
        
        theta = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                + r * K * np.exp(-r * T) * norm.cdf(-d2) 
                - q * S * np.exp(-q * T) * norm.cdf(-d1))
        return theta
    
    def rho_call(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Rho for a call option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Rho for call option
        """
        if T <= 0:
            return 0.0
        
        d1, d2 = self._d1_d2(S, K, T, r, q, sigma)
        return K * T * np.exp(-r * T) * norm.cdf(d2)
    
    def rho_put(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
        """
        Calculate Rho for a put option.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            sigma: Volatility
            
        Returns:
            Rho for put option
        """
        if T <= 0:
            return 0.0
        
        d1, d2 = self._d1_d2(S, K, T, r, q, sigma)
        return -K * T * np.exp(-r * T) * norm.cdf(-d2)
    
    def implied_volatility(self, price: float, S: float, K: float, T: float, r: float, q: float, 
                          option_type: str = 'call', tolerance: float = 1e-5, max_iterations: int = 100) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Args:
            price: Observed option price
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            option_type: 'call' or 'put'
            tolerance: Convergence tolerance
            max_iterations: Maximum number of iterations
            
        Returns:
            Implied volatility or None if not found
        """
        if T <= 0:
            return None
        
        # Initial guess for volatility
        sigma = 0.5
        
        for _ in range(max_iterations):
            if option_type.lower() == 'call':
                price_guess = self.price_call(S, K, T, r, q, sigma)
                vega_guess = self.vega(S, K, T, r, q, sigma)
            else:
                price_guess = self.price_put(S, K, T, r, q, sigma)
                vega_guess = self.vega(S, K, T, r, q, sigma)
            
            diff = price - price_guess
            
            if abs(diff) < tolerance:
                return sigma
            
            if abs(vega_guess) < 1e-10:
                return None
            
            sigma = sigma + diff / vega_guess
            
            # Ensure volatility stays positive
            sigma = max(sigma, 1e-6)
        
        return None 