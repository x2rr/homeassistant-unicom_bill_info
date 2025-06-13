import logging
import asyncio
import aiohttp
import uuid
import re
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from . import DOMAIN, CONF_REFRESH_INTERVAL, CONF_NAME

_LOGGER = logging.getLogger(__name__)
CONF_OPENID = "openid"
BALANCE_URL = "https://mina.10010.com/wxapplet/weixinNew/sspbalcbroadcast"
USAGE_URL = "https://mina.10010.com/wxapplet/weixinNew/sspbigball"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    openid = entry.data.get(CONF_OPENID)
    session = async_get_clientsession(hass)
    refresh_interval = entry.data.get(CONF_REFRESH_INTERVAL, 60 * 60)
    name = entry.data.get(CONF_NAME)

    entities = [
        UnicomBillSensor(session, openid, entry.entry_id, name, "话费余额", "¥", "CURNT_BALANCE_CUST", BALANCE_URL, "mdi:currency-cny", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "剩余流量", "GB", "x_canuse_value_data_2", USAGE_URL, "mdi:network", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "已用流量", "GB", "x_used_value_data_2", USAGE_URL, "mdi:network", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "总流量", "GB", "ADDUP_UPPER_2", USAGE_URL, "mdi:gauge-full", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "流量用量百分比", "%", "flow_usage_percentage", USAGE_URL, "mdi:percent", refresh_interval),

        UnicomBillSensor(session, openid, entry.entry_id, name, "剩余通话时间", "分钟", "x_canuse_value_data_0", USAGE_URL, "mdi:phone-in-talk", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "已用通话时间", "分钟", "x_used_value_data_0", USAGE_URL, "mdi:phone-check", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "总通话时间", "分钟", "ADDUP_UPPER_0", USAGE_URL, "mdi:phone-plus", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "通话用量百分比", "%", "call_usage_percentage", USAGE_URL, "mdi:percent", refresh_interval),

        UnicomBillSensor(session, openid, entry.entry_id, name, "剩余短信", "条", "x_canuse_value_data_1", USAGE_URL, "mdi:message-text-outline", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "已用短信", "条", "x_used_value_data_1", USAGE_URL, "mdi:message-check-outline", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "短信总数", "条", "ADDUP_UPPER_1", USAGE_URL, "mdi:message", refresh_interval),

        UnicomBillSensor(session, openid, entry.entry_id, name, "可用赠款", "¥", "AVAIL_GRANTS", BALANCE_URL, "mdi:gift", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "冻结赠款", "¥", "FROZEN_GRANTS", BALANCE_URL, "mdi:lock", refresh_interval),
        UnicomBillSensor(session, openid, entry.entry_id, name, "可用预存", "¥", "AVAIL_PREFEE", BALANCE_URL, "mdi:wallet", refresh_interval),
    ]

    async_add_entities(entities)

    def update_callback(now):
        for entity in entities:
            hass.async_create_task(entity.async_update())

    async_track_time_interval(hass, update_callback, timedelta(seconds=refresh_interval))


