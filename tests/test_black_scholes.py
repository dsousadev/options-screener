import pytest
import numpy as np
from libs.models.black_scholes import (
    black_scholes_call,
    black_scholes_put,
    call_delta,
    put_delta,
    gamma,
    theta,
    vega,
    rho,
    implied_volatility
)


class TestBlackScholesModel:
    """Test suite for Black-Scholes option pricing model."""
    
    def test_black_scholes_call_basic(self):
        """Test call option pricing with basic parameters."""
        # Test case: S=100, K=100, T=1, r=0.05, sigma=0.2
        # Expected call price ≈ 10.45 (from standard calculators)
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        call_price = black_scholes_call(S, K, T, r, sigma)
        
        assert abs(call_price - 10.45) < 0.1  # Within 10 cents
        
    def test_black_scholes_put_basic(self):
        """Test put option pricing with basic parameters."""
        # Test case: S=100, K=100, T=1, r=0.05, sigma=0.2
        # Expected put price ≈ 5.57 (from standard calculators)
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        put_price = black_scholes_put(S, K, T, r, sigma)
        
        assert abs(put_price - 5.57) < 0.1  # Within 10 cents
        
    def test_put_call_parity(self):
        """Test put-call parity: C + K*e^(-rT) = P + S"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        call_price = black_scholes_call(S, K, T, r, sigma)
        put_price = black_scholes_put(S, K, T, r, sigma)
        
        left_side = call_price + K * np.exp(-r * T)
        right_side = put_price + S
        
        assert abs(left_side - right_side) < 1e-10
        
    def test_at_the_money_call_delta(self):
        """Test call delta for at-the-money option."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        delta = call_delta(S, K, T, r, sigma)
        
        # At-the-money call delta should be approximately 0.5
        assert abs(delta - 0.5) < 0.1
        
    def test_at_the_money_put_delta(self):
        """Test put delta for at-the-money option."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        delta = put_delta(S, K, T, r, sigma)
        
        # At-the-money put delta should be approximately -0.5
        assert abs(delta + 0.5) < 0.1
        
    def test_gamma_maximum_at_the_money(self):
        """Test that gamma is maximum for at-the-money options."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        atm_gamma = gamma(S, K, T, r, sigma)
        
        # Test slightly in-the-money
        itm_gamma = gamma(S * 1.05, K, T, r, sigma)
        # Test slightly out-of-the-money
        otm_gamma = gamma(S * 0.95, K, T, r, sigma)
        
        # ATM gamma should be higher than both ITM and OTM
        assert atm_gamma > itm_gamma
        assert atm_gamma > otm_gamma
        
    def test_vega_always_positive(self):
        """Test that vega is always positive."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        vega_val = vega(S, K, T, r, sigma)
        
        assert vega_val > 0
        
    def test_theta_always_negative(self):
        """Test that theta is always negative (time decay)."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        theta_val = theta(S, K, T, r, sigma)
        
        assert theta_val < 0
        
    def test_implied_volatility_round_trip(self):
        """Test that implied volatility calculation recovers the original volatility."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        call_price = black_scholes_call(S, K, T, r, sigma)
        
        # Calculate implied volatility from the price
        implied_vol = implied_volatility(call_price, S, K, T, r, is_call=True)
        
        # Should recover the original volatility
        assert abs(implied_vol - sigma) < 0.01
        
    def test_edge_case_zero_time_to_expiry(self):
        """Test edge case where time to expiry is zero."""
        S, K, T, r, sigma = 100, 100, 0.0, 0.05, 0.2
        
        # Call should be worth max(0, S - K)
        call_price = black_scholes_call(S, K, T, r, sigma)
        expected_call = max(0, S - K)
        assert abs(call_price - expected_call) < 1e-10
        
        # Put should be worth max(0, K - S)
        put_price = black_scholes_put(S, K, T, r, sigma)
        expected_put = max(0, K - S)
        assert abs(put_price - expected_put) < 1e-10
        
    def test_edge_case_zero_volatility(self):
        """Test edge case where volatility is zero."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.0
        
        # With zero volatility, option should be worth intrinsic value
        call_price = black_scholes_call(S, K, T, r, sigma)
        expected_call = max(0, S - K * np.exp(-r * T))
        assert abs(call_price - expected_call) < 1e-10
        
    def test_delta_bounds(self):
        """Test that call delta is between 0 and 1, put delta between -1 and 0."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        
        call_delta_val = call_delta(S, K, T, r, sigma)
        put_delta_val = put_delta(S, K, T, r, sigma)
        
        assert 0 <= call_delta_val <= 1
        assert -1 <= put_delta_val <= 0
        
    def test_gamma_always_positive(self):
        """Test that gamma is always positive."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        gamma_val = gamma(S, K, T, r, sigma)
        
        assert gamma_val > 0
        
    def test_rho_call_positive_put_negative(self):
        """Test that call rho is positive and put rho is negative."""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        
        call_rho_val = rho(S, K, T, r, sigma, is_call=True)
        put_rho_val = rho(S, K, T, r, sigma, is_call=False)
        
        assert call_rho_val > 0
        assert put_rho_val < 0 