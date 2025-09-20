"""
Greeks Calculator Service for F&O Educational Learning System
"""
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
from loguru import logger

from models.strategy import GreeksImpact, OptionsStrategy, StrategyLeg
from models.education import GreekType

class GreeksCalculator:
    """Real-time options Greeks calculation engine"""

    def __init__(self, risk_free_rate: float = 0.06):
        """
        Initialize Greeks calculator

        Args:
            risk_free_rate: Risk-free interest rate (default 6% for India)
        """
        self.risk_free_rate = risk_free_rate
        logger.info(f"GreeksCalculator initialized with risk-free rate: {risk_free_rate}")

    def calculate_delta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """
        Calculate option delta using Black-Scholes model

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility
            option_type: 'call' or 'put'

        Returns:
            Delta value
        """
        try:
            # Input validation to prevent math domain errors
            if S <= 0 or K <= 0 or sigma <= 0:
                logger.warning(f"Invalid inputs for delta calculation: S={S}, K={K}, sigma={sigma}")
                return 0.0

            if T <= 0:
                return 1.0 if option_type == 'call' else -1.0

            # Safe log calculation with domain validation
            try:
                d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            except (ValueError, ZeroDivisionError, RuntimeWarning):
                logger.warning(f"Math domain error in delta calculation: S/K={S/K}")
                return 0.0

            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
            else:  # put
                delta = norm.cdf(d1) - 1

            logger.debug(f"Delta calculated: {delta} for {option_type} option")
            return float(delta)

        except Exception as e:
            logger.error(f"Error calculating delta: {e}")
            return 0.0

    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate option gamma

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility

        Returns:
            Gamma value
        """
        try:
            if T <= 0:
                return 0.0

            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

            logger.debug(f"Gamma calculated: {gamma}")
            return float(gamma)

        except Exception as e:
            logger.error(f"Error calculating gamma: {e}")
            return 0.0

    def calculate_theta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """
        Calculate option theta (time decay)

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility
            option_type: 'call' or 'put'

        Returns:
            Theta value (per day)
        """
        try:
            if T <= 0:
                return 0.0

            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)

            # Theta calculation (per day)
            theta_call = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) -
                         r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
            theta_put = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) +
                        r*K*np.exp(-r*T)*norm.cdf(-d2)) / 365

            theta = theta_call if option_type.lower() == 'call' else theta_put

            logger.debug(f"Theta calculated: {theta} for {option_type} option")
            return float(theta)

        except Exception as e:
            logger.error(f"Error calculating theta: {e}")
            return 0.0

    def calculate_vega(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate option vega (volatility sensitivity)

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility

        Returns:
            Vega value (for 1% change in volatility)
        """
        try:
            if T <= 0:
                return 0.0

            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # For 1% volatility change

            logger.debug(f"Vega calculated: {vega}")
            return float(vega)

        except Exception as e:
            logger.error(f"Error calculating vega: {e}")
            return 0.0

    def calculate_rho(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """
        Calculate option rho (interest rate sensitivity)

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility
            option_type: 'call' or 'put'

        Returns:
            Rho value (for 1% change in interest rate)
        """
        try:
            if T <= 0:
                return 0.0

            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)

            # Rho calculation (for 1% interest rate change)
            if option_type.lower() == 'call':
                rho = K * T * np.exp(-r*T) * norm.cdf(d2) / 100
            else:  # put
                rho = -K * T * np.exp(-r*T) * norm.cdf(-d2) / 100

            logger.debug(f"Rho calculated: {rho} for {option_type} option")
            return float(rho)

        except Exception as e:
            logger.error(f"Error calculating rho: {e}")
            return 0.0

    def calculate_all_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict[str, float]:
        """
        Calculate all Greeks for an option

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free interest rate
            sigma: Volatility
            option_type: 'call' or 'put'

        Returns:
            Dictionary containing all Greeks
        """
        try:
            greeks = {
                'delta': self.calculate_delta(S, K, T, r, sigma, option_type),
                'gamma': self.calculate_gamma(S, K, T, r, sigma),
                'theta': self.calculate_theta(S, K, T, r, sigma, option_type),
                'vega': self.calculate_vega(S, K, T, r, sigma),
                'rho': self.calculate_rho(S, K, T, r, sigma, option_type)
            }

            logger.info(f"All Greeks calculated for {option_type} option")
            return greeks

        except Exception as e:
            logger.error(f"Error calculating all Greeks: {e}")
            return {
                'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0
            }

    def calculate_strategy_greeks(self, strategy: OptionsStrategy, current_price: float, volatility: float) -> GreeksImpact:
        """
        Calculate Greeks for an entire strategy

        Args:
            strategy: Options strategy
            current_price: Current underlying price
            volatility: Current volatility

        Returns:
            GreeksImpact object with strategy Greeks
        """
        try:
            total_delta = 0.0
            total_gamma = 0.0
            total_theta = 0.0
            total_vega = 0.0
            total_rho = 0.0

            for leg in strategy.legs:
                if leg.instrument_type in ['call', 'put']:
                    # Calculate time to expiration
                    time_to_expiry = (leg.expiry_date - datetime.now()).days / 365.0

                    if time_to_expiry <= 0:
                        continue

                    # Determine position multiplier
                    position_multiplier = 1 if leg.position_type == 'long' else -1
                    quantity_multiplier = leg.quantity * position_multiplier

                    # Calculate Greeks for this leg
                    leg_greeks = self.calculate_all_greeks(
                        float(current_price),
                        float(leg.strike_price),
                        time_to_expiry,
                        self.risk_free_rate,
                        volatility,
                        leg.instrument_type
                    )

                    # Add to totals
                    total_delta += leg_greeks['delta'] * quantity_multiplier
                    total_gamma += leg_greeks['gamma'] * quantity_multiplier
                    total_theta += leg_greeks['theta'] * quantity_multiplier
                    total_vega += leg_greeks['vega'] * quantity_multiplier
                    total_rho += leg_greeks['rho'] * quantity_multiplier

            # Create Greeks impact object
            greeks_impact = GreeksImpact(
                strategy_id=strategy.id,
                delta=Decimal(str(total_delta)),
                gamma=Decimal(str(total_gamma)),
                theta=Decimal(str(total_theta)),
                vega=Decimal(str(total_vega)),
                rho=Decimal(str(total_rho)),
                delta_exposure=self._analyze_delta_exposure(total_delta),
                gamma_exposure=self._analyze_gamma_exposure(total_gamma),
                theta_exposure=self._analyze_theta_exposure(total_theta),
                vega_exposure=self._analyze_vega_exposure(total_vega)
            )

            logger.info(f"Strategy Greeks calculated for {strategy.name}")
            return greeks_impact

        except Exception as e:
            logger.error(f"Error calculating strategy Greeks: {e}")
            return GreeksImpact(
                strategy_id=strategy.id,
                delta=Decimal('0'),
                gamma=Decimal('0'),
                theta=Decimal('0'),
                vega=Decimal('0'),
                rho=Decimal('0')
            )

    def _analyze_delta_exposure(self, delta: float) -> str:
        """Analyze delta exposure"""
        if delta > 0.5:
            return "Strong bullish exposure"
        elif delta > 0.2:
            return "Moderate bullish exposure"
        elif delta > -0.2:
            return "Neutral exposure"
        elif delta > -0.5:
            return "Moderate bearish exposure"
        else:
            return "Strong bearish exposure"

    def _analyze_gamma_exposure(self, gamma: float) -> str:
        """Analyze gamma exposure"""
        if gamma > 0.01:
            return "High gamma risk - large price movements will amplify P&L"
        elif gamma > 0.005:
            return "Moderate gamma risk"
        elif gamma > -0.005:
            return "Low gamma exposure"
        elif gamma > -0.01:
            return "Moderate negative gamma"
        else:
            return "High negative gamma - large price movements will reduce P&L"

    def _analyze_theta_exposure(self, theta: float) -> str:
        """Analyze theta exposure"""
        if theta < -1.0:
            return "High time decay - losing significant value daily"
        elif theta < -0.5:
            return "Moderate time decay"
        elif theta < 0.5:
            return "Low time decay impact"
        elif theta < 1.0:
            return "Moderate time benefit"
        else:
            return "High time benefit - gaining value over time"

    def _analyze_vega_exposure(self, vega: float) -> str:
        """Analyze vega exposure"""
        if vega > 50:
            return "High volatility sensitivity - benefits from volatility increases"
        elif vega > 25:
            return "Moderate volatility sensitivity"
        elif vega > -25:
            return "Low volatility sensitivity"
        elif vega > -50:
            return "Moderate negative volatility sensitivity"
        else:
            return "High negative volatility sensitivity - benefits from volatility decreases"

    def calculate_greeks_scenarios(self, S: float, K: float, T: float, r: float, sigma: float,
                                 option_type: str, price_scenarios: List[float],
                                 volatility_scenarios: List[float]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate Greeks under different scenarios

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration
            r: Risk-free rate
            sigma: Current volatility
            option_type: 'call' or 'put'
            price_scenarios: List of price scenarios
            volatility_scenarios: List of volatility scenarios

        Returns:
            Dictionary with Greeks scenarios
        """
        try:
            scenarios = {
                'price_scenarios': [],
                'volatility_scenarios': [],
                'time_scenarios': []
            }

            # Price scenarios
            for price in price_scenarios:
                greeks = self.calculate_all_greeks(price, K, T, r, sigma, option_type)
                scenarios['price_scenarios'].append({
                    'price': price,
                    'greeks': greeks,
                    'price_change_percent': (price - S) / S * 100
                })

            # Volatility scenarios
            for vol in volatility_scenarios:
                greeks = self.calculate_all_greeks(S, K, T, r, vol, option_type)
                scenarios['volatility_scenarios'].append({
                    'volatility': vol,
                    'greeks': greeks,
                    'vol_change_percent': (vol - sigma) / sigma * 100
                })

            # Time scenarios (decay over time)
            time_scenarios = [T * (1 - i/10) for i in range(1, 11)]  # 10% to 100% of original time
            for time in time_scenarios:
                if time > 0:
                    greeks = self.calculate_all_greeks(S, K, time, r, sigma, option_type)
                    scenarios['time_scenarios'].append({
                        'time_to_expiry': time,
                        'greeks': greeks,
                        'days_remaining': int(time * 365)
                    })

            logger.info(f"Greeks scenarios calculated for {len(price_scenarios)} price and {len(volatility_scenarios)} volatility scenarios")
            return scenarios

        except Exception as e:
            logger.error(f"Error calculating Greeks scenarios: {e}")
            return {'price_scenarios': [], 'volatility_scenarios': [], 'time_scenarios': []}

    def get_greeks_education_content(self, greek_type: GreekType) -> Dict[str, Any]:
        """
        Get educational content for specific Greek

        Args:
            greek_type: Type of Greek to explain

        Returns:
            Educational content dictionary
        """
        education_content = {
            GreekType.DELTA: {
                'name': 'Delta',
                'description': 'Price sensitivity of option to underlying asset price',
                'range': 'Call: 0 to 1, Put: -1 to 0',
                'interpretation': 'Delta represents the expected change in option price for a ₹1 change in underlying price',
                'key_concepts': [
                    'Delta is highest for ATM options',
                    'Delta approaches 1 for deep ITM calls',
                    'Delta approaches -1 for deep ITM puts',
                    'Delta changes with time and volatility'
                ],
                'practical_example': 'If NIFTY call has delta of 0.5 and NIFTY moves from 18000 to 18050, option price increases by approximately ₹25',
                'risk_management': 'Use delta to hedge portfolio exposure and manage directional risk'
            },
            GreekType.GAMMA: {
                'name': 'Gamma',
                'description': 'Rate of change of delta with respect to underlying price',
                'range': 'Always positive for long options',
                'interpretation': 'Gamma measures how quickly delta changes as underlying price moves',
                'key_concepts': [
                    'Gamma is highest for ATM options',
                    'Gamma increases as expiration approaches',
                    'High gamma means high sensitivity to price movements',
                    'Gamma is always positive for long positions'
                ],
                'practical_example': 'If option has high gamma, small price moves can cause large changes in delta and option value',
                'risk_management': 'Monitor gamma exposure to avoid unexpected losses from large price movements'
            },
            GreekType.THETA: {
                'name': 'Theta',
                'description': 'Time decay of option value',
                'range': 'Usually negative for long options',
                'interpretation': 'Theta represents daily loss in option value due to time passage',
                'key_concepts': [
                    'Theta is negative for long options (time decay)',
                    'Theta accelerates as expiration approaches',
                    'ATM options have highest theta',
                    'Theta can be positive for short positions'
                ],
                'practical_example': 'If option has theta of -5, it loses ₹5 in value each day due to time decay',
                'risk_management': 'Consider theta when holding options close to expiration'
            },
            GreekType.VEGA: {
                'name': 'Vega',
                'description': 'Sensitivity to changes in implied volatility',
                'range': 'Always positive for long options',
                'interpretation': 'Vega measures option price change for 1% change in implied volatility',
                'key_concepts': [
                    'Vega is highest for ATM options',
                    'Vega decreases as expiration approaches',
                    'Long options benefit from volatility increases',
                    'Short options suffer from volatility increases'
                ],
                'practical_example': 'If option has vega of 20 and volatility increases from 20% to 21%, option price increases by ₹20',
                'risk_management': 'Monitor volatility environment and vega exposure'
            },
            GreekType.RHO: {
                'name': 'Rho',
                'description': 'Sensitivity to changes in interest rates',
                'range': 'Positive for calls, negative for puts',
                'interpretation': 'Rho measures option price change for 1% change in interest rates',
                'key_concepts': [
                    'Rho is generally small for short-term options',
                    'Rho increases with time to expiration',
                    'Higher rates benefit calls, hurt puts',
                    'Rho is less significant for most retail traders'
                ],
                'practical_example': 'If option has rho of 5 and interest rates rise by 1%, option price changes by ₹5',
                'risk_management': 'Rho is less critical for short-term trading but important for long-term options'
            }
        }

        return education_content.get(greek_type, {})

# Global instance
greeks_calculator = GreeksCalculator()




