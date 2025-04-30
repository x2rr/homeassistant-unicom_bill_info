import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from . import DOMAIN, CONF_OPENID, CONF_REFRESH_INTERVAL

class UnicomBillInfoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            user_input[CONF_REFRESH_INTERVAL] = user_input[CONF_REFRESH_INTERVAL] * 60
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default="联通话费信息"): str,
            vol.Required(CONF_OPENID): str,
            vol.Required(CONF_REFRESH_INTERVAL, default=60): int  # 默认 60 分钟
        })
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
