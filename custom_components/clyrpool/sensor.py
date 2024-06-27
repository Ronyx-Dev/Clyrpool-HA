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

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Water Quality'
SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    email = config[CONF_EMAIL]
    password = config[CONF_PASSWORD]

    add_entities([WaterQualitySensor(email, password)], True)

class WaterQualitySensor(SensorEntity):
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
        return TEMP_CELSIUS

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
            email_input = wait.until(EC.presence_of_element_located((By.ID, "Email Address-input")))
            email_input.clear()
            email_input.send_keys(self._email)

            # Locate the password input field by its ID and enter the password
            password_input = wait.until(EC.presence_of_element_located((By.ID, "Password-input")))
            password_input.clear()
            password_input.send_keys(self._password)

            # Locate the submit button and click it
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            submit_button.click()

            # Wait for the next page to load
            driver.get(url)
            time.sleep(10)  # Adjust the sleep time if needed

            # Extract the water quality data
            self._ph = driver.find_element(By.XPATH, "//p[text()='pH']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='pH')]").text
            self._orp = driver.find_element(By.XPATH, "//p[text()='ORP']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='ORP')]").text
            self._water_level = driver.find_element(By.XPATH, "//p[text()='Water Level']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='Water Level')]").text
            self._water_temp = driver.find_element(By.XPATH, "//p[text()='Water Temp']/ancestor::div[contains(@class, 'MuiPaper-root')]/descendant::p[contains(@class, 'MuiTypography-body1') and not(text()='Water Temp')]").text

            driver.quit()

        except Exception as e:
            _LOGGER.error(f"An error occurred while updating the sensor: {e}")
            self._state = None
