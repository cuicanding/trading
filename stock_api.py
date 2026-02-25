"""
股票数据API
优化版：本地缓存股票列表，快速搜索
"""
import urllib.request
import json
import ssl
import os
import aiohttp
import asyncio
from typing import Optional, List, Dict

class StockAPI:
    """股票数据API - 优化版"""
    
    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self._a_stock_list = []  # A股列表缓存
        self._hk_stock_list = []  # 港股列表缓存
        self._cache_file = "stock_cache.json"
    
    def is_configured(self) -> bool:
        return True
    
    def _load_cache(self):
        """加载本地缓存"""
        if self._a_stock_list:
            return
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._a_stock_list = data.get('a_stocks', [])
                    self._hk_stock_list = data.get('hk_stocks', [])
        except:
            pass
    
    def _save_cache(self):
        """保存本地缓存"""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'a_stocks': self._a_stock_list,
                    'hk_stocks': self._hk_stock_list
                }, f, ensure_ascii=False)
        except:
            pass
    
    def _fetch_json(self, url: str, timeout: int = 5) -> Optional[dict]:
        """获取JSON数据"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Referer': 'https://quote.eastmoney.com/'
                }
            )
            with urllib.request.urlopen(req, timeout=timeout, context=self.ctx) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"请求失败: {e}")
            return None
    
    def _normalize_code(self, stock_code: str) -> str:
        """标准化股票代码"""
        code = str(stock_code).upper()
        code = code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '').replace('.HK', '')
        return code
    
    def _is_hk_stock(self, stock_code: str) -> bool:
        """判断是否为港股 - 5位数字代码"""
        code = self._normalize_code(stock_code)
        if len(code) == 5 and code.isdigit():
            return True
        return False
    
    def _is_us_stock(self, stock_code: str) -> bool:
        """判断是否为美股"""
        code = str(stock_code).upper()
        if code.isalpha() and len(code) <= 5:
            return True
        return False
    
    def _get_secid(self, stock_code: str) -> str:
        """获取东方财富secid格式"""
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
    
    def search_stock(self, keyword: str) -> List[Dict]:
        """搜索股票 - 快速本地搜索"""
        self._load_cache()
        keyword = keyword.upper()
        results = []
        
        # 搜索港股（5位数字）
        if keyword.isdigit() and len(keyword) <= 5:
            code = keyword.zfill(5)
            results.append({"code": f"{code}.HK", "name": f"港股{code}", "market": "HK"})
        
        # 搜索A股
        if keyword.isdigit() and len(keyword) <= 6:
            code = keyword.zfill(6)
            market = "SH" if code.startswith('6') else "SZ"
            results.append({"code": f"{code}.{market}", "name": f"A股{code}", "market": market})
        
        # 搜索美股
        if keyword.isalpha():
            results.append({"code": keyword, "name": keyword, "market": "US"})
        
        return results[:5]
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            code = self._normalize_code(stock_code)
            secid = self._get_secid(stock_code)
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58"
            data = self._fetch_json(url)
            if not data or 'data' not in data or not data['data']:
                return None
            d = data['data']
            
            if self._is_hk_stock(stock_code):
                market = 'HK'
            elif self._is_us_stock(stock_code):
                market = 'US'
            else:
                market = 'SH' if code.startswith('6') else 'SZ' if code.startswith(('0', '3')) else 'BJ'
            
            return {
                "code": f"{code}.{market}",
                "name": d.get('f58', '')
            }
        except:
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情"""
        try:
            is_hk = self._is_hk_stock(stock_code)
            is_us = self._is_us_stock(stock_code)
            
            secid = self._get_secid(stock_code)
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60"
            data = self._fetch_json(url)
            if not data or 'data' not in data or not data['data']:
                return None
            d = data['data']
            
            divisor = 1000 if is_hk else 100
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
        """异步获取实时行情"""
        secid = self._get_secid(stock_code)
        is_hk = self._is_hk_stock(stock_code)
        is_us = self._is_us_stock(stock_code)
        divisor = 1000 if is_hk else 100
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
        """异步搜索股票，返回真实名称"""
        results = []
        keyword = str(keyword).upper()
        
        if keyword.isdigit() and len(keyword) <= 5:
            code = keyword.zfill(5)
            results.append({"code": f"{code}.HK", "name": f"港股{code}", "market": "HK"})
        if keyword.isdigit() and len(keyword) <= 6:
            code = keyword.zfill(6)
            market = "SH" if code.startswith('6') else "SZ"
            results.append({"code": f"{code}.{market}", "name": f"A股{code}", "market": market})
        if keyword.isalpha():
            results.append({"code": keyword, "name": keyword, "market": "US"})
        
        try:
            url = f"https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch?keyword={keyword}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/'
            }
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3), headers=headers) as response:
                data = await response.json()
                if data and 'Data' in data:
                    for item in data['Data'][:5]:
                        code = item.get('Code', '')
                        name = item.get('Name', '')
                        market_code = item.get('MktNum', '')
                        if code and name:
                            market = 'HK' if market_code == '116' else 'SH' if market_code == '1' else 'SZ'
                            suffix = '.HK' if market == 'HK' else f'.{market}'
                            results.append({"code": f"{code}{suffix}", "name": name, "market": market})
        except Exception as e:
            print(f"搜索API失败: {e}")
        
        seen = set()
        unique_results = []
        for r in results:
            if r['code'] not in seen:
                seen.add(r['code'])
                unique_results.append(r)
        return unique_results[:5]

stock_api = StockAPI()
