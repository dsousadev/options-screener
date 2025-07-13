import pytest
import numpy as np
from libs.models.heston import (
    heston_call_price,
    heston_put_price,
    heston_call_delta,
    heston_put_delta,
    heston_gamma,
    heston_vega,
    heston_theta,
    calibrate_heston_model
)


class TestHestonModel:
    """Test suite for Heston stochastic volatility model."""
    
    def test_heston_call_basic(self):
        """Test Heston call option pricing with basic parameters."""
        # Test case with typical Heston parameters
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        call_price = heston_call_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        # Should be a reasonable positive value
        assert call_price > 0
        assert call_price < S  # Call price should be less than stock price
        
    def test_heston_put_basic(self):
        """Test Heston put option pricing with basic parameters."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        put_price = heston_put_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        # Should be a reasonable positive value
        assert put_price > 0
        assert put_price < K  # Put price should be less than strike
        
    def test_heston_put_call_parity(self):
        """Test put-call parity for Heston model."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        call_price = heston_call_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        put_price = heston_put_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        left_side = call_price + K * np.exp(-r * T)
        right_side = put_price + S
        
        assert abs(left_side - right_side) < 1e-10
        
    def test_edge_case_zero_time_to_expiry(self):
        """Test edge case where time to expiry is zero."""
        S, K, T, r = 100, 100, 0.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        # Call should be worth max(0, S - K)
        call_price = heston_call_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        expected_call = max(0, S - K)
        assert abs(call_price - expected_call) < 1e-10
        
        # Put should be worth max(0, K - S)
        put_price = heston_put_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        expected_put = max(0, K - S)
        assert abs(put_price - expected_put) < 1e-10
        
    def test_edge_case_zero_initial_volatility(self):
        """Test edge case where initial volatility is zero."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.0, 0.04, 2.0, -0.7, 0.3
        
        # Should still produce reasonable prices (not crash)
        call_price = heston_call_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        put_price = heston_put_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        assert call_price >= 0
        assert put_price >= 0
        
    def test_heston_delta_bounds(self):
        """Test that Heston call delta is between 0 and 1, put delta between -1 and 0."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        call_delta_val = heston_call_delta(S, K, T, r, v0, theta, kappa, rho, sigma)
        put_delta_val = heston_put_delta(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        assert 0 <= call_delta_val <= 1
        assert -1 <= put_delta_val <= 0
        
    def test_heston_gamma_always_positive(self):
        """Test that Heston gamma is always positive."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        gamma_val = heston_gamma(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        assert gamma_val > 0
        
    def test_heston_vega_always_positive(self):
        """Test that Heston vega is always positive."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        vega_val = heston_vega(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        assert vega_val > 0
        
    def test_heston_theta_always_negative(self):
        """Test that Heston theta is always negative (time decay)."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        theta_val = heston_theta(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        assert theta_val < 0
        
    def test_parameter_sanity_checks(self):
        """Test that model parameters make logical sense."""
        S, K, T, r = 100, 100, 1.0, 0.05
        v0, theta, kappa, rho, sigma = 0.04, 0.04, 2.0, -0.7, 0.3
        
        # Test that higher volatility leads to higher option prices
        call_price_low_vol = heston_call_price(S, K, T, r, 0.02, theta, kappa, rho, sigma)
        call_price_high_vol = heston_call_price(S, K, T, r, 0.08, theta, kappa, rho, sigma)
        
        assert call_price_high_vol > call_price_low_vol
        
        # Test that higher correlation leads to different prices
        call_price_low_corr = heston_call_price(S, K, T, r, v0, theta, kappa, -0.9, sigma)
        call_price_high_corr = heston_call_price(S, K, T, r, v0, theta, kappa, -0.3, sigma)
        
        # Should be different (though direction depends on moneyness)
        assert abs(call_price_low_corr - call_price_high_corr) > 1e-6
        
    def test_calibration_round_trip(self):
        """Test that calibration can recover original parameters."""
        # Original parameters
        S, K, T, r = 100, 100, 1.0, 0.05
        original_params = {
            'v0': 0.04,
            'theta': 0.04,
            'kappa': 2.0,
            'rho': -0.7,
            'sigma': 0.3
        }
        
        # Generate "market" prices using original parameters
        market_prices = []
        strikes = [90, 95, 100, 105, 110]
        
        for strike in strikes:
            price = heston_call_price(S, strike, T, r, **original_params)
            market_prices.append(price)
        
        # Calibrate model to these prices
        calibrated_params = calibrate_heston_model(
            S, strikes, T, r, market_prices, 
            initial_guess=original_params
        )
        
        # Check that calibrated parameters are close to original
        for param, original_value in original_params.items():
            calibrated_value = calibrated_params[param]
            assert abs(calibrated_value - original_value) < 0.1
            
    def test_calibration_with_noise(self):
        """Test calibration with small amount of noise in market prices."""
        S, K, T, r = 100, 100, 1.0, 0.05
        original_params = {
            'v0': 0.04,
            'theta': 0.04,
            'kappa': 2.0,
            'rho': -0.7,
            'sigma': 0.3
        }
        
        # Generate market prices with small noise
        market_prices = []
        strikes = [90, 95, 100, 105, 110]
        
        for strike in strikes:
            price = heston_call_price(S, strike, T, r, **original_params)
            # Add 1% noise
            noisy_price = price * (1 + 0.01 * np.random.normal())
            market_prices.append(noisy_price)
        
        # Calibrate model to noisy prices
        calibrated_params = calibrate_heston_model(
            S, strikes, T, r, market_prices,
            initial_guess=original_params
        )
        
        # Check that calibrated parameters are reasonable
        for param, original_value in original_params.items():
            calibrated_value = calibrated_params[param]
            # Should be within 50% of original (due to noise)
            assert 0.5 * original_value <= calibrated_value <= 1.5 * original_value
            
    def test_calibration_parameter_bounds(self):
        """Test that calibrated parameters stay within reasonable bounds."""
        S, K, T, r = 100, 100, 1.0, 0.05
        original_params = {
            'v0': 0.04,
            'theta': 0.04,
            'kappa': 2.0,
            'rho': -0.7,
            'sigma': 0.3
        }
        
        market_prices = []
        strikes = [90, 95, 100, 105, 110]
        
        for strike in strikes:
            price = heston_call_price(S, strike, T, r, **original_params)
            market_prices.append(price)
        
        calibrated_params = calibrate_heston_model(
            S, strikes, T, r, market_prices,
            initial_guess=original_params
        )
        
        # Check parameter bounds
        assert 0 < calibrated_params['v0'] < 1  # Initial volatility
        assert 0 < calibrated_params['theta'] < 1  # Long-term volatility
        assert 0 < calibrated_params['kappa'] < 10  # Mean reversion speed
        assert -1 < calibrated_params['rho'] < 1  # Correlation
        assert 0 < calibrated_params['sigma'] < 1  # Volatility of volatility
        
    def test_heston_vs_black_scholes_convergence(self):
        """Test that Heston converges to Black-Scholes for high kappa."""
        S, K, T, r = 100, 100, 1.0, 0.05
        sigma_bs = 0.2  # Black-Scholes volatility
        
        # Heston parameters with high mean reversion (fast convergence to constant vol)
        v0, theta, kappa, rho, sigma = sigma_bs**2, sigma_bs**2, 10.0, -0.7, 0.1
        
        heston_price = heston_call_price(S, K, T, r, v0, theta, kappa, rho, sigma)
        
        # Simple Black-Scholes approximation
        bs_price = S * 0.5 - K * np.exp(-r * T) * 0.5  # Rough ATM approximation
        
        # Should be reasonably close
        assert abs(heston_price - bs_price) < 2.0 