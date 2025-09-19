"""
Unit tests for Greeks Calculator Service
"""
import pytest
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

from services.greeks_calculator import GreeksCalculator
from models.strategy import OptionsStrategy, StrategyLeg, InstrumentType, PositionType
from models.education import GreekType


class TestGreeksCalculator:
    """Test Greeks calculator functionality"""

    @pytest.fixture
    def greeks_calculator(self):
        """Create Greeks calculator instance"""
        return GreeksCalculator(risk_free_rate=0.06)

    @pytest.fixture
    def sample_option_data(self):
        """Sample option data for testing"""
        return {
            'stock_price': 100.0,
            'strike_price': 100.0,
            'time_to_expiry': 30.0 / 365.0,  # 30 days
            'interest_rate': 0.06,
            'volatility': 0.20,
            'option_type': 'call'
        }

    def test_calculate_delta_call(self, greeks_calculator, sample_option_data):
        """Test delta calculation for call option"""
        data = sample_option_data
        delta = greeks_calculator.calculate_delta(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        # ATM call should have delta around 0.5
        assert 0.4 <= delta <= 0.6
        assert isinstance(delta, float)

    def test_calculate_delta_put(self, greeks_calculator, sample_option_data):
        """Test delta calculation for put option"""
        data = sample_option_data.copy()
        data['option_type'] = 'put'

        delta = greeks_calculator.calculate_delta(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        # ATM put should have delta around -0.5
        assert -0.6 <= delta <= -0.4
        assert isinstance(delta, float)

    def test_calculate_gamma(self, greeks_calculator, sample_option_data):
        """Test gamma calculation"""
        data = sample_option_data
        gamma = greeks_calculator.calculate_gamma(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility']
        )

        # Gamma should be positive
        assert gamma > 0
        assert isinstance(gamma, float)

    def test_calculate_theta_call(self, greeks_calculator, sample_option_data):
        """Test theta calculation for call option"""
        data = sample_option_data
        theta = greeks_calculator.calculate_theta(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        # Theta for long call should be negative (time decay)
        assert theta < 0
        assert isinstance(theta, float)

    def test_calculate_vega(self, greeks_calculator, sample_option_data):
        """Test vega calculation"""
        data = sample_option_data
        vega = greeks_calculator.calculate_vega(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility']
        )

        # Vega should be positive for long options
        assert vega > 0
        assert isinstance(vega, float)

    def test_calculate_rho_call(self, greeks_calculator, sample_option_data):
        """Test rho calculation for call option"""
        data = sample_option_data
        rho = greeks_calculator.calculate_rho(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        # Rho for call should be positive
        assert rho > 0
        assert isinstance(rho, float)

    def test_calculate_all_greeks(self, greeks_calculator, sample_option_data):
        """Test calculation of all Greeks"""
        data = sample_option_data
        greeks = greeks_calculator.calculate_all_greeks(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        # Check all Greeks are present
        assert 'delta' in greeks
        assert 'gamma' in greeks
        assert 'theta' in greeks
        assert 'vega' in greeks
        assert 'rho' in greeks

        # Check all values are floats
        for greek_name, value in greeks.items():
            assert isinstance(value, float)

    def test_calculate_strategy_greeks(self, greeks_calculator):
        """Test strategy Greeks calculation"""
        # Create a simple long call strategy
        strategy = OptionsStrategy(
            id="test_strategy",
            name="Long Call Test",
            strategy_type="basic",
            legs=[
                StrategyLeg(
                    leg_id="leg1",
                    instrument_type=InstrumentType.CALL,
                    position_type=PositionType.LONG,
                    strike_price=Decimal("100.0"),
                    expiry_date=datetime.now() + timedelta(days=30),
                    quantity=1,
                    underlying_symbol="TEST"
                )
            ],
            entry_conditions={},
            exit_conditions={},
            risk_parameters={},
            description="Test strategy"
        )

        greeks_impact = greeks_calculator.calculate_strategy_greeks(
            strategy, 100.0, 0.20
        )

        # Check Greeks impact object is created
        assert greeks_impact.strategy_id == "test_strategy"
        assert isinstance(greeks_impact.delta, Decimal)
        assert isinstance(greeks_impact.gamma, Decimal)
        assert isinstance(greeks_impact.theta, Decimal)
        assert isinstance(greeks_impact.vega, Decimal)
        assert isinstance(greeks_impact.rho, Decimal)

    def test_edge_case_zero_time(self, greeks_calculator):
        """Test edge case with zero time to expiry"""
        data = {
            'stock_price': 100.0,
            'strike_price': 100.0,
            'time_to_expiry': 0.0,
            'interest_rate': 0.06,
            'volatility': 0.20,
            'option_type': 'call'
        }

        delta = greeks_calculator.calculate_delta(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        # At expiry, call delta should be 1 if ITM, 0 if OTM
        assert delta in [0.0, 1.0]

    def test_edge_case_negative_inputs(self, greeks_calculator):
        """Test edge case with negative inputs"""
        data = {
            'stock_price': -100.0,  # Negative stock price
            'strike_price': 100.0,
            'time_to_expiry': 0.1,
            'interest_rate': 0.06,
            'volatility': 0.20,
            'option_type': 'call'
        }

        # Should handle gracefully and return 0.0
        delta = greeks_calculator.calculate_delta(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type']
        )

        assert isinstance(delta, float)

    def test_greeks_scenarios(self, greeks_calculator, sample_option_data):
        """Test Greeks calculation under different scenarios"""
        data = sample_option_data
        price_scenarios = [90.0, 100.0, 110.0]
        volatility_scenarios = [0.15, 0.20, 0.25]

        scenarios = greeks_calculator.calculate_greeks_scenarios(
            data['stock_price'], data['strike_price'], data['time_to_expiry'],
            data['interest_rate'], data['volatility'], data['option_type'],
            price_scenarios, volatility_scenarios
        )

        # Check scenarios structure
        assert 'price_scenarios' in scenarios
        assert 'volatility_scenarios' in scenarios
        assert 'time_scenarios' in scenarios

        # Check price scenarios
        assert len(scenarios['price_scenarios']) == 3
        for scenario in scenarios['price_scenarios']:
            assert 'price' in scenario
            assert 'greeks' in scenario
            assert 'price_change_percent' in scenario

        # Check volatility scenarios
        assert len(scenarios['volatility_scenarios']) == 3
        for scenario in scenarios['volatility_scenarios']:
            assert 'volatility' in scenario
            assert 'greeks' in scenario
            assert 'vol_change_percent' in scenario

    def test_get_greeks_education_content(self, greeks_calculator):
        """Test getting educational content for Greeks"""
        # Test each Greek type
        for greek_type in GreekType:
            content = greeks_calculator.get_greeks_education_content(greek_type)

            assert isinstance(content, dict)
            assert 'name' in content
            assert 'description' in content
            assert 'interpretation' in content
            assert 'key_concepts' in content

    def test_delta_exposure_analysis(self, greeks_calculator):
        """Test delta exposure analysis"""
        # Test different delta values
        assert "bullish" in greeks_calculator._analyze_delta_exposure(0.8).lower()
        assert "bearish" in greeks_calculator._analyze_delta_exposure(-0.8).lower()
        assert "neutral" in greeks_calculator._analyze_delta_exposure(0.1).lower()

    def test_gamma_exposure_analysis(self, greeks_calculator):
        """Test gamma exposure analysis"""
        # Test different gamma values
        assert "High gamma" in greeks_calculator._analyze_gamma_exposure(0.02)
        assert "Low gamma" in greeks_calculator._analyze_gamma_exposure(0.001)
        assert "negative gamma" in greeks_calculator._analyze_gamma_exposure(-0.02)

    def test_theta_exposure_analysis(self, greeks_calculator):
        """Test theta exposure analysis"""
        # Test different theta values
        assert "time decay" in greeks_calculator._analyze_theta_exposure(-2.0)
        assert "time benefit" in greeks_calculator._analyze_theta_exposure(2.0)
        assert "Low time decay" in greeks_calculator._analyze_theta_exposure(-0.1)

    def test_vega_exposure_analysis(self, greeks_calculator):
        """Test vega exposure analysis"""
        # Test different vega values
        assert "High volatility" in greeks_calculator._analyze_vega_exposure(60)
        assert "Low volatility" in greeks_calculator._analyze_vega_exposure(10)
        assert "negative volatility" in greeks_calculator._analyze_vega_exposure(-60)

