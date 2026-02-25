"""
测试指数配置
"""
import pytest
from stock_api import StockAPI


def test_index_config_contains_all_markets():
    """验证指数配置包含港股和美股"""
    api = StockAPI()
    assert 'hsi' in api.INDEX_CONFIG
    assert 'hstech' in api.INDEX_CONFIG
    assert 'ixic' in api.INDEX_CONFIG
    assert 'dji' in api.INDEX_CONFIG
    assert 'sp500' in api.INDEX_CONFIG


def test_get_secid_for_index_codes():
    """验证指数代码获取正确的 secid"""
    api = StockAPI()
    # 港股指数
    assert api._get_secid('HSI') == '100.HSI'
    assert api._get_secid('HSTECH') == '100.HSTECH'
    # 美股指数
    assert api._get_secid('IXIC') == '100.IXIC'
    assert api._get_secid('DJI') == '100.DJI'
    assert api._get_secid('SPX') == '100.SPX'
    assert api._get_secid('SP500') == '100.SPX'