class UnicomBillSensor(Entity):
    def __init__(self, session, openid, entry_id, device_name, name, unit, data_key, url, icon, refresh_interval):
        self._session = session
        self._openid = openid
        self._entry_id = entry_id
        self._device_name = device_name
        self._name = f"{device_name} {name}"
        self._unit_default = unit
        self._unit_dynamic = unit
        self._data_key = data_key
        self._state = None
        self._unique_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{device_name}-{name}"))
        self._url = url
        self._icon = icon

    @property
    def name(self):
        return self._name

    @property
    def unit_of_measurement(self):
        return self._unit_dynamic

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_name)},
        )

    @property
    def icon(self):
        return self._icon

    async def async_update(self):
        try:
            payload = {"openid": self._openid, "channel": "wxmini"}
            async with self._session.post(self._url, json=payload) as response:
                data = await response.json()
                if data["code"] == "0000":
                    if self._url == USAGE_URL:
                        # 通话
                        if self._data_key == "x_canuse_value_data_0":
                            value = data["data"][0]["X_CANUSE_VALUE"]
                            self._state = float(re.sub(r'[^\d.]', '', value))
                            self._unit_dynamic = "分钟"
                        elif self._data_key == "x_used_value_data_0":
                            value = data["data"][0]["X_USED_VALUE"]
                            self._state = float(re.sub(r'[^\d.]', '', value))
                            self._unit_dynamic = "分钟"
                        elif self._data_key == "ADDUP_UPPER_0":
                            value = data["data"][0]["ADDUP_UPPER"]
                            self._state = float(re.sub(r'[^\d.]', '', value))
                            self._unit_dynamic = "分钟"
                        elif self._data_key == "call_usage_percentage":
                            used = float(re.sub(r'[^\d.]', '', data["data"][0]["X_USED_VALUE"]))
                            total = float(re.sub(r'[^\d.]', '', data["data"][0]["ADDUP_UPPER"]))
                            self._state = round((used / total) * 100, 2) if total > 0 else 0
                            self._unit_dynamic = "%"
                        # 短信
                        elif self._data_key == "x_canuse_value_data_1":
                            value = data["data"][1]["X_CANUSE_VALUE"]
                            self._state = int(re.sub(r'[^\d]', '', value))
                            self._unit_dynamic = "条"
                        elif self._data_key == "x_used_value_data_1":
                            value = data["data"][1]["X_USED_VALUE"]
                            self._state = int(re.sub(r'[^\d]', '', value))
                            self._unit_dynamic = "条"
                        elif self._data_key == "ADDUP_UPPER_1":
                            value = data["data"][1]["ADDUP_UPPER"]
                            self._state = int(re.sub(r'[^\d]', '', value))
                            self._unit_dynamic = "条"
                        # 流量
                        elif self._data_key == "x_canuse_value_data_2":
                            value = data["data"][2]["X_CANUSE_VALUE"]
                            num = float(re.sub(r'[^\d.]', '', value))
                            if "MB" in value or num < 1:
                                self._state = num if "MB" in value else num * 1024
                                self._unit_dynamic = "MB"
                            else:
                                self._state = num
                                self._unit_dynamic = "GB"
                        elif self._data_key == "x_used_value_data_2":
                            value = data["data"][2]["X_USED_VALUE"]
                            num = float(re.sub(r'[^\d.]', '', value))
                            if "MB" in value or num < 1:
                                self._state = num if "MB" in value else num * 1024
                                self._unit_dynamic = "MB"
                            else:
                                self._state = num
                                self._unit_dynamic = "GB"
                        elif self._data_key == "ADDUP_UPPER_2":
                            value = data["data"][2]["ADDUP_UPPER"]
                            num = float(re.sub(r'[^\d.]', '', value))
                            if "MB" in value or num < 1:
                                self._state = num if "MB" in value else num * 1024
                                self._unit_dynamic = "MB"
                            else:
                                self._state = num
                                self._unit_dynamic = "GB"
                        elif self._data_key == "flow_usage_percentage":
                            used = data["data"][2]["X_USED_VALUE"]
                            total = data["data"][2]["ADDUP_UPPER"]
                            used_val = float(re.sub(r'[^\d.]', '', used))
                            if "MB" in used:
                                used_val = used_val / 1024
                            total_val = float(re.sub(r'[^\d.]', '', total))
                            self._state = round((used_val / total_val) * 100, 2) if total_val > 0 else 0
                            self._unit_dynamic = "%"
                    elif self._url == BALANCE_URL:
                        if self._data_key in data["data"][0]:
                            self._state = data["data"][0][self._data_key]
                            self._unit_dynamic = self._unit_default
                        else:
                            _LOGGER.error(f"Key {self._data_key} not found in response data: {data}")
                else:
                    _LOGGER.error("Failed to fetch data: %s", data)
        except Exception as e:
            _LOGGER.error("Error fetching data: %s", e)
