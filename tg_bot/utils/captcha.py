from time import sleep
from DrissionPage import ChromiumPage
from tg_bot.utils.proxy import create_page_with_proxy


def bypass_and_register(proxy=None):
    print("🚀 Starting browser session...")

    p: ChromiumPage = create_page_with_proxy(proxy)
    p.get("https://uz-appointment.visametric.com/uz/appointment-form")
    sleep(5)  # Allow page and scripts to load

    print("🔍 Scanning for iframes...")
    frames = p.eles('tag:iframe')
    print(f"🧩 Found {len(frames)} iframes on page.")

    captcha_frame = None

    for idx, frame in enumerate(frames):
        src = frame.attr('src') or ''
        print(f"  🔗 Frame[{idx}] src: {src}")
        if 'cdn-cgi' in src:
            captcha_frame = p.get_frame(f"@src='{src}'")
            break

    if captcha_frame:
        print("✅ CAPTCHA iframe found. Attempting to click checkbox...")
        checkbox = captcha_frame(".mark")
        if checkbox:
            sleep(2)
            checkbox.click()
            print("🟢 CAPTCHA checkbox clicked.")
        else:
            print("❌ CAPTCHA checkbox (.mark) not found inside iframe.")
            p.get_screenshot(path='captcha_no_checkbox.png')
            print("📸 Saved get_screenshot as captcha_no_checkbox.png")
            return
    else:
        print("❌ CAPTCHA iframe not found.")
        p.get_screenshot(path='captcha_iframe_not_found.png')
        print("📸 Saved get_screenshot as captcha_iframe_not_found.png")
        return

    sleep(10)  # Let Cloudflare validate

    # === Registration logic ===
    print("✍️ Filling out registration form...")

    name_input = p.ele('@name=FirstName')
    if name_input:
        name_input.input('John')
        print("✅ First name filled.")
    else:
        print("❌ First name input not found.")
        p.get_screenshot(path='form_input_not_found.png')
        print("📸 Saved screenshot as form_input_not_found.png")
        return

    # Continue form filling here
    # Example:
    # p.ele('@name=LastName').input('Doe')
    # p.ele('@name=Email').input('john@example.com')

    sleep(10)
    print("✅ Registration flow completed.")


# Run the function directly for testing
if __name__ == "__main__":
    bypass_and_register()
