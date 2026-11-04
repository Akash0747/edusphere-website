"""Headless smoke test + screenshots. Requires playwright (installed to /tmp/pw)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950}, device_scale_factor=1)
    page.on("pageerror", lambda e: errors.append("PAGEERROR: " + str(e)))
    page.on("console", lambda m: errors.append("CONSOLE: " + m.text) if m.type == "error" else None)
    page.goto("file://" + str(ROOT / "index.html"))
    page.wait_for_timeout(700)

    def shot(name, full=False):
        page.screenshot(path=str(SHOTS / (name + ".jpg")), type="jpeg", quality=82, full_page=full)
        print("shot:", name)

    print("title:", page.title())
    print("hero count:", page.locator("#heroCount").inner_text())
    print("ticker items:", page.locator(".ticker__item").count())
    print("home exam cards:", page.locator("#homeExams .exam-card").count())
    print("featured cards:", page.locator("#featuredPapers .paper-card").count())
    shot("01-home", full=True)

    # Exams view
    page.locator('[data-nav="exams"]').click()
    page.wait_for_timeout(400)
    print("exam shelf cards:", page.locator("#examShelf .exam-card").count())
    shot("02-exams", full=True)

    # Papers view
    page.locator('[data-nav="papers"]').click()
    page.wait_for_timeout(400)
    print("results:", page.locator("#resultsCount").inner_text())
    print("paper cards page1:", page.locator("#paperGrid .paper-card").count())
    print("pager buttons:", page.locator("#pager button").count())
    shot("03-papers", full=True)

    # Filter by exam chip
    page.locator('[data-chip="jee-advanced"]').click()
    page.wait_for_timeout(250)
    print("JEE Adv filtered:", page.locator("#resultsCount").inner_text())
    print("active filter:", page.locator("#activeFilterText").inner_text())

    # Open a drawer
    page.locator("#paperGrid .paper-card [data-open]").first.click()
    page.wait_for_timeout(400)
    print("drawer title:", page.locator("#drawerTitle").inner_text())
    print("drawer meta cells:", page.locator("#drawerPanel .meta-grid div").count())
    shot("04-drawer")
    page.locator("[data-drawer-close]").click()
    page.wait_for_timeout(250)

    # Search
    page.locator("#searchInput").fill("Physics")
    page.wait_for_timeout(400)
    print("search results:", page.locator("#resultsCount").inner_text())
    page.locator("#searchInput").fill("")
    page.wait_for_timeout(300)

    # Save a paper, then check dashboard
    page.locator("#paperGrid .paper-card [data-save]").first.click()
    page.wait_for_timeout(200)
    page.locator('[data-nav="dashboard"]').click()
    page.wait_for_timeout(350)
    print("saved stat:", page.locator("#dashStats .dash-stat").nth(1).inner_text().replace("\n", " "))
    shot("05-dashboard", full=True)

    # Practice
    page.locator('[data-nav="practice"]').click()
    page.wait_for_timeout(350)
    print("quiz options:", page.locator("#quizCard .option").count())
    page.locator("#quizCard .option").first.click()
    page.wait_for_timeout(250)
    print("explanation visible:", page.locator("#quizCard .explanation").count())
    shot("06-practice", full=True)

    # Connect
    page.locator('[data-nav="connect"]').click()
    page.wait_for_timeout(350)
    print("db table rows:", page.locator("#dbTable tbody tr").count())
    shot("07-connect", full=True)

    # Mobile
    m = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    m.on("pageerror", lambda e: errors.append("MOBILE PAGEERROR: " + str(e)))
    m.goto("file://" + str(ROOT / "index.html"))
    m.wait_for_timeout(600)
    m.screenshot(path=str(SHOTS / "08-mobile-home.jpg"), type="jpeg", quality=82, full_page=True)
    m.locator("#menuToggle").click()
    m.wait_for_timeout(200)
    m.locator('[data-nav="papers"]').click()
    m.wait_for_timeout(400)
    m.screenshot(path=str(SHOTS / "09-mobile-papers.jpg"), type="jpeg", quality=82, full_page=True)
    print("mobile paper cards:", m.locator("#paperGrid .paper-card").count())
    browser.close()

print("\nERRORS:", len(errors))
for e in errors[:20]:
    print(" ", e)
