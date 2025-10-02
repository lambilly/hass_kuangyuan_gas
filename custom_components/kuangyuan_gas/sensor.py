"""Sensor platform for Kuangyuan Gas."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=24)  # 24小时更新一次


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kuangyuan Gas sensor platform."""
    session = async_get_clientsession(hass)
    
    sensors = [
        GasBalanceSensor(entry, session),
        GasUsageSensor(entry, session),
        GasStatusSensor(entry, session),
        GasUpdateTimeSensor(entry, session),
    ]
    
    async_add_entities(sensors, update_before_add=True)


class KuangyuanGasSensor(SensorEntity):
    """Representation of a Kuangyuan Gas sensor."""

    def __init__(self, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._session = session
        self._attr_available = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["uno"])},
            name="燃气费查询",
            manufacturer="旷远能源",
            model="燃气用户",
        )

    async def async_update(self) -> None:
        """Fetch data from the API."""
        try:
            data = await self._fetch_gas_data()
            await self._process_data(data)
        except Exception as err:
            _LOGGER.error("Error updating sensor data: %s", err)
            self._attr_available = False

    async def _fetch_gas_data(self) -> dict[str, Any]:
        """Fetch gas data from the API."""
        url = "http://www.kynyyyt.com/member/api/gas.asp"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; JEF-AN00 Build/HUAWEIJEF-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160117 MMWEBSDK/20240301 MMWEBID/9537 MicroMessenger/8.0.48.2580(0x28003052) WeChat/arm64 Weixin NetType/5G Language/zh_CN ABI/arm64',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': self._entry.data["full_cookie"]  # 使用完整的Cookie
        }
        
        payload = {
            "ac": "query",
            "uno": self._entry.data["uno"]
        }

        _LOGGER.debug("Sending request to %s with payload %s", url, payload)
        
        async with async_timeout.timeout(30):
            async with self._session.post(
                url, headers=headers, data=payload, raise_for_status=False
            ) as response:
                html_content = await response.text()
                _LOGGER.debug("Received response: %s", html_content[:500])  # 只记录前500个字符
                if response.status != 200:
                    _LOGGER.error("API request failed with status %s: %s", response.status, html_content)
                    raise Exception(f"API request failed with status {response.status}")
                return self._parse_html_data(html_content)

    def _parse_html_data(self, html: str) -> dict[str, Any]:
        """Parse HTML data and extract gas information."""
        result = {}
        
        # 使用更灵活的正则表达式匹配表格行
        # 匹配模式：<tr><td>键</td><td>值</td></tr>
        regex = re.compile(r'<tr>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*</tr>', re.IGNORECASE)
        
        matches = regex.findall(html)
        for key, value in matches:
            clean_key = re.sub(r'[\s：:]+', '', key)  # 移除空格和冒号
            clean_value = value.strip()
            result[clean_key] = clean_value
            _LOGGER.debug("Parsed key: %s, value: %s", clean_key, clean_value)
        
        _LOGGER.debug("Parsed data: %s", result)
        return result

    async def _process_data(self, data: dict[str, Any]) -> None:
        """Process the data - to be implemented by subclasses."""
        raise NotImplementedError


class GasBalanceSensor(KuangyuanGasSensor):
    """Representation of gas balance sensor."""

    _attr_name = "燃气费余额"
    _attr_unique_id = "gas_balance"
    _attr_icon = "mdi:currency-cny"
    _attr_native_unit_of_measurement = "元"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        """Initialize the balance sensor."""
        super().__init__(entry, session)
        self._attr_unique_id = f"{entry.data['uno']}_balance"

    async def _process_data(self, data: dict[str, Any]) -> None:
        """Process balance data."""
        _LOGGER.debug("Processing balance data: %s", data)
        
        # 尝试多种可能的键名
        balance_keys = ["余额", "当前余额", "账户余额"]
        balance_value = None
        
        for key in balance_keys:
            if key in data:
                balance_str = data[key]
                _LOGGER.debug("Found balance key '%s': %s", key, balance_str)
                match = re.search(r'([\d.]+)', balance_str)
                if match:
                    balance_value = float(match.group(1))
                    break
        
        if balance_value is not None:
            self._attr_native_value = balance_value
            self._attr_available = True
            _LOGGER.debug("Set balance value: %s", balance_value)
        else:
            _LOGGER.warning("Could not find balance in data: %s", data)
            self._attr_available = False


