from enum import Enum
from typing import Tuple


class AssetType(Enum):
    """Enum for different asset types."""
    CRYPTO = "crypto"
    STOCK = "stock"
    UNKNOWN = "unknown"


class SymbolDetector:
    """Detects whether a symbol is crypto or stock and standardizes format."""

    CRYPTO_QUOTE_CURRENCIES = ['USDT', 'USDC', 'USD', 'BTC', 'ETH', 'BUSD', 'DAI']

    @staticmethod
    def detect(symbol: str) -> AssetType:
        """
        Detect if symbol is crypto or stock.
        - Crypto: Contains '/' or ends with known quote currency (USDT, USDC, etc.)
        - Stock: 1-5 letter ticker
        """
        symbol_upper = symbol.upper().strip()

        # Has / separator? It's crypto (BTC/USDT)
        if '/' in symbol_upper:
            return AssetType.CRYPTO

        # Ends with known quote currency? It's crypto (BTCUSDT)
        for quote in SymbolDetector.CRYPTO_QUOTE_CURRENCIES:
            if symbol_upper.endswith(quote) and len(symbol_upper) > len(quote):
                return AssetType.CRYPTO

        # Short alphabetic ticker? Likely stock
        if len(symbol_upper) <= 5 and symbol_upper.isalpha():
            return AssetType.STOCK

        return AssetType.UNKNOWN

    @staticmethod
    def standardize_crypto_symbol(symbol: str) -> str:
        """Convert crypto symbol to standard format (BTC/USDT)."""
        symbol_upper = symbol.upper().strip()

        # Remove underscores (ETH_USDT -> ETHUSDT)
        symbol_upper = symbol_upper.replace('_', '')

        # Already standardized
        if '/' in symbol_upper:
            return symbol_upper

        # Split concatenated format (BTCUSDT -> BTC/USDT)
        for quote in SymbolDetector.CRYPTO_QUOTE_CURRENCIES:
            if symbol_upper.endswith(quote):
                base = symbol_upper[:-len(quote)]
                return f"{base}/{quote}"

        return symbol_upper

    @staticmethod
    def get_standardized_symbol(symbol: str) -> Tuple[str, AssetType]:
        """Detect asset type and return standardized symbol."""
        asset_type = SymbolDetector.detect(symbol)

        if asset_type == AssetType.CRYPTO:
            standardized = SymbolDetector.standardize_crypto_symbol(symbol)
        elif asset_type == AssetType.STOCK:
            standardized = symbol.upper().strip()
        else:
            standardized = symbol.upper().strip()

        return standardized, asset_type
