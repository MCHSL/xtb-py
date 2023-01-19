from enum import Enum
from typing import Optional
from .base_commands import BaseCommand


def ArrayOf(cls):
    def wrapper(_, items):
        return [cls(**item) for item in items]

    return wrapper


class LoginCommand(BaseCommand):
    command = "login"

    def __init__(self, userId, password, **kwargs):
        self.arguments = {"userId": userId, "password": password, **kwargs}


class TradeTransactionResult:
    def __init__(self, **kwargs):
        self.order = kwargs.get("order")


class TradeTransactionCommand(BaseCommand):
    command = "tradeTransaction"
    result_class = TradeTransactionResult


class BalanceRecord:
    def __init__(self, **kwargs):
        self.currency = kwargs.get("currency")
        self.balance = kwargs.get("balance")
        self.equity = kwargs.get("equity")
        self.margin = kwargs.get("margin")
        self.freeMargin = kwargs.get("marginFree")
        if not self.freeMargin:
            self.freeMargin = kwargs.get("margin_free")
        self.marginLevel = kwargs.get("marginLevel")
        if not self.marginLevel:
            self.marginLevel = kwargs.get("margin_level")

    def __repr__(self):
        return f"BalanceRecord(currency={self.currency}, balance={self.balance}, equity={self.equity}, margin={self.margin}, freeMargin={self.freeMargin}, marginLevel={self.marginLevel})"


class StreamingBalanceRecord:
    def __init__(self, **kwargs):
        self.balance = kwargs.get("balance")
        self.equity = kwargs.get("equity")
        self.margin = kwargs.get("margin")
        self.freeMargin = kwargs.get("marginFree")
        self.marginLevel = kwargs.get("marginLevel")


class GetMarginLevelCommand(BaseCommand):
    command = "getMarginLevel"
    result_class = BalanceRecord


class ServerTime:
    def __init__(self, **kwargs):
        self.time = kwargs.get("time")
        self.timeString = kwargs.get("timeString")


class GetServerTimeCommand(BaseCommand):
    command = "getServerTime"
    result_class = ServerTime


class GetChartLastRequestCommand(BaseCommand):
    command = "getChartLastRequest"

    def __init__(self, symbol: str, period: int, start: int, **kwargs):
        self.arguments = {
            "info": {"symbol": symbol, "period": period, "start": start},
            **kwargs,
        }


class OperationType(Enum):
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BALANCE = 6
    CREDIT = 7


class OrderType(Enum):
    OPEN = 0
    PENDING = 1
    CLOSE = 2
    MODIFY = 3
    DELETE = 4


class TradeTransInfo:
    def __init__(
        self,
        operation: OperationType,
        type: OrderType,
        symbol: str,
        volume: float,
        customComment: str = "",
        expiration: Optional[int] = None,
        offset: int = 0,
        order: Optional[int] = None,
        price: float = 1,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ):
        self.operation = operation
        self.type = type
        self.symbol = symbol
        self.volume = volume
        self.customComment = customComment
        self.expiration = expiration
        self.offset = offset
        self.order = order
        self.price = price
        self.sl = sl
        self.tp = tp

    def serialize(self) -> dict:
        return {
            "cmd": self.operation.value,
            "type": self.type.value,
            "symbol": self.symbol,
            "volume": self.volume,
            "customComment": self.customComment,
            "expiration": self.expiration,
            "offset": self.offset,
            "order": self.order,
            "price": self.price,
            "sl": self.sl,
            "tp": self.tp,
        }


class Candle:
    def __init__(self, **kwargs):
        self.symbol = kwargs.get("symbol")
        self.ctm = kwargs.get("ctm")
        self.ctmString = kwargs.get("ctmString")
        self.open = kwargs.get("open")
        self.high = kwargs.get("high")
        self.low = kwargs.get("low")
        self.close = kwargs.get("close")
        self.vol = kwargs.get("vol")


class CandleRequestResult:
    def __init__(self, **kwargs):
        self.digits = kwargs.get("digits")
        self.candles = [Candle(**candle) for candle in kwargs.get("rateInfos")]


class TradeRecord:
    def __init__(self, **kwargs):
        self.order = kwargs.get("order")
        self.symbol = kwargs.get("symbol")
        self.volume = kwargs.get("volume")
        self.operation = kwargs.get("cmd")
        self.position = kwargs.get("position")
        self.close_price = kwargs.get("close_price")

    def __repr__(self):
        return f"TradeRecord(order={self.order}, symbol={self.symbol}, volume={self.volume}, operation={self.operation}, position={self.position})"


class GetTradesCommand(BaseCommand):
    command = "getTrades"
    result_class = ArrayOf(TradeRecord)

    def __init__(self, opened_only: bool = True, **kwargs):
        self.arguments = {"openedOnly": opened_only, **kwargs}


class MarginTradeRecord:
    def __init__(self, **kwargs):
        self.margin = kwargs.get("margin")

    def __repr__(self):
        return f"MarginTradeRecord(margin={self.margin})"


class GetMarginTradeCommand(BaseCommand):
    command = "getMarginTrade"
    result_class = MarginTradeRecord

    def __init__(self, symbol: str, volume: float, **kwargs):
        self.arguments = {"symbol": symbol, "volume": volume, **kwargs}


class SymbolRecord:
    def __init__(self, **kwargs):
        self.symbol = kwargs.get("symbol")
        self.ask = kwargs.get("ask")
        self.bid = kwargs.get("bid")
        self.contractSize = kwargs.get("contractSize")
        self.currency = kwargs.get("currency")
        self.leverage = kwargs.get("leverage") * 0.01  # percentage
        self.lot_min = kwargs.get("lotMin")
        self.lot_max = kwargs.get("lotMax")
        self.lot_step = kwargs.get("lotStep")

    def __repr__(self):
        return f"SymbolRecord(symbol={self.symbol}, ask={self.ask}, bid={self.bid}, contractSize={self.contractSize}, currency={self.currency}, leverage={self.leverage}, lot_min={self.lot_min}, lot_max={self.lot_max}, lot_step={self.lot_step})"


class GetSymbolCommand(BaseCommand):
    command = "getSymbol"
    result_class = SymbolRecord

    def __init__(self, symbol: str, **kwargs):
        self.arguments = {"symbol": symbol, **kwargs}