class GasUsageSensor(KuangyuanGasSensor):
    """Representation of gas usage sensor."""

    _attr_name = "累积用气量"
    _attr_unique_id = "gas_usage"
    _attr_icon = "mdi:meter-gas-outline"
    _attr_device_class = SensorDeviceClass.GAS
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        """Initialize the usage sensor."""
        super().__init__(entry, session)
        self._attr_unique_id = f"{entry.data['uno']}_usage"

    async def _process_data(self, data: dict[str, Any]) -> None:
        """Process usage data."""
        _LOGGER.debug("Processing usage data: %s", data)
        
        # 尝试多种可能的键名
        usage_keys = ["累积用气量", "累计用气量", "用气量"]
        usage_value = None
        
        for key in usage_keys:
            if key in data:
                usage_str = data[key]
                _LOGGER.debug("Found usage key '%s': %s", key, usage_str)
                match = re.search(r'([\d.]+)', usage_str)
                if match:
                    usage_value = float(match.group(1))
                    break
        
        if usage_value is not None:
            self._attr_native_value = usage_value
            self._attr_available = True
            _LOGGER.debug("Set usage value: %s", usage_value)
        else:
            _LOGGER.warning("Could not find usage in data: %s", data)
            self._attr_available = False


class GasStatusSensor(KuangyuanGasSensor):
    """Representation of gas status sensor."""

    _attr_name = "是否通气"
    _attr_unique_id = "gas_status"
    _attr_icon = "mdi:pipe-valve"

    def __init__(self, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        """Initialize the status sensor."""
        super().__init__(entry, session)
        self._attr_unique_id = f"{entry.data['uno']}_status"

    async def _process_data(self, data: dict[str, Any]) -> None:
        """Process status data."""
        _LOGGER.debug("Processing status data: %s", data)
        
        # 尝试多种可能的键名
        status_keys = ["是否通气", "通气状态", "状态"]
        status_value = None
        
        for key in status_keys:
            if key in data:
                status_value = data[key]
                _LOGGER.debug("Found status key '%s': %s", key, status_value)
                break
        
        if status_value is not None:
            self._attr_native_value = status_value
            self._attr_available = True
            _LOGGER.debug("Set status value: %s", status_value)
        else:
            _LOGGER.warning("Could not find status in data: %s", data)
            self._attr_available = False


class GasUpdateTimeSensor(KuangyuanGasSensor):
    """Representation of gas update time sensor."""

    _attr_name = "截至时间"
    _attr_unique_id = "gas_update_time"
    _attr_icon = "mdi:update"

    def __init__(self, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        """Initialize the update time sensor."""
        super().__init__(entry, session)
        self._attr_unique_id = f"{entry.data['uno']}_update_time"

    async def _process_data(self, data: dict[str, Any]) -> None:
        """Process update time data."""
        _LOGGER.debug("Processing update time data: %s", data)
        
        # 尝试多种可能的键名
        time_keys = ["操作时间", "更新时间", "截至时间", "时间"]
        time_value = None
        
        for key in time_keys:
            if key in data:
                time_value = data[key]
                _LOGGER.debug("Found time key '%s': %s", key, time_value)
                break
        
        if time_value is not None:
            self._attr_native_value = time_value
            self._attr_available = True
            _LOGGER.debug("Set time value: %s", time_value)
        else:
            _LOGGER.warning("Could not find update time in data: %s", data)
            self._attr_available = False