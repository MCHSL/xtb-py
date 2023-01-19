import asyncio
import datetime
import math
import time
from typing import List, Optional
import websockets
from websockets.client import WebSocketClientProtocol
import json

from commands.request import *
from commands.streaming import *

XTB_LIVE_WEBSOCKET_URL = "wss://ws.xtb.com"
XTB_LIVE_STREAMING_URL = "wss://ws.xtb.com/stream"

XTB_DEMO_WEBSOCKET_URL = "wss://ws.xtb.com/demo"
XTB_DEMO_STREAMING_URL = "wss://ws.xtb.com/demoStream"


class ClosedPosition:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.symbol = kwargs.get("symbol")
        self.volume = kwargs.get("volume")
        self.openPrice = kwargs.get("openPrice")
        self.openTime = kwargs.get("openTime")
        self.closePrice = kwargs.get("closePrice")
        self.closeTime = kwargs.get("closeTime")
        self.profit = kwargs.get("profit")

    def __repr__(self):
        return f"ClosedPosition({self.id}, {self.symbol}, {self.volume}, {self.openPrice}, {self.openTime}, {self.closePrice}, {self.closeTime}, {self.profit})"


class XTBPosition:
    def __init__(self, **kwargs):
        self.xtb: XTB = kwargs.get("xtb")
        self.id = kwargs.get("id")
        self.symbol = kwargs.get("symbol")
        self.volume = kwargs.get("volume")
        self.openPrice = kwargs.get("openPrice")
        self.openTime = kwargs.get("openTime")

    @property
    def profit(self):
        return self.xtb.positions[self.id].profit

    async def close(self):
        await self.xtb.close(self.id, volume=self.volume)
        return ClosedPosition(
            id=self.id,
            symbol=self.symbol,
            volume=self.volume,
            openPrice=self.openPrice,
            openTime=self.openTime,
            closePrice=self.openPrice,
            closeTime=datetime.datetime.now(),
            profit=self.profit,
        )

    def __repr__(self):
        return f"Position({self.id}, {self.symbol}, {self.volume}, {self.openPrice}, {self.openTime}, {self.profit})"


