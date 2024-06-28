import logging
from datetime import timedelta

import voluptuous as vol
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_URL = "url"

DEFAULT_NAME = "Clyrpool Monitor"
SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_URL): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Clyrpool sensor."""
    email = config[CONF_EMAIL]
    password = config[CONF_PASSWORD]
    url = config[CONF_URL]
    name = config.get(CONF_NAME)

    add_entities([ClyrpoolSensor(name, email, password, url)], True)

class ClyrpoolSensor(Entity):
    """Representation of a Clyrpool sensor."""

    def __init__(self, name, email, password, url):
        """Initialize the sensor."""
        self._name = name
        self._email = email
        self._password = password
        self._url = url
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Fetch new state data for the sensor."""
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(self._url)
            wait = WebDriverWait(driver, 10)

            email_input = wait.until(EC.presence_of_element_located((By.ID, "Email Address-input")))
            email_input.clear()
            email_input.send_keys(self._email)

            password_input = wait.until(EC.presence_of_element_located((By.ID, "Password-input")))
            password_input.clear()
            password_input.send_keys(self._password)

            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            submit_button.click()

            # Add a wait to ensure the next page loads
            wait.until(EC.url_changes(self._url))
            time.sleep(10)  # Adjust the sleep time if needed

            ph_value = driver.find_element(By.XPATH, "//p[text()='pH']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='pH')]").text
            orp_value = driver.find_element(By.XPATH, "//p[text()='ORP']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='ORP')]").text
            water_level_value = driver.find_element(By.XPATH, "//p[text()='Water Level']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='Water Level')]").text
            water_temp_value = driver.find_element(By.XPATH, "//p[text()='Water Temp']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='Water Temp')]").text

            self._state = "Online"
            self._attributes = {
                "pH": ph_value,
                "ORP": orp_value,
                "Water Level": water_level_value,
                "Water Temperature": water_temp_value
            }

        except Exception as e:
            _LOGGER.error("An error occurred while updating the sensor: %s", e)
            self._state = "Error"
            self._attributes = {}

        finally:
            driver.quit()
