from DrissionPage import ChromiumOptions, ChromiumPage

def create_page_with_proxy(proxy: str = None) -> ChromiumPage:
    co = ChromiumOptions()

    if proxy:
        co.set_argument('--proxy-server=' + proxy)

    # Stronger fingerprint + GUI mode for debugging
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    co.headless(False)

    return ChromiumPage(co)
