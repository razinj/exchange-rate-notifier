"""Exchange rate source adapters."""

from .apilayer_exchangeratesapi import ApilayerExchangeRatesApiProvider
from .bank_al_maghrib import BankAlMaghribProvider
from .currencyapi import CurrencyApiProvider
from .exchangerate_api import ExchangeRateApiProvider
from .fawazahmed0_exchange_api import FawazAhmed0ExchangeApiProvider
from .openexchangerates import OpenExchangeRatesProvider

__all__ = [
    "ApilayerExchangeRatesApiProvider",
    "BankAlMaghribProvider",
    "CurrencyApiProvider",
    "ExchangeRateApiProvider",
    "FawazAhmed0ExchangeApiProvider",
    "OpenExchangeRatesProvider",
]
