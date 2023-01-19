from .base_commands import StreamingCommand


class getBalanceStreamCommand(StreamingCommand):
    command = "getBalance"


class getTradesStreamCommand(StreamingCommand):
    command = "getTrades"


class getProfitStreamCommand(StreamingCommand):
    command = "getProfits"


class getCandlesStreamCommand(StreamingCommand):
    command = "getCandles"

    def __init__(self, symbol, **kwargs):
        self.arguments = {"symbol": symbol, **kwargs}


class StreamingProfitRecord:
    def __init__(self, **kwargs):
        self.order = kwargs.get("order")
        self.order2 = kwargs.get("order2")
        self.position = kwargs.get("position")
        self.profit = kwargs.get("profit")


class StreamingTradeRecord:
    def __init__(self, **kwargs):
        self.symbol: str = kwargs.get("symbol")
        self.volume = kwargs.get("volume")
        self.openPrice = kwargs.get("openPrice")
        self.closePrice = kwargs.get("closePrice")
        self.profit = kwargs.get("profit")
        self.openTime = kwargs.get("openTime")
        self.closeTime = kwargs.get("closeTime")
        self.comment = kwargs.get("comment")
        self.commission = kwargs.get("commission")
        self.swaps = kwargs.get("swaps")
        self.order = kwargs.get("order")
        self.order2 = kwargs.get("order2")
        self.position: int = kwargs.get("position")
        self.type = kwargs.get("type")
        self.operation = kwargs.get("cmd")
        self.offset = kwargs.get("offset")
        self.expiration = kwargs.get("expiration")
        self.tp = kwargs.get("tp")
        self.sl = kwargs.get("sl")

    def __str__(self):
        return (
            f"TradeRecord(symbol={self.symbol},\n"
            f"volume={self.volume},\n"
            f"openPrice={self.openPrice},\n"
            f"closePrice={self.closePrice},\n"
            f"profit={self.profit},\n"
            f"openTime={self.openTime},\n"
            f"closeTime={self.closeTime},\n"
            f"comment={self.comment},\n"
            f"commission={self.commission},\n"
            f"swaps={self.swaps},\n"
            f"order={self.order},\n"
            f"order2={self.order2},\n"
            f"position={self.position},\n"
            f"type={self.type},\n"
            f"operation={self.operation},\n"
            f"offset={self.offset},\n"
            f"expiration={self.expiration},\n"
            f"tp={self.tp},\n"
            f"sl={self.sl})"
        )
