import os
import time
import sys
import traceback
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options


# ------------------------------ CONFIGURE THESE ------------------------------

EXCEL_PATH = "users.csv"          # Path to your Excel file
SHEET_NAME = 0                     # Sheet index or name; 0 = first sheet
START_ROW = 0                      # 0-based index of first data row (not Excel row number)
MAX_USERS = 20                     # Submit for first 30 users

STEADFAST_CREATE_URL = "https://steadfast.com.bd/user/frauds/create"
STEADFAST_LOGIN_URL  = "https://steadfast.com.bd/login"  # If different, update this

# Put your fixed description here:
DESCRIPTION_TEXT = (
    "ma*darch*d কাস্টমার। khank*rp0la পোলায় ক্যাশ অন ডেলিভারিতে অর্ডার করছে। ওরে কল দিয়া অর্ডার কনফার্ম করা হইছে। প্রোডাক্ট পাঠানোর পরে khank*r পোলায় কয় লোকেশন এর বাইরে আছে।পরেরদিন কয় একটু পরে নিবো।একটু পরে কল দিলে আর কল ধরে নাই।মার্চেন্ট কল দিছি তাও ma*darch*d পার্সেল এর কথা শুইনা কল কাইটা দিছে আর কল ধরে নাই।নাম্বার ব্লাক লিস্টে দিয়া রাখছে ma*darch*de। এইসব kutt@r চোদা khank*r পোলারে কেউ ক্যাশ অন  ডেলিভারিতে প্রোডাক্ট পাঠাইয়েন না।তাইলে ch0d@nir পোলায় ঠিক হইবো"
)

# Credentials: either set environment variables or hard-code here (not recommended)
USERNAME = os.getenv("STEADFAST_USERNAME", "ibnasinha15@gmail.com")
PASSWORD = os.getenv("STEADFAST_PASSWORD", "P@ssword0194")

# Headless browser? Set to True for invisible browser, False to watch it work
HEADLESS = False

# Wait/Retry settings
PAGE_LOAD_TIMEOUT = 30
ELEM_TIMEOUT = 20
SLEEP_BETWEEN_SUBMISSIONS = 1  # seconds (be nice to the site / avoid rate limits)


# ------------------------ SELECTOR “GUESS LISTS” (EDIT IF NEEDED) ------------------------
# These are lists of possible selectors we try, in order. Adjust to match the site’s fields.

# Name field (column E)
NAME_LOCATORS = [
    (By.CSS_SELECTOR, 'input[name="name"]'),
    (By.CSS_SELECTOR, 'input#name'),
    (By.XPATH, '//input[contains(@name,"name")]'),
    (By.XPATH, '//label[contains(translate(normalize-space(.),"NAME","name"),"name")]/following::input[1]'),
]

# Phone field (column F)
PHONE_LOCATORS = [
    (By.CSS_SELECTOR, 'input[name="phone"]'),
    (By.CSS_SELECTOR, 'input#phone'),
    (By.XPATH, '//input[contains(@name,"phone") or contains(@id,"phone")]'),
    (By.XPATH, '//label[contains(translate(normalize-space(.),"PHONE","phone"),"phone")]/following::input[1]'),
]