class XTB:
    def __init__(
        self,
        real: bool = False,
    ):
        self.websocket_url: str = (
            XTB_LIVE_WEBSOCKET_URL if real else XTB_DEMO_WEBSOCKET_URL
        )
        self.streaming_url: str = (
            XTB_LIVE_STREAMING_URL if real else XTB_DEMO_STREAMING_URL
        )
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.streaming_websocket: Optional[WebSocketClientProtocol] = None
        self.stream_session_id: Optional[str] = None
        self.message_queue = asyncio.Queue()

        self.stopped: bool = False

        self.balance_callback = None
        self.trade_callback = None
        self.profit_callback = None
        self.candle_callbacks = {}

        self.positions: dict[int, XTBPosition] = {}
        self.position_futures: dict[int, asyncio.Future] = {}

        self.last_request_action_time = 0
        self.last_streaming_action_time = 0

    async def login(self, userId: str, password: str):
        if self.websocket:
            raise Exception("Already logged in")

        self.websocket = await websockets.connect(self.websocket_url)

        login_command = LoginCommand(userId, password)
        await self.websocket.send(login_command.serialize())

        response = await self.websocket.recv()
        response = json.loads(response)

        if not response["status"]:
            raise Exception("Login failed")

        self.stream_session_id = response["streamSessionId"]
        self.streaming_websocket = await websockets.connect(self.streaming_url)

        await self.__doStreamingCommand(getTradesStreamCommand)
        await self.__doStreamingCommand(getBalanceStreamCommand)
        await self.__doStreamingCommand(getProfitStreamCommand)

        asyncio.create_task(self.__handleStreamingMessages())
        asyncio.create_task(self.__handleMessageQueue())

    async def __handleStreamingMessages(self):
        while not self.stopped:
            try:
                message = await self.streaming_websocket.recv()
                # print(message)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

            message = json.loads(message)
            if message["command"] == "trade":
                trade = StreamingTradeRecord(**message["data"])
                self.positions[trade.position] = trade

                # print(trade)

                if (
                    trade.order2 != trade.order
                    and trade.order2 in self.position_futures
                ):
                    position = XTBPosition(
                        xtb=self,
                        id=trade.order2,
                        symbol=trade.symbol,
                        volume=trade.volume,
                        openPrice=trade.openPrice,
                        openTime=trade.openTime,
                        profit=trade.profit,
                    )
                    self.positions[trade.order2] = trade
                    self.position_futures[trade.order2].set_result(position)

            await self.message_queue.put(message)

    async def __handleMessageQueue(self):
        while not self.stopped:
            message = await self.message_queue.get()
            # print(message)

            if message["command"] == "trade" and self.trade_callback:
                await self.trade_callback(StreamingTradeRecord(**message["data"]))

            elif message["command"] == "balance" and self.balance_callback:
                await self.balance_callback(StreamingBalanceRecord(**message["data"]))

            elif message["command"] == "profit":
                record = StreamingProfitRecord(**message["data"])
                if record.position in self.positions:
                    self.positions[record.position].profit = record.profit
                if self.profit_callback:
                    await self.profit_callback(record)

            elif (
                message["command"] == "candle"
                and message["data"]["symbol"] in self.candle_callbacks
            ):
                await self.candle_callbacks[message["data"]["symbol"]](
                    Candle(**message["data"])
                )

    async def __waitForTrade(self, position_id: int):
        if position_id not in self.position_futures:
            self.position_futures[
                position_id
            ] = asyncio.get_event_loop().create_future()

        position = await self.position_futures[position_id]
        del self.position_futures[position_id]
        return position

    async def __doCommand(self, command: BaseCommand, **kwargs):
        if not self.websocket:
            raise Exception("Not logged in")

        if not isinstance(command, BaseCommand):
            command = command()

        time_diff = time.time() - self.last_request_action_time
        if time_diff < 0.2:
            await asyncio.sleep(0.2 - time_diff)

        cmd = command.serialize(**kwargs)
        print(cmd)

        await self.websocket.send(cmd)

        response = await self.websocket.recv()
        response = json.loads(response)

        if not response["status"]:
            raise Exception("Command failed: " + response["errorDescr"])

        data = response["returnData"]
        print(data)

        if command.result_class:
            if isinstance(data, dict):
                return command.result_class(**data)
            else:
                return command.result_class(data)
        else:
            return data

    async def __doStreamingCommand(self, command: StreamingCommand, **kwargs):
        if not isinstance(command, StreamingCommand):
            command = command()

        if not self.streaming_websocket:
            raise Exception("Not logged in")

        ser = command.serialize(**kwargs, stream_session_id=self.stream_session_id)
        # print(ser)

        await self.streaming_websocket.send(ser)

    async def getMarginLevel(self) -> BalanceRecord:
        return await self.__doCommand(GetMarginLevelCommand)

    async def getTrades(self, opened_only: bool = True) -> List[XTBPosition]:
        return await self.__doCommand(GetTradesCommand(opened_only=opened_only))

    async def startBalanceStream(self, callback):
        self.balance_callback = callback

    async def startTradeStream(self, callback):
        self.trade_callback = callback

    async def startProfitStream(self, callback):
        self.profit_callback = callback

    async def startCandleStream(self, symbol: str, callback):
        self.candle_callbacks[symbol] = callback
        await self.__doCommand(
            GetChartLastRequestCommand(
                symbol=symbol, period=1, start=math.floor(time.time() * 1000)
            )
        )
        await self.__doStreamingCommand(getCandlesStreamCommand(symbol=symbol))

    async def getCandles(self, symbol: str, period: int, start: int):
        data = await self.__doCommand(
            GetChartLastRequestCommand(symbol=symbol, period=period, start=start)
        )

        return [Candle(**candle) for candle in data["rateInfos"]]

    async def getServerTime(self):
        return await self.__doCommand(GetServerTimeCommand)

    async def getMarginTrade(self, symbol: str, volume: float):
        result: MarginTradeRecord = await self.__doCommand(
            GetMarginTradeCommand(symbol=symbol, volume=volume)
        )

        return result.margin

    async def getSymbol(self, symbol: str) -> SymbolRecord:
        return await self.__doCommand(GetSymbolCommand(symbol=symbol))

    async def buy(self, symbol: str, volume: float) -> XTBPosition:
        result: TradeTransactionResult = await self.__doCommand(
            TradeTransactionCommand(
                tradeTransInfo=TradeTransInfo(
                    OperationType.BUY, OrderType.OPEN, symbol, volume
                )
            )
        )

        position = await self.__waitForTrade(result.order)
        return position

    async def sell(self, symbol: str, volume: float) -> StreamingTradeRecord:
        result: TradeTransactionResult = await self.__doCommand(
            TradeTransactionCommand(
                tradeTransInfo=TradeTransInfo(
                    OperationType.SELL, OrderType.OPEN, symbol, volume
                )
            )
        )

        position: StreamingTradeRecord = await self.__waitForTrade(result.order)
        return position

    async def close(self, position: int, volume: Optional[float] = None):
        pos = self.positions[position]
        await self.__doCommand(
            TradeTransactionCommand(
                tradeTransInfo=TradeTransInfo(
                    OperationType.BUY,
                    OrderType.CLOSE,
                    order=position,
                    symbol=pos.symbol,
                    volume=volume if volume else pos.volume,
                )
            )
        )
