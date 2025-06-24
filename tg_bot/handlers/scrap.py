import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import imaplib
import email
import re
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'attempts_per_account': 6,
    'sleep_between_attempts': 2000,  # milliseconds
    'sleep_between_accounts': 1000,  # milliseconds
    'sleep_after_login': 3000,
    'otp_wait_time': 35000,
    'sleep_after_otp': 1000,
    'cycle_interval': 54 * 60 * 1000  # 54 minutes
}

# Account configuration
ACCOUNTS = [
    {
        'email': 'airdroplar834@gmail.com',
        'password': 'Cb277KmTYca$95x',
        'token_file': 'tokens-airdroplar.json'
    }
]

# Telegram Bot Configuration
BOT_TOKEN_NO_SLOTS = "7681038007:AAG35DU1fJcpCBOEC4MbPbnU0bEff3piBrA"
BOT_TOKEN_AVAILABLE = "7472884606:AAFoS-NHJmdiYNvAl1df5a-nEi360nqpMpQ"
USER_CHAT_IDS = ["237330399", "5806791136"]


class OTPExtractor:
    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password

    async def get_latest_otp(self, timeout_ms: int = 35000) -> Dict[str, Optional[str]]:
        """Extract OTP from latest email"""
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.email_address, self.app_password)
            mail.select('inbox')

            start_time = time.time()
            timeout_seconds = timeout_ms / 1000

            while time.time() - start_time < timeout_seconds:
                # Search for emails from VFS Global
                status, messages = mail.search(None, 'FROM "noreply@vfsglobal.com"')

                if status == 'OK' and messages[0]:
                    # Get the latest email
                    email_ids = messages[0].split()
                    latest_email_id = email_ids[-1]

                    # Fetch the email
                    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')

                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # Extract text content
                        body = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = email_message.get_payload(decode=True).decode()

                        # Extract OTP using regex
                        otp_pattern = r'\b\d{6}\b'
                        otp_match = re.search(otp_pattern, body)

                        if otp_match:
                            otp_code = otp_match.group()
                            logger.info(f"✅ OTP extracted: {otp_code}")
                            mail.logout()
                            return {'code': otp_code, 'error': None}

                await asyncio.sleep(2)  # Wait 2 seconds before checking again

            mail.logout()
            return {'code': None, 'error': 'Timeout waiting for OTP email'}

        except Exception as e:
            logger.error(f"❌ Error extracting OTP: {str(e)}")
            return {'code': None, 'error': str(e)}