# Description textarea
DESCRIPTION_LOCATORS = [
    (By.CSS_SELECTOR, 'textarea[name="description"]'),
    (By.CSS_SELECTOR, 'textarea#description'),
    (By.CSS_SELECTOR, 'textarea[name="details"]'),
    (By.CSS_SELECTOR, 'textarea#details'),
    (By.CSS_SELECTOR, 'textarea[name="comment"]'),
    (By.CSS_SELECTOR, 'textarea#comment'),
    (By.CSS_SELECTOR, 'textarea[name="note"]'),
    (By.CSS_SELECTOR, 'textarea#note'),
    (By.XPATH, '//textarea[contains(@name,"description") or contains(@id,"description")]'),
    (By.XPATH, '//textarea[contains(@name,"details") or contains(@id,"details")]'),
    (By.XPATH, '//textarea[contains(@name,"comment") or contains(@id,"comment")]'),
    (By.XPATH, '//textarea[contains(@name,"note") or contains(@id,"note")]'),
    (By.XPATH, '//label[contains(translate(normalize-space(.),"DESCRIPTION","description"),"description")]/following::textarea[1]'),
    (By.XPATH, '//label[contains(translate(normalize-space(.),"DETAILS","details"),"details")]/following::textarea[1]'),
    (By.XPATH, '//label[contains(translate(normalize-space(.),"COMMENT","comment"),"comment")]/following::textarea[1]'),
    (By.XPATH, '//label[contains(translate(normalize-space(.),"NOTE","note"),"note")]/following::textarea[1]'),
    (By.XPATH, '//textarea[contains(@placeholder,"description") or contains(@placeholder,"details") or contains(@placeholder,"comment") or contains(@placeholder,"note")]'),
    (By.XPATH, '//textarea[1]'),  # Last resort: first textarea on page
]

# Submit button
SUBMIT_LOCATORS = [
    (By.CSS_SELECTOR, 'button[type="submit"]'),
    (By.XPATH, '//button[contains(@type,"submit")]'),
    (By.XPATH, '//button[.//text()[contains(translate(.,"SUBMIT","submit"),"submit")]]'),
    (By.XPATH, '//input[@type="submit"]'),
]

# Optional: a “Create new” / “Add another” button after submitting, to go back to the form
ADD_ANOTHER_LOCATORS = [
    (By.LINK_TEXT, 'Create another'),
    (By.PARTIAL_LINK_TEXT, 'Create'),
    (By.LINK_TEXT, 'Add another'),
    (By.PARTIAL_LINK_TEXT, 'Add'),
]


# ------------------------------ HELPER FUNCTIONS ------------------------------

def get_driver():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def wait_and_find_first(driver, locators, timeout=ELEM_TIMEOUT):
    """
    Try multiple locator strategies in order; return the first WebElement that appears.
    Raises TimeoutException if none are found.
    """
    last_exc = None
    end_time = time.time() + timeout
    while time.time() < end_time:
        for by, value in locators:
            try:
                elem = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((by, value))
                )
                # also wait until interactable if input/button
                WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((by, value))
                )
                return elem
            except Exception as e:
                last_exc = e
        time.sleep(0.2)
    if last_exc:
        raise TimeoutException(f"Could not find element by any provided locator. Last error: {last_exc}")
    raise TimeoutException("Could not find element by any provided locator.")


def safe_click(driver, elem):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
        elem.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", elem)


def login_if_needed(driver):
    """
    Navigate directly to the create page. If redirected to login, try to log in.
    Adjust login field selectors if the site uses different names/ids.
    """
    driver.get(STEADFAST_CREATE_URL)
    time.sleep(1)

    # Heuristic: if we are not on the create URL after load, assume redirect to login page.
    if STEADFAST_CREATE_URL not in driver.current_url:
        # Attempt login flow
        # Guess login fields
        username_locators = [
            (By.CSS_SELECTOR, 'input[name="email"]'),
            (By.CSS_SELECTOR, 'input#email'),
            (By.CSS_SELECTOR, 'input[name="username"]'),
            (By.CSS_SELECTOR, 'input#username'),
            (By.XPATH, '//input[contains(@name,"email") or contains(@id,"email") or contains(@name,"username") or contains(@id,"username")]'),
        ]
        password_locators = [
            (By.CSS_SELECTOR, 'input[name="password"]'),
            (By.CSS_SELECTOR, 'input#password'),
            (By.XPATH, '//input[@type="password"]'),
        ]
        login_button_locators = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.XPATH, '//button[contains(@type,"submit")]'),
            (By.XPATH, '//button[.//text()[contains(translate(.,"LOGIN","login"),"login") or contains(translate(.,"SIGN IN","sign in"),"sign in")]]'),
            (By.XPATH, '//input[@type="submit"]'),
        ]

        if not USERNAME or not PASSWORD:
            raise RuntimeError(
                "Login likely required, but no credentials provided.\n"
                "Set STEADFAST_USERNAME and STEADFAST_PASSWORD environment variables, "
                "or hard-code USERNAME/PASSWORD in the script (not recommended)."
            )

        # If we know a login URL, go there first
        try:
            driver.get(STEADFAST_LOGIN_URL)
        except Exception:
            pass

        user_field = wait_and_find_first(driver, username_locators)
        pass_field = wait_and_find_first(driver, password_locators)

        user_field.clear()
        user_field.send_keys(USERNAME)
        pass_field.clear()
        pass_field.send_keys(PASSWORD)

        login_btn = wait_and_find_first(driver, login_button_locators)
        safe_click(driver, login_btn)

        # Wait until we are on the create page (or navigate there)
        try:
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(EC.url_contains("steadfast.com.bd"))
        except TimeoutException:
            pass

        # Always navigate to the fraud form after login
        if driver.current_url and STEADFAST_CREATE_URL not in driver.current_url:
            driver.get(STEADFAST_CREATE_URL)
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(EC.url_contains("/user/frauds/create"))
        elif not driver.current_url:
            # If current_url is None, navigate directly
            driver.get(STEADFAST_CREATE_URL)
            WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(EC.url_contains("/user/frauds/create"))


