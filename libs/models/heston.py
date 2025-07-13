"""
Heston Stochastic Volatility Model

This module implements the Heston model for option pricing, which accounts for
stochastic volatility. The model includes calibration functionality to fit
parameters to market data.
"""

import numpy as np
from scipy.optimize import least_squares
from scipy.integrate import quad
from typing import Dict, List, Tuple, Optional
import warnings


class HestonModel:
    """
    Heston stochastic volatility model implementation.
    
    The Heston model assumes that the volatility follows a mean-reverting
    square-root process, which can capture the volatility smile/skew observed
    in real option markets.
    """
    
    def __init__(self):
        """
        Initialize the Heston model.
        
        Parameters:
        - v0: Initial variance
        - theta: Long-term variance
        - kappa: Mean reversion speed
        - rho: Correlation between stock and variance processes
        - sigma: Volatility of volatility
        """
        self.v0 = 0.04      # Initial variance (20% volatility)
        self.theta = 0.04    # Long-term variance
        self.kappa = 2.0     # Mean reversion speed
        self.rho = -0.7      # Correlation
        self.sigma = 0.3     # Volatility of volatility
    
    def set_parameters(self, v0: float, theta: float, kappa: float, rho: float, sigma: float):
        """
        Set the Heston model parameters.
        
        Args:
            v0: Initial variance
            theta: Long-term variance
            kappa: Mean reversion speed
            rho: Correlation between stock and variance processes
            sigma: Volatility of volatility
        """
        self.v0 = v0
        self.theta = theta
        self.kappa = kappa
        self.rho = rho
        self.sigma = sigma
    
    def _characteristic_function(self, phi: float, S: float, K: float, T: float, r: float, q: float) -> complex:
        """
        Calculate the characteristic function for the Heston model.
        
        Args:
            phi: Integration variable
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            q: Dividend yield
            
        Returns:
            Complex characteristic function value
        """
        # Parameters
        v0, theta, kappa, rho, sigma = self.v0, self.theta, self.kappa, self.rho, self.sigma
        
        # Complex parameters
        u = 0.5
        a = kappa * theta
        b = kappa
        
        d = np.sqrt((b - 1j * rho * sigma * phi)**2 + sigma**2 * (phi**2 + 1j * phi))
        g = (b - 1j * rho * sigma * phi + d) / (b - 1j * rho * sigma * phi - d)
        
        # Characteristic function
        C = (r - q) * phi * 1j * T + (a / sigma**2) * (
            (b - 1j * rho * sigma * phi + d) * T - 2 * np.log((1 - g * np.exp(d * T)) / (1 - g))
        )
        
        D = ((b - 1j * rho * sigma * phi + d) / sigma**2) * (
            (1 - np.exp(d * T)) / (1 - g * np.exp(d * T))
        )
        
        return np.exp(C + D * v0)
    
    def _integrand_call(self, phi: float, S: float, K: float, T: float, r: float, q: float) -> float:
        """
        Integrand for call option pricing.
        
        Args:
            phi: Integration variable
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            q: Dividend yield
            
        Returns:
            Real part of the integrand
        """
        if phi == 0:
            return 0.5
        
        cf = self._characteristic_function(phi, S, K, T, r, q)
        integrand = np.real(np.exp(-1j * phi * np.log(K)) * cf / (1j * phi))
        return integrand
    
    def _integrand_put(self, phi: float, S: float, K: float, T: float, r: float, q: float) -> float:
        """
        Integrand for put option pricing.
        
        Args:
            phi: Integration variable
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            q: Dividend yield
            
        Returns:
            Real part of the integrand
        """
        if phi == 0:
            return 0.5
        
        cf = self._characteristic_function(phi, S, K, T, r, q)
        integrand = np.real(np.exp(-1j * phi * np.log(K)) * cf / (1j * phi))
        return -integrand
    
    def price_call(self, S: float, K: float, T: float, r: float, q: float) -> float:
        """
        Price a European call option using the Heston model.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            
        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)
        
        # Integration limits and tolerance
        upper_limit = 100
        tolerance = 1e-6
        
        # Numerical integration
        integral, _ = quad(self._integrand_call, 0, upper_limit, 
                          args=(S, K, T, r, q), limit=1000, epsabs=tolerance)
        
        call_price = S * np.exp(-q * T) - K * np.exp(-r * T) * (0.5 + integral / np.pi)
        return call_price
    
    def price_put(self, S: float, K: float, T: float, r: float, q: float) -> float:
        """
        Price a European put option using the Heston model.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            q: Dividend yield
            
        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)
        
        # Integration limits and tolerance
        upper_limit = 100
        tolerance = 1e-6
        
        # Numerical integration
        integral, _ = quad(self._integrand_put, 0, upper_limit, 
                          args=(S, K, T, r, q), limit=1000, epsabs=tolerance)
        
        put_price = K * np.exp(-r * T) * (0.5 - integral / np.pi) - S * np.exp(-q * T)
        return put_price
    
    def _calibration_objective(self, params: np.ndarray, market_data: List[Dict]) -> np.ndarray:
        """
        Objective function for calibration.
        
        Args:
            params: Model parameters [v0, theta, kappa, rho, sigma]
            market_data: List of dictionaries with market option data
            
        Returns:
            Array of price differences (model - market)
        """
        v0, theta, kappa, rho, sigma = params
        
        # Ensure parameters are within reasonable bounds
        if (v0 <= 0 or theta <= 0 or kappa <= 0 or sigma <= 0 or 
            abs(rho) >= 1 or v0 > 1 or theta > 1 or kappa > 10 or sigma > 2):
            return np.full(len(market_data), 1e6)
        
        self.set_parameters(v0, theta, kappa, rho, sigma)
        
        errors = []
        for option in market_data:
            S = option['S']
            K = option['K']
            T = option['T']
            r = option['r']
            q = option['q']
            market_price = option['price']
            option_type = option.get('type', 'call')
            
            try:
                if option_type.lower() == 'call':
                    model_price = self.price_call(S, K, T, r, q)
                else:
                    model_price = self.price_put(S, K, T, r, q)
                
                # Relative error to give equal weight to different price levels
                error = (model_price - market_price) / market_price
                errors.append(error)
                
            except Exception:
                errors.append(1e6)
        
        return np.array(errors)
    
    def calibrate(self, market_data: List[Dict], initial_params: Optional[List[float]] = None) -> Dict:
        """
        Calibrate the Heston model to market option prices.
        
        Args:
            market_data: List of dictionaries with keys:
                - S: Stock price
                - K: Strike price
                - T: Time to expiration
                - r: Risk-free rate
                - q: Dividend yield
                - price: Market option price
                - type: 'call' or 'put' (optional, defaults to 'call')
            initial_params: Initial parameter guess [v0, theta, kappa, rho, sigma]
            
        Returns:
            Dictionary with calibrated parameters and fit statistics
        """
        if not market_data:
            raise ValueError("Market data cannot be empty")
        
        # Default initial parameters
        if initial_params is None:
            initial_params = [0.04, 0.04, 2.0, -0.7, 0.3]
        
        # Parameter bounds
        bounds = ([0.001, 0.001, 0.1, -0.99, 0.01],  # Lower bounds
                 [1.0, 1.0, 10.0, 0.99, 2.0])         # Upper bounds
        
        try:
            # Optimize using least squares
            result = least_squares(
                self._calibration_objective,
                initial_params,
                args=(market_data,),
                bounds=bounds,
                method='trf',
                ftol=1e-8,
                xtol=1e-8,
                max_nfev=1000
            )
            
            if result.success:
                v0, theta, kappa, rho, sigma = result.x
                self.set_parameters(v0, theta, kappa, rho, sigma)
                
                # Calculate final errors
                final_errors = self._calibration_objective(result.x, market_data)
                rmse = np.sqrt(np.mean(final_errors**2))
                max_error = np.max(np.abs(final_errors))
                
                return {
                    'success': True,
                    'parameters': {
                        'v0': v0,
                        'theta': theta,
                        'kappa': kappa,
                        'rho': rho,
                        'sigma': sigma
                    },
                    'rmse': rmse,
                    'max_error': max_error,
                    'iterations': result.nfev
                }
            else:
                return {
                    'success': False,
                    'error': 'Optimization failed to converge',
                    'parameters': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'parameters': None
            }
    
    def get_greeks(self, S: float, K: float, T: float, r: float, q: float, 
                   option_type: str = 'call', h: float = 1e-6) -> Dict[str, float]:
        """
        Calculate Greeks using finite differences.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            q: Dividend yield
            option_type: 'call' or 'put'
            h: Step size for finite differences
            
        Returns:
            Dictionary with Greeks
        """
        if option_type.lower() == 'call':
            price_func = self.price_call
        else:
            price_func = self.price_put
        
        # Delta
        price_up = price_func(S + h, K, T, r, q)
        price_down = price_func(S - h, K, T, r, q)
        delta = (price_up - price_down) / (2 * h)
        
        # Gamma
        price_center = price_func(S, K, T, r, q)
        gamma = (price_up - 2 * price_center + price_down) / (h**2)
        
        # Vega (with respect to v0)
        original_v0 = self.v0
        self.v0 += h
        price_v_up = price_func(S, K, T, r, q)
        self.v0 = original_v0 - h
        price_v_down = price_func(S, K, T, r, q)
        self.v0 = original_v0
        vega = (price_v_up - price_v_down) / (2 * h)
        
        # Theta
        price_t_up = price_func(S, K, T + h, r, q)
        price_t_down = price_func(S, K, T - h, r, q)
        theta = -(price_t_up - price_t_down) / (2 * h)
        
        # Rho
        price_r_up = price_func(S, K, T, r + h, q)
        price_r_down = price_func(S, K, T, r - h, q)
        rho = (price_r_up - price_r_down) / (2 * h)
        
        return {
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta': theta,
            'rho': rho
        } 