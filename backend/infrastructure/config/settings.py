import os
from pathlib import Path
from typing import Literal, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    """
    Configuration settings for the trading bot.

    Important: For historical data retrieval, always use the LIVE API credentials.
    Paper credentials are only for executing simulated trades.
    """

    # Trading mode: 'paper' or 'live' (default to paper for safety)
    TRADING_MODE = os.getenv('TRADING_MODE', 'paper')

    # Alpaca LIVE API credentials (also used for historical data)
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://api.alpaca.markets')

    # Alpaca PAPER API credentials (only for paper trading execution)
    ALPACA_PAPERS_KEY = os.getenv('ALPACA_PAPERS_KEY', '')
    ALPACA_PAPERS_SECRET_KEY = os.getenv('ALPACA_PAPERS_SECRET_KEY', '')

    # Binance API credentials (optional, CCXT works without keys for public data)
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')

    @classmethod
    def get_alpaca_data_config(cls) -> Tuple[str, str]:
        """
        Get Alpaca credentials for historical data retrieval.
        Always uses LIVE API credentials (not paper).

        Returns:
            Tuple of (api_key, secret_key)

        Raises:
            ValueError: If credentials are not configured
        """
        api_key = cls.ALPACA_API_KEY
        secret_key = cls.ALPACA_SECRET_KEY

        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca API credentials not configured.\n"
                "Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file.\n"
                "Get credentials at: https://alpaca.markets/"
            )

        return api_key, secret_key

    @classmethod
    def get_alpaca_trading_config(cls, mode: Literal['paper', 'live'] = 'paper') -> Tuple[str, str, str]:
        """
        Get Alpaca Trading API credentials for executing trades.

        Args:
            mode: Trading mode ('paper' or 'live'). Defaults to 'paper' for safety.

        Returns:
            Tuple of (api_key, secret_key, base_url)

        Raises:
            ValueError: If credentials for the specified mode are not configured
        """
        if mode == 'paper':
            api_key = cls.ALPACA_PAPERS_KEY
            secret_key = cls.ALPACA_PAPERS_SECRET_KEY
            base_url = None

            if not api_key or not secret_key:
                raise ValueError(
                    "Alpaca Paper Trading API credentials not configured.\n"
                    "Please set ALPACA_PAPERS_KEY and ALPACA_PAPERS_SECRET_KEY in .env file"
                )
        elif mode == 'live':
            api_key = cls.ALPACA_API_KEY
            secret_key = cls.ALPACA_SECRET_KEY
            base_url = cls.ALPACA_BASE_URL

            if not api_key or not secret_key:
                raise ValueError(
                    "Alpaca Live Trading API credentials not configured.\n"
                    "Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file.\n"
                    "WARNING: This uses REAL MONEY!"
                )
        else:
            raise ValueError(f"Invalid trading mode: {mode}. Must be 'paper' or 'live'")

        return api_key, secret_key, base_url

    @classmethod
    def validate_alpaca_data_config(cls) -> bool:
        """Check if Alpaca credentials are configured for data retrieval."""
        return bool(cls.ALPACA_API_KEY and cls.ALPACA_SECRET_KEY)

    @classmethod
    def validate_alpaca_trading_config(cls, mode: Literal['paper', 'live'] = 'paper') -> bool:
        """Check if Alpaca Trading API credentials are configured for the specified mode."""
        if mode == 'paper':
            return bool(cls.ALPACA_PAPERS_KEY and cls.ALPACA_PAPERS_SECRET_KEY)
        elif mode == 'live':
            return bool(cls.ALPACA_API_KEY and cls.ALPACA_SECRET_KEY)
        return False

    @classmethod
    def validate_binance_config(cls) -> bool:
        """Check if Binance credentials are configured."""
        return bool(cls.BINANCE_API_KEY and cls.BINANCE_SECRET_KEY)