import os
import pandas as pd

def read_users_from_excel(path, sheet=0, start_row=0, max_users=30):
    """
    Reads Name from column A (index 0) and Phone from column B (index 1)
    from the first `max_users` rows starting at `start_row`.
    Supports .xlsx, .xls, and .csv automatically.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"EXCEL_PATH not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == ".xlsx":
            df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
        elif ext == ".xls":
            # requires xlrd
            df = pd.read_excel(path, sheet_name=sheet, engine="xlrd")
        elif ext == ".csv":
            # CSV has no sheets; treat as raw table
            # Read phone numbers as strings to preserve leading zeros
            df = pd.read_csv(path, dtype={'recipient_phone': str})
        else:
            # Last resort: try to open as xlsx then as xls then as csv
            try:
                df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
            except Exception:
                try:
                    df = pd.read_excel(path, sheet_name=sheet, engine="xlrd")
                except Exception:
                    # try CSV
                    df = pd.read_csv(path)

    except Exception as e:
        raise RuntimeError(
            "Could not read the data file. "
            "If your file is CSV, set EXCEL_PATH to the .csv and it will be read. "
            "If it’s an old Excel (.xls), install xlrd and keep the .xls extension. "
            "If it’s a real .xlsx, re-save it in Excel as .xlsx and try again.\n"
            f"Original error: {type(e).__name__}: {e}"
        )

    # Ensure we have enough columns (need at least 2 columns: 0..1)
    if df.shape[1] < 2:
        raise ValueError(
            f"Expected at least 2 columns to read A and B. "
            f"Found {df.shape[1]} columns. "
            f"Make sure Name is in column A and Phone in column B."
        )

    # Slice rows and pick columns by position (A=0, B=1) - recipient_name and recipient_phone
    sub = df.iloc[start_row:start_row + max_users, [0, 1]].copy()
    sub.columns = ["name", "phone"]
    sub = sub.dropna(how="all").fillna("")
    return sub.to_dict(orient="records")



def submit_form_for_user(driver, name, phone, description):
    print(f"  Looking for name field...")
    # Fill Name
    name_input = wait_and_find_first(driver, NAME_LOCATORS)
    name_input.clear()
    name_input.send_keys(str(name).strip())
    print(f"  ✓ Filled name: {name}")

    print(f"  Looking for phone field...")
    # Fill Phone
    phone_input = wait_and_find_first(driver, PHONE_LOCATORS)
    phone_input.clear()
    phone_input.send_keys(str(phone).strip())
    print(f"  ✓ Filled phone: {phone}")

    print(f"  Looking for description field...")
    # Fill Description
    try:
        desc_area = wait_and_find_first(driver, DESCRIPTION_LOCATORS)
        desc_area.clear()
        desc_area.send_keys(description)
        print(f"  ✓ Filled description")
    except Exception as e:
        print(f"  ✗ Could not find description field: {e}")
        print(f"  Current page URL: {driver.current_url}")
        # Try to find any textarea on the page
        try:
            textareas = driver.find_elements(By.TAG_NAME, "textarea")
            print(f"  Found {len(textareas)} textarea elements on page:")
            for i, ta in enumerate(textareas):
                print(f"    {i}: name='{ta.get_attribute('name')}' id='{ta.get_attribute('id')}' placeholder='{ta.get_attribute('placeholder')}'")
        except Exception as e2:
            print(f"  Could not inspect page elements: {e2}")
        raise

    # Submit
    submit_btn = wait_and_find_first(driver, SUBMIT_LOCATORS)
    safe_click(driver, submit_btn)

    # Wait briefly for form submission to complete
    time.sleep(1)


def navigate_back_to_form(driver):
    """
    After submission, bring the browser back to a fresh form.
    Always navigate directly to the fraud form URL to avoid wrong redirects.
    """
    print("  Navigating back to fraud form...")
    try:
        # Always go directly to the fraud form URL to avoid wrong redirects
        driver.get(STEADFAST_CREATE_URL)
        # Wait for the page to load
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(EC.url_contains("/user/frauds/create"))
        print("  ✓ Successfully returned to fraud form")
    except Exception as e:
        print(f"  ✗ Error navigating back to form: {e}")
        # Try one more time
        try:
            driver.get(STEADFAST_CREATE_URL)
            time.sleep(2)
        except Exception:
            pass
def _extract_name_phone(u):
    """
    Accepts either a dict {'name':..., 'phone':...}, a list/tuple [name, phone, ...],
    or a plain string. Returns (name, phone) as strings.
    """
    if isinstance(u, dict):
        name = str(u.get("name", "")).strip()
        phone = str(u.get("phone", "")).strip()
        return name, phone

    if isinstance(u, (list, tuple)):
        name = str(u[0] if len(u) > 0 else "").strip()
        phone = str(u[1] if len(u) > 1 else "").strip()
        return name, phone

    # Fallback: treat as a single string and leave phone blank
    return str(u).strip(), ""


def main():
    print("Reading Excel…")
    users = read_users_from_excel(EXCEL_PATH, SHEET_NAME, START_ROW, MAX_USERS)
    if not users:
        print("No users found in the specified rows/columns.")
        sys.exit(1)

    print(f"Loaded {len(users)} users (capped at {MAX_USERS}).")

    driver = get_driver()
    try:
        print("Opening site…")
        login_if_needed(driver)

        processed = 0
        for idx, u in enumerate(users, start=1):
            # Ensure we have string values and handle any data type issues
            try:
                name = str(u.get("name", "")).strip()
                phone = str(u.get("phone", "")).strip()
            except (AttributeError, TypeError):
                print(f"[{idx}] Error: Invalid data format for user {u}")
                continue

            # Basic sanity checks
            if not name and not phone:
                print(f"[{idx}] Skipped: empty name and phone")
                continue

            try:
                print(f"[{idx}] Submitting: name='{name}' phone='{phone}'")
                submit_form_for_user(driver, name, phone, DESCRIPTION_TEXT)
                processed += 1
            except Exception:
                print(f"[{idx}] Error during submission:")
                traceback.print_exc()

            # Navigate back for next entry
            try:
                navigate_back_to_form(driver)
            except Exception:
                print(f"[{idx}] Could not navigate back to fresh form, trying direct load.")
                try:
                    driver.get(STEADFAST_CREATE_URL)
                except Exception:
                    pass

            time.sleep(SLEEP_BETWEEN_SUBMISSIONS)

        print(f"Done. Successfully attempted {processed} submissions.")
    finally:
        # Give you a moment to review in non-headless mode
        if not HEADLESS:
            print("Sleeping 3 seconds before closing the browser…")
            time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    main()
