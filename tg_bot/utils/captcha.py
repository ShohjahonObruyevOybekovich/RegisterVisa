from time import sleep

from DrissionPage import ChromiumPage

p = ChromiumPage()
p.get("https://nowsecure.nl/")

i=p.get_frame("@src^https://challenges.cloudflare.com/cdn-cgi/")
e=i(".mark")
sleep(3)
e.click()