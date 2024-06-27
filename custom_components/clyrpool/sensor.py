import logging
from datetime import timedelta
import time

import voluptuous as vol
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, UnitOfTemperature
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Clyrpool Water Quality'
SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    email = config[CONF_EMAIL]
    password = config[CONF_PASSWORD]

    add_entities([ClyrpoolWaterQualitySensor(email, password)], True)

class ClyrpoolWaterQualitySensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, email, password):
        """Initialize the sensor."""
        self._state = None
        self._email = email
        self._password = password
        self._ph = None
        self._orp = None
        self._water_level = None
        self._water_temp = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return DEFAULT_NAME

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            'ph': self._ph,
            'orp': self._orp,
            'water_level': self._water_level,
            'water_temp': self._water_temp,
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    def update(self):
        """Fetch new state data for the sensor."""
        try:
            # Set up Chrome options
            options = Options()
            options.headless = True  # Run in headless mode
            options.add_argument("--window-size=1920,1080")  # Optional: Set the window size

            # Set up the WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            # Navigate to the webpage
            url = "https://app.clyrpool.com/dashboard/location/RyiIrtevakEc2yJZSRaz/waterQuality/maintenance/"
            driver.get(url)

            # Add explicit wait to ensure the page loads completely
            wait = WebDriverWait(driver, 10)

            # Locate the email input field by its ID and enter the email address
            _LOGGER.debug("Locating email input field")
            email_input = wait.until(EC.presence_of_element_located((By.ID, "Email Address-input")))
            email_input.clear()
            email_input.send_keys(self._email)
            _LOGGER.debug("Email address entered successfully")

            # Locate the password input field by its ID and enter the password
            _LOGGER.debug("Locating password input field")
            password_input = wait.until(EC.presence_of_element_located((By.ID, "Password-input")))
            password_input.clear()
            password_input.send_keys(self._password)
            _LOGGER.debug("Password entered successfully")

            # Locate the submit button and click it
            _LOGGER.debug("Locating submit button")
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            submit_button.click()
            _LOGGER.debug("Form submitted successfully")

            # Wait for the next page to load
            driver.get(url)
            time.sleep(10)  # Adjust the sleep time if needed

            # Extract the water quality data
            _LOGGER.debug("Extracting water quality data")
            try:
                ph_element = driver.find_element(By.XPATH, "//p[text()='pH']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='pH')]")
                self._ph = ph_element.text if ph_element else None
                _LOGGER.debug("pH value: %s", self._ph)
            except Exception as e:
                _LOGGER.error("Error extracting pH value: %s", e)
                self._ph = None

            try:
                orp_element = driver.find_element(By.XPATH, "//p[text()='ORP']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='ORP')]")
                self._orp = orp_element.text if orp_element else None
                _LOGGER.debug("ORP value: %s", self._orp)
            except Exception as e:
                _LOGGER.error("Error extracting ORP value: %s", e)
                self._orp = None

            try:
                water_level_element = driver.find_element(By.XPATH, "//p[text()='Water Level']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='Water Level')]")
                self._water_level = water_level_element.text if water_level_element else None
                _LOGGER.debug("Water level value: %s", self._water_level)
            except Exception as e:
                _LOGGER.error("Error extracting water level value: %s", e)
                self._water_level = None

            try:
                water_temp_element = driver.find_element(By.XPATH, "//p[text()='Water Temp']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='Water Temp')]")
                self._water_temp = water_temp_element.text if water_temp_element else None
                _LOGGER.debug("Water temperature value: %s", self._water_temp)
            except Exception as e:
                _LOGGER.error("Error extracting water temperature value: %s", e)
                self._water_temp = None

            self._state = "OK"
            driver.quit()

        except Exception as e:
            _LOGGER.error(f"An error occurred while updating the sensor: {e}")
            self._state = None

