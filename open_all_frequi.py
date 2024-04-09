
"""
Usage Instructions:

    Ensure Python and Selenium WebDriver are installed in your environment.
    Install the Chrome WebDriver and ensure it's accessible in your system's PATH or specify its path when initializing the webdriver.Chrome() instance.
    Place the strategy_url_mappings.json file in the same directory as this script or provide the absolute path to the file when initializing StrategyActionExecutor.
    Run the script using python3 script_name.py, where script_name.py is the name you've given to this script.

JSON File Format:

The strategy_url_mappings.json file should contain a JSON object with strategy names as keys and their corresponding URLs as values, similar to the example provided.

json

{
    "StrategyName1": "http://localhost:6970",
    "StrategyName2": "http://localhost:6971",
    ...
}

Note:

This script uses hardcoded placeholder values ('1') for some form fields and assumes a certain structure of the web page it interacts with. Adjust the script accordingly to fit the specific requirements and structure of your web interface.

"""


import json
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class StrategyActionExecutor:
    """
    A class to execute predefined actions for a list of strategies on a web interface.

    Attributes:
        mappings_file (str): The path to the JSON file containing strategy-url mappings.
        initial_url (str): The initial URL to start automation on, defaults to 'http://localhost:6970'.
        driver: Instance of Selenium WebDriver for browser automation.
        mappings (dict): Dictionary loaded from the JSON file containing strategy-url mappings.
    """

    def __init__(self, mappings_file, initial_url='http://localhost:6900'):
        """
        Initializes the StrategyActionExecutor with mappings file and initial URL.

        Parameters:
            mappings_file (str): The path to the JSON file containing strategy-url mappings.
            initial_url (str): The initial URL to start automation on.
        """
        self.mappings_file = mappings_file
        self.initial_url = initial_url
        self.driver = webdriver.Chrome()  # Initialize the Chrome WebDriver
        self.load_mappings()

    def load_mappings(self):
        """Loads strategy-url mappings from the specified JSON file."""
        with open(self.mappings_file, 'r') as file:
            self.mappings = json.load(file)

    def execute_actions(self):
        """
        Executes predefined actions for each strategy defined in mappings.
        Actions include navigating to initial_url, clicking buttons, and filling out forms.
        """
        self.driver.get(self.initial_url)
        time.sleep(1)  # Ensure the page has loaded

        first_run = True  # Flag to check if it's the first strategy being executed

        for strategy, url in self.mappings.items():
            print(f"Executing actions for {strategy} at {url}")
            try:
                # Click the 'Login' button on the first run, else click 'Add new bot'
                button_text = "Login" if first_run else "Add new bot"
                action_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f'//button[text()="{button_text}"]'))
                    )
                action_button.click()
                print(f'Clicked the {button_text} button')
            except Exception as e:
                print(f"Error clicking the button for {strategy}: {e}")
                return

            try:

                time.sleep(0.3)

                # Use ActionChains to simulate form filling
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.TAB * 2)  # Skip to the form
                actions.send_keys(strategy)  # Input strategy name
                actions.send_keys(Keys.TAB).send_keys(url)  # Input strategy URL
                actions.send_keys(Keys.TAB).send_keys('1')  # Input a placeholder value
                actions.send_keys(Keys.TAB).send_keys('1')  # Input another placeholder value
                actions.send_keys(Keys.TAB * 2).send_keys(Keys.ENTER)  # Submit the form
                actions.perform()

                print(f"Form submitted for {strategy}")
                time.sleep(0.3)

                first_run = False  # Update flag after the first iteration

            except Exception as e:
                print(f"Error executing actions for {strategy}: {e}")
                input("\n\n\n\nPress Enter to continue...")
                continue

        input("\n\n\n\nPress Enter to close the browser...")
        self.driver.quit()
        print('Browser closed')


if __name__ == "__main__":
    # Ensure the JSON file with mappings is in the same directory as this script or provide the full path.
    executor = StrategyActionExecutor('strategy_url_mappings.json')
    executor.execute_actions()