class VFSAppointmentChecker:
    def __init__(self):
        self.driver = None

    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        # Remove headless for debugging, add back for production
        # chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver

    async def send_telegram_message(self, message: str, bot_token: str):
        """Send message to all configured Telegram chat IDs"""
        results = []

        for chat_id in USER_CHAT_IDS:
            try:
                logger.info(f"📤 Sending message to chat ID: {chat_id}")

                async with aiohttp.ClientSession() as session:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }

                    async with session.post(url, json=payload, timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"✅ Message sent successfully to {chat_id}")
                            results.append({'chat_id': chat_id, 'success': True})
                        else:
                            logger.error(f"❌ Failed to send message to {chat_id}: {response.status}")
                            results.append({'chat_id': chat_id, 'success': False})

            except Exception as error:
                logger.error(f"❌ Failed to send message to {chat_id}: {str(error)}")
                results.append({'chat_id': chat_id, 'success': False, 'error': str(error)})

        return results

    async def check_appointment_availability(self):
        """Check appointment availability on VFS Global website"""
        try:
            logger.info('🎯 Starting appointment availability check...')

            # Wait for and click "Start New Booking" button
            wait = WebDriverWait(self.driver, 15)

            try:
                # Try multiple selectors for the start booking button
                start_button = None
                button_selectors = [
                    "//button[contains(text(), 'Start New Booking')]",
                    "//button[contains(text(), 'start new booking')]",
                    "//button[contains(@class, 'btn-brand-orange')]",
                    "//button[contains(@class, 'mat-raised-button')]"
                ]

                for selector in button_selectors:
                    try:
                        start_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except TimeoutException:
                        continue

                if start_button:
                    start_button.click()
                    logger.info('✅ Successfully clicked "Start New Booking" button')
                    await asyncio.sleep(3)
                else:
                    raise Exception('Could not find "Start New Booking" button')

            except Exception as e:
                logger.error(f"❌ Error clicking start booking button: {str(e)}")
                raise

            # Wait for and open appointment category dropdown
            logger.info('🔍 Looking for appointment category dropdown...')

            try:
                # Try multiple selectors for dropdown
                dropdown_selectors = [
                    "mat-select",
                    ".mat-select",
                    "[role='combobox']",
                    ".dropdown"
                ]

                dropdown = None
                for selector in dropdown_selectors:
                    try:
                        dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        break
                    except TimeoutException:
                        continue

                if dropdown:
                    dropdown.click()
                    await asyncio.sleep(2)
                    logger.info('✅ Successfully opened dropdown')
                else:
                    raise Exception('Could not find appointment category dropdown')

            except Exception as e:
                logger.error(f"❌ Error opening dropdown: {str(e)}")
                raise

            # Select Lithuania Temporary Residence Permit option
            try:
                option_selectors = [
                    "//mat-option[contains(text(), 'Lithuania Temporary Residence Permit')]",
                    "//option[contains(text(), 'Lithuania Temporary Residence Permit')]",
                    "//div[contains(text(), 'Lithuania Temporary Residence Permit')]"
                ]

                option = None
                for selector in option_selectors:
                    try:
                        option = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except TimeoutException:
                        continue

                if option:
                    option.click()
                    logger.info('✅ Successfully selected Lithuania Temporary Residence Permit')
                    await asyncio.sleep(3)
                else:
                    raise Exception('Could not find Lithuania Temporary Residence Permit option')

            except Exception as e:
                logger.error(f"❌ Error selecting option: {str(e)}")
                raise

            # Check for appointment availability
            logger.info('🔍 Checking for appointment availability...')
            await asyncio.sleep(5)

            # Check for "no slots available" messages
            no_slots_messages = [
                'we are sorry, but no appointment slots are currently available',
                'no appointment slots are currently available',
                'please try again later',
                'currently no appointments available',
                'no slots available',
                'no appointments available'
            ]

            page_text = self.driver.page_source.lower()

            for message in no_slots_messages:
                if message in page_text:
                    logger.info('❌ No appointment slots available')

                    telegram_message = (
                        "❌ <b>No Appointment Slots Available</b>\n\n"
                        f"Time checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    )

                    await self.send_telegram_message(telegram_message, BOT_TOKEN_NO_SLOTS)
                    return 'No'

            # Check for availability indicators
            available_indicators = [
                'available appointment',
                'select appointment',
                'choose time',
                'book appointment',
                'available slots',
                'appointment available'
            ]

            for indicator in available_indicators:
                if indicator in page_text:
                    logger.info('✅ Appointment slots are available!')

                    telegram_message = (
                        "🎉 <b>APPOINTMENT SLOTS AVAILABLE!</b>\n\n"
                        f"Time found: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"URL: {self.driver.current_url}"
                    )

                    await self.send_telegram_message(telegram_message, BOT_TOKEN_AVAILABLE)
                    return 'Yes'

            # Also check for interactive elements that indicate availability
            availability_selectors = [
                '.calendar',
                '.time-slot',
                '.appointment-slot',
                '.book-button',
                'button[class*="book"]',
                'button[class*="appointment"]'
            ]

            for selector in availability_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info('✅ Appointment slots are available!')

                        telegram_message = (
                            "🎉 <b>APPOINTMENT SLOTS AVAILABLE!</b>\n\n"
                            f"Time found: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"URL: {self.driver.current_url}"
                        )

                        await self.send_telegram_message(telegram_message, BOT_TOKEN_AVAILABLE)
                        return 'Yes'
                except:
                    continue

            logger.info('❓ Could not determine availability status clearly')
            return 'Unknown'

        except Exception as error:
            logger.error(f'❌ Error checking appointment availability: {str(error)}')
            return 'Error'

    async def login_with_account(self, account: Dict, attempt_number: int, total_attempts: int):
        """Login with account credentials and check appointments"""

        try:
            logger.info(f"\n🔐 Account: {account['email']} | Attempt {attempt_number}/{total_attempts}")

            # Setup WebDriver
            self.setup_driver()

            # Initialize OTP extractor (you'll need to configure email app passwords)
            # For Gmail, you need to enable 2FA and create an app password
            otp_extractor = OTPExtractor(account['email'], "your_app_password_here")

            # Navigate to VFS Global login page
            logger.info('Navigating to VFS Global login page...')
            self.driver.get("https://visa.vfsglobal.com/uzb/en/ltp/login")

            # Wait for page to load
            wait = WebDriverWait(self.driver, 15)

            # Enter email
            logger.info('📧 Entering email...')
            email_field = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'input[type="email"], input[name="email"], input[id="email"], #email'
            )))
            email_field.clear()
            email_field.send_keys(account['email'])

            # Enter password
            logger.info('🔑 Entering password...')
            password_field = self.driver.find_element(
                By.CSS_SELECTOR,
                'input[type="password"], input[name="password"], input[id="password"], #password'
            )
            password_field.clear()
            password_field.send_keys(account['password'])

            # Click login button
            logger.info('🚀 Clicking initial login button...')
            login_button_selectors = [
                'button.mat-stroked-button',
                'button[mat-stroked-button]',
                'button.btn.mat-btn-lg.btn-block',
                "//button[contains(text(), 'Sign In')]",
                "//button[contains(text(), 'sign in')]"
            ]

            login_button = None
            for selector in login_button_selectors:
                try:
                    if selector.startswith('//'):
                        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue

            if login_button:
                login_button.click()
                logger.info('✅ Successfully clicked login button')
            else:
                raise Exception('Could not find login button')

            await asyncio.sleep(CONFIG['sleep_after_login'] / 1000)

            # Wait for OTP field
            logger.info('⏳ Waiting for OTP input field...')
            await asyncio.sleep(35)  # Wait for email to arrive

            try:
                otp_field_selectors = [
                    'input[type="text"][placeholder*="OTP"]',
                    'input[name*="otp"]',
                    'input[id*="otp"]',
                    'input[placeholder*="code"]',
                    'input[placeholder*="verification"]'
                ]

                otp_field = None
                for selector in otp_field_selectors:
                    try:
                        otp_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        break
                    except TimeoutException:
                        continue

                if otp_field:
                    logger.info('🔢 OTP field detected, waiting for email...')

                    # Get OTP from email
                    otp_result = await otp_extractor.get_latest_otp(CONFIG['otp_wait_time'])

                    if not otp_result['code']:
                        raise Exception('Failed to retrieve OTP from email')

                    logger.info(f"✅ OTP received: {otp_result['code']}")

                    # Enter OTP
                    logger.info('🔢 Entering OTP...')
                    otp_field.clear()
                    otp_field.send_keys(otp_result['code'])

                    await asyncio.sleep(CONFIG['sleep_after_otp'] / 1000)

                    # Click verify button
                    logger.info('🔐 Clicking verify/login button...')
                    verify_button_selectors = [
                        "//button[contains(text(), 'Sign In')]",
                        "//button[contains(text(), 'Verify')]",
                        "//button[contains(text(), 'Login')]",
                        "//button[contains(text(), 'Submit')]",
                        'button[type="submit"]'
                    ]

                    verify_button = None
                    for selector in verify_button_selectors:
                        try:
                            if selector.startswith('//'):
                                verify_button = self.driver.find_element(By.XPATH, selector)
                            else:
                                verify_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                            if verify_button and verify_button.is_enabled():
                                break
                        except NoSuchElementException:
                            continue

                    if verify_button:
                        verify_button.click()
                        logger.info('✅ Successfully clicked verify button')

                    # Wait for navigation
                    await asyncio.sleep(5)

            except TimeoutException:
                logger.info('⚠️ No OTP field found, assuming direct login')

            logger.info('🎯 Login successful, now checking appointment availability...')

            # Check appointment availability
            availability_status = await self.check_appointment_availability()

            logger.info(f"🏁 Final result for {account['email']}: Availability = {availability_status}")

            return {
                'account': account['email'],
                'attempt': attempt_number,
                'success': True,
                'appointment_available': availability_status,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as error:
            logger.error(f"❌ Login error for {account['email']}: {str(error)}")

            return {
                'account': account['email'],
                'attempt': attempt_number,
                'success': False,
                'error': str(error),
                'timestamp': datetime.now().isoformat()
            }

        finally:
            if self.driver:
                logger.info('🔄 Closing browser...')
                self.driver.quit()


class VFSMonitorBot:
    def __init__(self):
        self.checker = VFSAppointmentChecker()

    async def run_monitoring_cycle(self):
        """Run the complete monitoring cycle"""
        cycle = 1

        while True:
            logger.info(f"\n🔁 Starting login cycle #{cycle} with {len(ACCOUNTS)} accounts...")
            logger.info(f"📋 Configuration: {CONFIG['attempts_per_account']} attempts per account")

            all_results = []

            for account_index, account in enumerate(ACCOUNTS):
                start_time = time.time()
                account_results = []

                for attempt in range(1, CONFIG['attempts_per_account'] + 1):
                    try:
                        result = await self.checker.login_with_account(account, attempt, CONFIG['attempts_per_account'])
                        account_results.append(result)

                        # Sleep between attempts (except for last attempt of last account)
                        if not (account_index == len(ACCOUNTS) - 1 and attempt == CONFIG['attempts_per_account']):
                            await asyncio.sleep(0.001)  # Minimal sleep

                    except Exception as error:
                        logger.error(f"❌ Attempt {attempt} failed for {account['email']}: {str(error)}")

                        error_result = {
                            'account': account['email'],
                            'attempt': attempt,
                            'success': False,
                            'error': str(error),
                            'timestamp': datetime.now().isoformat()
                        }

                        account_results.append(error_result)

                        if attempt < CONFIG['attempts_per_account']:
                            await asyncio.sleep(CONFIG['sleep_between_attempts'] / 1000)

                all_results.append({
                    'account': account['email'],
                    'results': account_results,
                    'success_count': sum(1 for r in account_results if r['success']),
                    'total_attempts': len(account_results)
                })

                # Sleep between accounts
                if account_index < len(ACCOUNTS) - 1:
                    logger.info(
                        f"\n⏰ Sleeping for {CONFIG['sleep_between_accounts'] / 1000}s before switching to next account...")
                    await asyncio.sleep(CONFIG['sleep_between_accounts'] / 1000)

                end_time = time.time()
                logger.info(f"⏱️ Account {account['email']} processing took {end_time - start_time:.2f} seconds")

            # Summary
            total_attempts = sum(acc['total_attempts'] for acc in all_results)
            total_successes = sum(acc['success_count'] for acc in all_results)

            logger.info('\n🎉 All accounts and attempts completed!')
            logger.info(f"📊 Summary (Cycle {cycle}): {total_successes}/{total_attempts} successful logins")

            for acc in all_results:
                logger.info(f"   {acc['account']}: {acc['success_count']}/{acc['total_attempts']} successful")

            logger.info(f"\n🛌 Sleeping for 54 minutes before starting the next cycle...")
            await asyncio.sleep(CONFIG['cycle_interval'] / 1000)

            cycle += 1


# Main execution
async def main():
    """Main function to run the VFS monitoring bot"""
    try:
        bot = VFSMonitorBot()
        await bot.run_monitoring_cycle()
    except KeyboardInterrupt:
        logger.info("❌ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())