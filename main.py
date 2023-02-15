import MetaTrader5 as mt5
import Meta5 as mt2
import asyncio
import time
import os

from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
COPY_PATH = os.getenv('COPY_PATH')
COPY_SERVER = os.getenv('COPY_SERVER')
COPY_LOGIN = os.getenv('COPY_LOGIN')
COPY_PASSWORD = os.getenv('COPY_PASSWORD')

MAIN_PATH = os.getenv('MAIN_PATH')
MAIN_SERVER = os.getenv('MAIN_SERVER')
MAIN_LOGIN = os.getenv('MAIN_LOGIN')
MAIN_PASSWORD = os.getenv('MAIN_PASSWORD')

if not mt2.initialize(path=COPY_PATH,login=int(COPY_LOGIN), server=COPY_SERVER,password=COPY_PASSWORD):
      print("initialize() failed, error code =",mt5.last_error())  

if not mt5.initialize(path=MAIN_PATH,login=int(MAIN_LOGIN), server=MAIN_SERVER,password=MAIN_PASSWORD):
      print("initialize() failed, error code =",mt2.last_error())

def generateLot(copyLot, multiplier):
  lot = copyLot * multiplier * 3.5
  if lot < 0.01:
    lot = 0.01
  return float(int(100*lot))/100

async def pendingOrder(copyOrder, mainOrder, multiplier):
  for copy in copyOrder:
    isThere = False
    for main in mainOrder:
      if str(main.comment) == str(copy.ticket):
        isThere = True
        break
    if isThere == False:
      lot = generateLot(copy.volume_current, multiplier)
      request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": copy.symbol,
        "volume": lot,
        "type": copy.type,
        "price": copy.price_open,
        "sl": copy.sl,
        "tp": copy.tp,
        "magic": 190196,
        "comment": str(copy.ticket),
        "type_time": copy.type_time,
        "type_filling": copy.type_filling,
      }
      result = mt5.order_send(request)
      if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("{} pendingOrder order_send failed, retcode={}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result.retcode))
      else:
        print("{} pendingOrder order_send(): for {} {} lots at {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), copy.symbol,lot,copy.price_open))

async def closeOrder(copyOrder, mainOrder):
  for main in mainOrder:
    isThere = False
    for copy in copyOrder:
      if str(main.comment) == str(copy.ticket):
        isThere = True
        break
    if main.comment != "" and isThere == False:
      price = main.price_current
      if main.type == mt5.ORDER_TYPE_BUY:
        price = mt5.symbol_info_tick(main.symbol).ask
      elif main.type == mt5.ORDER_TYPE_SELL:
        price = mt5.symbol_info_tick(main.symbol).bid
      
      request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": main.symbol,
        "volume": main.volume,
        "type": mt5.ORDER_TYPE_BUY if main.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
        "position": main.ticket,
        "price": price,
        "deviation": 20,
        "magic": 190196,
        "comment": "python script close",
      }
      # print(mt5.Close(symbol=main.symbol, ticket=main.ticket))
      result = mt5.order_send(request)
      if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("{} closeOrder order_send failed, retcode={}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result.retcode))
      else:
        print("{} closeOrder order_send(): for {} {} lot at {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), copy.symbol, main.volume, price))


async def dealOrder(copyOrder, mainOrder, multiplier):
  for copy in copyOrder:
    isThere = False
    for main in mainOrder:
      if str(main.comment) == str(copy.ticket):
        isThere = True
        break
    if isThere == False:
      lot = generateLot(copy.volume, multiplier)
      price = copy.price_current
      if copy.type == mt5.ORDER_TYPE_BUY:
        price = mt5.symbol_info_tick(copy.symbol).ask
      elif copy.type == mt5.ORDER_TYPE_SELL:
        price = mt5.symbol_info_tick(copy.symbol).bid

      if copy.type == mt5.ORDER_TYPE_BUY and copy.price_open < price:
        break
      if copy.type == mt5.ORDER_TYPE_SELL and copy.price_open > price:
        break
      
      request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": copy.symbol,
        "volume": lot,
        "type": copy.type,
        "price": price,
        "sl": copy.sl,
        "tp": copy.tp,
        "deviation": 20,
        "magic": 190196,
        "comment": str(copy.ticket),
      }
      result = mt5.order_send(request)
      if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("{} dealOrder order_send failed, retcode={}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result.retcode))
      else:
        print("{} dealOrder order_send(): for {} {} lot at {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), copy.symbol, lot, price))

async def modifyPendingOrder(copyOrder, mainOrder, multiplier):
  for copy in copyOrder:
    for main in mainOrder:
      if str(main.comment) == str(copy.ticket) and (main.price_open != copy.price_open or main.tp != copy.tp or main.sl != copy.sl):
        request = {
          "action": mt5.TRADE_ACTION_MODIFY,
          "symbol": copy.symbol,
          "type": copy.type,
          "price": copy.price_open,
          "sl": copy.sl,
          "tp": copy.tp,
          "magic": 190196,
          "position": main.ticket,
          "comment": str(copy.ticket),
          "type_time": copy.type_time,
          "type_filling": copy.type_filling,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
          print("{} modifyPendingOrder order_send failed, retcode={}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result.retcode))
        else:
          print("{} modifyPendingOrder order_send(): for {} ticket {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), copy.symbol, main.ticket))
        break

async def modifyOpenOrder(copyOrder, mainOrder):
  for copy in copyOrder:
    for main in mainOrder:
      if str(main.comment) == str(copy.ticket) and (main.tp != copy.tp or main.sl != copy.sl):
        request = {
          "action": mt5.TRADE_ACTION_SLTP,
          "symbol": copy.symbol,
          "sl": copy.sl,
          "tp": copy.tp,
          "position": main.ticket,
          "magic": 190196,
          "comment": str(copy.ticket),
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
          print("{} modifyOpenOrder order_send failed, retcode={}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result.retcode))
        else:
          print("{} modifyOpenOrder order_send(): for {} ticket {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), copy.symbol, main.ticket))
        break

async def removePendingOrder(copyOrder, mainOrder):
  for main in mainOrder:
    isThere = False
    for copy in copyOrder:
      if str(main.comment) == str(copy.ticket):
        isThere = True
        break
    if main.comment != "" and isThere == False:      
      request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": main.ticket,
        "comment": str(main.ticket),
        "type_time": main.type_time,
        "type_filling": main.type_filling,
      }

      result = mt5.order_send(request)
      if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("{} removePendingOrder order_send failed, retcode={}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result.retcode))
      else:
        print("{} removePendingOrder order_send(): for {} ticket {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), main.symbol, main.ticket))

async def main():
  copyAccount = mt2.account_info() 
  mainAccount = mt5.account_info() 
  copyPendingOrder = mt2.orders_get()
  mainPendingOrder = mt5.orders_get()
  copyOpenOrder = mt2.positions_get()
  mainOpenOrder = mt5.positions_get()
  
  multiplier = float(mainAccount.balance/copyAccount.balance)

  asyncio.gather(
    asyncio.create_task(pendingOrder(copyPendingOrder, mainPendingOrder, multiplier)),
    asyncio.create_task(closeOrder(copyOpenOrder, mainOpenOrder)),
    asyncio.create_task(dealOrder(copyOpenOrder, mainOpenOrder, multiplier)),
    asyncio.create_task(modifyPendingOrder(copyPendingOrder, mainPendingOrder, multiplier)),
    asyncio.create_task(modifyOpenOrder(copyOpenOrder, mainOpenOrder)),
    asyncio.create_task(removePendingOrder(copyPendingOrder, mainPendingOrder)),
  )

if __name__ == "__main__":
  while True:
    asyncio.run(main())
    time.sleep(1)