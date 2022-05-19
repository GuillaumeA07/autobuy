#!/usr/bin/python
from math import trunc
import sys
import time
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
import os
from tabulate import tabulate
from dotenv import dotenv_values
import csv


from binance.client import Client


class AutoBuy():
	def __init__(self,config,primary,amount):
		
		self.yaml_store = self.loadConfig(config)
		self.primary = primary
		self.amount = amount
		self.config = dotenv_values(".env")
		try:
			self.client = Client(self.config['KEY'], self.config['SECRET'])
		except:
			print("[!] Can't connect to binance endpoint")

		self.symbols_info = None
		self.prices = None
		self.orders_array = []

		self.run()

	def loadConfig(self,config):

		config_path = './'+config
		abs_path = os.path.abspath(config_path)

		with open(abs_path) as f:
			data = yaml.load(f, Loader=SafeLoader)
		
		return data

	def controlQty(self):
		qty = round(sum([v for k,v in self.yaml_store.items()]),4)
		if qty > 1:
			print('[!] Quantity in config file is greater than 100%')
			sys.exit(0)
		elif qty < 1:
			print('[!] Quantity in config file is lower than 100%')
			sys.exit(0)

	def controlAvailableQty(self):
		balance = self.client.get_asset_balance(asset=self.primary)
		if float(balance['free']) < float(self.amount):
			print('[!] You have insuficient balance of ', self.primary)
			sys.exit(0)

	def getBinanceSymbols(self):
		self.symbols_info = self.client.get_exchange_info()['symbols']

	def controlSymbols(self):
		symbol = [s['symbol'] for s in self.symbols_info if ('SPOT' in s['permissions'])]
		bad_symbols = []
		for k,v in self.yaml_store.items():
			if k != self.primary:
				if (k+self.primary not in symbol):
					bad_symbols.append(k)
			
		if len(bad_symbols) > 0:
			print('[!] Some symbols don\'t match with Binance symbols ', '/'.join([x+self.primary for x in bad_symbols]))
			sys.exit(0)

	def splitAmount(self):
		data = {}
		for k,v in self.yaml_store.items():
			if k != self.primary:
				o_amount = float(self.amount)*float(v)
				symbol = k+self.primary
				data[symbol] = o_amount

		return data

	def controlOrders(self,splitted_amount):
		self.prices = self.client.get_all_tickers()
	
		for k,v in splitted_amount.items():
			secondary = k.split(self.primary)[0]
			usd_price = float([p['price'] for p in self.prices if p['symbol'] == secondary+self.primary][0])
			minimum_order = float([f['minQty'] for s in self.symbols_info if s['symbol'] == k for f in s['filters'] if f['filterType'] == 'LOT_SIZE'][0])
			asset_price = float([p['price'] for p in self.prices if p['symbol'] == k][0])
			if v/asset_price < minimum_order or v/asset_price*usd_price < 10:
				print('[!] Check quantity for ', k , ' or allow more alocation')
				sys.exit(0)
				
		return splitted_amount

	def passOrders(self,splitted_amount):
		for k,v in splitted_amount.items():
			asset_price = float([p['price'] for p in self.prices if p['symbol'] == k][0])
			precision = [int(s['baseAssetPrecision']) for s in self.symbols_info if s['symbol'] == k][0]
			qty = "{:0.0{}f}".format( v/asset_price, precision)
			step_size = float([f['stepSize'] for s in self.symbols_info if s['symbol'] == k for f in s['filters'] if f['filterType'] == 'LOT_SIZE'][0])
			qty = round(trunc(float(qty)/float(step_size))*float(step_size),precision)
			try:
				order = self.client.order_market_buy(symbol=k,quantity=qty)
				symbol = order['symbol']
				exec_qty = float(order['executedQty'])
				cumul_quote_qty = order['cummulativeQuoteQty']
				commission = sum([float(c['commission']) for c in order['fills']])
				exec_price = sum([float(c['qty'])*float(c['price']) for c in order['fills']])/exec_qty
				commission_asset = order['fills'][0]['commissionAsset']
				transact_time = datetime.fromtimestamp(trunc(order['transactTime']/1000))

				self.orders_array.append({'symbol': symbol,'qty': exec_qty, 'price': exec_price, 'quoteQty': cumul_quote_qty, 'commission': commission, 'commissionAsset' :commission_asset, 'time': transact_time})
				time.sleep(0.5)
			except Exception as e:
				print('[!] Unable to pass order for ', k)
				print(e)

	def formatOutput(self):
		arr = []
		for x in self.orders_array:
			obj_a = []
			for k,v in x.items():
				obj_a.append(v)
			arr.append(obj_a)
		return arr

	def saveToCSV(self,data):
		f = open('./orders.csv','a+')
		obj = csv.writer(f)
		for d in data:
			obj.writerow(d)
		f.close()

	def run(self):
		#Control quantity in config file
		self.controlQty()
		#Control available primary asset
		self.controlAvailableQty()
		#Get symbol present on binance
		self.getBinanceSymbols()
		#Control symbol in config file
		self.controlSymbols()
		#Split amount in orders
		splitted_amount = self.splitAmount()
		#Control that order match minimum order
		self.controlOrders(splitted_amount)
		#Passing orders at market
		self.passOrders(splitted_amount)
		orders = self.formatOutput()
		#Save to csv
		self.saveToCSV(orders)
		#Print
		print(' ')
		print (tabulate(orders, headers=['Symbol',"Qty", "Price", "QuoteQty", "Commission",'CommAsset','Time']))
		print(' ')
		print(' ')

if __name__ == '__main__':
	import os
	import sys
	import argparse

	my_parser = argparse.ArgumentParser()
	my_parser.add_argument('-c',help='Config file', required=True)
	my_parser.add_argument('-p',help='Primary asset to buy with',required=True)
	my_parser.add_argument('-a',help='Amount to spend on buying',required=True)
	
	args = my_parser.parse_args()
	print('[*] Config File: ', str(args.c))
	print('[*] Using ', str(args.p), 'to buy')
	print('[*]',str(args.a),' ',str(args.p),' will be spend on different orders')
	AutoBuy(args.c, args.p, args.a)