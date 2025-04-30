import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)

DOMAIN = "unicom_bill_info"
CONF_OPENID = "openid"
# 定义 CONF_REFRESH_INTERVAL 常量
CONF_REFRESH_INTERVAL = "refresh_interval"
CONF_NAME = "name"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Unicom Bill Info from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    device_registry = dr.async_get(hass)
    # 使用配置中的 name 作为设备标识符和设备名称
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_NAME])},
        name=entry.data[CONF_NAME],
        manufacturer="中国联通",
        model="话费信息监测",
    )

    # 使用 async_forward_entry_setups 替代 async_forward_entry_setup
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True
