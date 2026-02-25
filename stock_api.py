"""
股票数据API
"""
import urllib.request
import json
import ssl
import os
import aiohttp
from typing import Optional, List, Dict
import asyncio


class StockAPI:
    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self._cache_file = "stock_cache.json"

    def _normalize_code(self, stock_code: str) -> str:
        code = str(stock_code).upper()
        code = code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '').replace('.HK', '')
        return code

    def _is_hk_stock(self, stock_code: str) -> bool:
        code = self._normalize_code(stock_code)
        return len(code) == 5 and code.isdigit()

    def _is_us_stock(self, stock_code: str) -> bool:
        code = str(stock_code).upper()
        return code.isalpha() and len(code) <= 5

    def _get_secid(self, stock_code: str) -> str:
        code = self._normalize_code(stock_code)
        
        if self._is_hk_stock(stock_code):
            return f"116.{code}"
        if self._is_us_stock(stock_code):
            return f"105.{code}"
        
        if len(code) < 6 and code.isdigit():
            code = code.zfill(6)
        
        if code.startswith('6'):
            return f"1.{code}"
        elif code.startswith(('0', '3')):
            return f"0.{code}"
        elif code.startswith(('4', '8')):
            return f"0.{code}"
        return f"1.{code}"

    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        try:
            is_hk = self._is_hk_stock(stock_code)
            is_us = self._is_us_stock(stock_code)
            
            secid = self._get_secid(stock_code)
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60"
            
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://quote.eastmoney.com/'
                }
            )
            with urllib.request.urlopen(req, timeout=5, context=self.ctx) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if not data or 'data' not in data or not data['data']:
                return None
            
            d = data['data']
            divisor = 1000 if is_hk or is_us else 100
            price = d.get('f43', 0) / divisor if d.get('f43') else 0
            pre_close = d.get('f60', 0) / divisor if d.get('f60') else 0
            change = price - pre_close if pre_close > 0 else 0
            pct_chg = (change / pre_close * 100) if pre_close > 0 else 0
            currency = "HK$" if is_hk else "$" if is_us else "¥"
            
            return {
                "code": str(d.get('f57', '')),
                "name": d.get('f58', ''),
                "price": round(price, 2),
                "pre_close": round(pre_close, 2),
                "change": round(change, 2),
                "pct_chg": round(pct_chg, 2),
                "currency": currency
            }
        except:
            return None

    async def get_realtime_quote_async(self, stock_code: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        secid = self._get_secid(stock_code)
        is_hk = self._is_hk_stock(stock_code)
        is_us = self._is_us_stock(stock_code)
        divisor = 1000 if is_hk or is_us else 100
        currency = "HK$" if is_hk else "$" if is_us else "¥"
        
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/'
            }
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5), headers=headers) as response:
                data = await response.json()
                if not data or 'data' not in data or not data['data']:
                    return None
                d = data['data']
                price = d.get('f43', 0) / divisor if d.get('f43') else 0
                pre_close = d.get('f60', 0) / divisor if d.get('f60') else 0
                change = price - pre_close if pre_close > 0 else 0
                pct_chg = (change / pre_close * 100) if pre_close > 0 else 0
                return {
                    "code": str(d.get('f57', '')),
                    "name": d.get('f58', ''),
                    "price": round(price, 2),
                    "pre_close": round(pre_close, 2),
                    "change": round(change, 2),
                    "pct_chg": round(pct_chg, 2),
                    "currency": currency
                }
        except Exception as e:
            print(f"异步请求失败 [{stock_code}]: {e}")
            return None

    async def search_stock_async(self, keyword: str, session: aiohttp.ClientSession) -> List[Dict]:
        keyword = str(keyword).upper()
        results = []
        
        try:
            if keyword.isdigit():
                if len(keyword) <= 5:
                    code = keyword.zfill(5)
                    secid = f"116.{code}"
                else:
                    code = keyword.zfill(6)
                    if code.startswith('6'):
                        secid = f"1.{code}"
                    else:
                        secid = f"0.{code}"
                
                url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58"
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://quote.eastmoney.com/'
                }
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3), headers=headers) as response:
                    data = await response.json()
                    if data and 'data' in data and data['data']:
                        d = data['data']
                        code = str(d.get('f57', ''))
                        name = d.get('f58', '')
                        if code and name:
                            if len(code) == 5:
                                results.append({"code": f"{code}.HK", "name": name, "market": "HK"})
                            elif code.startswith('6'):
                                results.append({"code": f"{code}.SH", "name": name, "market": "SH"})
                            else:
                                results.append({"code": f"{code}.SZ", "name": name, "market": "SZ"})
        except Exception as e:
            print(f"行情API搜索失败: {e}")
        
        # 如果是字母（可能是美股代码），尝试从API获取
        if keyword.isalpha() and not results:
            try:
                secid = f"105.{keyword}"
                url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58"
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://quote.eastmoney.com/'
                }
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3), headers=headers) as response:
                    data = await response.json()
                    if data and 'data' in data and data['data']:
                        d = data['data']
                        name = d.get('f58', '')
                        if name:
                            results.append({"code": keyword, "name": name, "market": "US"})
            except Exception as e:
                print(f"美股搜索失败: {e}")
        
        # 不添加假结果，让搜索结果为空，前端会显示为不可选择
        
        return results[:5]
    
    INDEX_CONFIG = {
        "sh": {"secid": "1.000001", "name": "上证指数", "currency": "¥"},
        "sz": {"secid": "0.399001", "name": "深证成指", "currency": "¥"},
    }
    
    async def get_index_quotes_async(self, session: aiohttp.ClientSession) -> List[Dict]:
        results = []
        for key, config in self.INDEX_CONFIG.items():
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={config['secid']}&fields=f43,f58,f60"
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://quote.eastmoney.com/'
                }
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3), headers=headers) as response:
                    data = await response.json()
                    if data and 'data' in data and data['data']:
                        d = data['data']
                        price = d.get('f43', 0) / 100 if d.get('f43') else 0
                        pre_close = d.get('f60', 0) / 100 if d.get('f60') else 0
                        pct_chg = ((price - pre_close) / pre_close * 100) if pre_close > 0 else 0
                        results.append({
                            "key": key,
                            "name": config['name'],
                            "price": f"{price:.2f}",
                            "pct_chg": f"{pct_chg:+.2f}%",
                            "currency": config['currency'],
                            "is_up": pct_chg >= 0
                        })
            except Exception as e:
                print(f"获取指数失败 [{config['name']}]: {e}")
        return results


stock_api = StockAPI()
