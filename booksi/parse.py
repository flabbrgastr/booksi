"""HTML parsing — extract gal data from category pages."""

import os
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

from booksi.config import load_categories

# Price extraction patterns (ordered by specificity)
_PRICE_PATTERNS = [
    # "15 Minuten 40 € / 30 Minuten 60 € / 60 Minuten 100 €" — extract hourly
    r'(\d+)\s*(?:€|Euro)\s*/\s*(?:Std\.?|Stunde|h|hour)',
    r'(?:Std\.?|Stunde|h|hour|1\s*h)\s*(?:pro|nur)?\s*(\d+)\s*(?:€|Euro)',
    # "100€ / Stunde"
    r'(\d+)\s*(?:€|Euro)\s*/\s*(?:Std\.?|Stunde|h)',
    # "Stunde nur 100€", "STUNDE 100€"
    r'Stunde\s*(?:nur)?\s*(\d+)\s*(?:€|Euro)',
    # "1h 100€"
    r'1\s*h[a-z]*[\s:]+\d+\s*€',
    # "200 € 1 Std."
    r'(\d+)\s*(?:€|Euro)\s+\d+\s*(?:Std\.?|Stunde|h)',
    # fallback: extract any number+€ that seems hourly
    r'(\d+)\s*(?:€|Euro)',
]


def extract_price(text):
    """Extract a price string from a gal's short description.

    Returns the highest price found (e.g. '100€' from '40€ / 60€ / 100€').
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    prices = []
    for pattern in _PRICE_PATTERNS:
        for m in re.finditer(pattern, text):
            val = m.group(1) if m.lastindex else m.group(0)
            try:
                prices.append(int(val))
            except ValueError:
                pass
    if prices:
        return f"{max(prices)}€"
    return ""


def ex_names(dir_path):
    """Extract base names from HTML files in dir (e.g., 'vivien' from 'vivien1.html')."""
    pattern = r"^(.*?)\d+\.html$"
    filenames = []
    for filename in os.listdir(dir_path):
        if filename.endswith(".html"):
            match = re.match(pattern, filename)
            if match:
                filenames.append(match.group(1))
    filenames.sort()
    return list(dict.fromkeys(filenames))


def cat_files(dir_path, name, remove=True):
    """Concatenate all HTML files for a base name into one."""
    concatenated_files = 0
    concatenated_content = ""
    files = os.listdir(dir_path)
    num_items = len([f for f in files if f.startswith(name)])
    progress_bar = tqdm(
        total=num_items, desc="   ✓ " + name, bar_format="{l_bar}", ncols=80
    )
    for filename in files:
        if filename.startswith(name):
            file_path = os.path.join(dir_path, filename)
            with open(file_path, "r") as file:
                content = file.read()
                sgirls = BeautifulSoup(content, "html.parser")
                girls = sgirls.find_all(
                    "div", {"class": "girl-list-item", "data-type": "listing"}
                )
                progress_bar.update(1)
                for girl in girls:
                    concatenated_content += str(girl)
            if remove:
                os.remove(file_path)
            concatenated_files += 1
    output_file_path = os.path.join(dir_path, f"{name}.html")
    with open(output_file_path, "w") as output_file:
        output_file.write(concatenated_content)
    progress_bar.close()
    return concatenated_files


def _get_category_flags(category_name):
    """Look up flags for a category from gals.conf."""
    categories = load_categories()
    base = os.path.splitext(category_name)[0]
    for cat in categories:
        if cat["name"] == base:
            return cat["flags"]
    return {"a1": False, "a0": False, "cim": False, "cof": False}


def get_gals(dir_path, category, test=False):
    """Parse a category HTML file and return list of gal dicts."""
    f = category
    fh = _check_file_exists(os.path.join(dir_path, f))
    if not fh:
        raise FileNotFoundError(f"Category file not found: {f}")

    flags = _get_category_flags(category)
    a1 = "✓" if flags["a1"] else ""
    a0 = "✓" if flags["a0"] else ""
    cim = "✓" if flags["cim"] else ""
    cof = "✓" if flags["cof"] else ""

    page_soup = BeautifulSoup(fh, "html.parser")
    girls = page_soup.findAll(
        "div", {"class": "girl-list-item", "data-type": "listing"}
    )
    noofgals = len(girls)
    descstr = "   ✓ " + f + ": " + str(noofgals)
    progress_bar = tqdm(total=noofgals, desc=descstr, bar_format="{l_bar}", ncols=80)

    results = []
    for girl in girls:
        progress_bar.update(1)
        results.append(_parse_girl(girl, a1, a0, cim, cof))
    progress_bar.close()
    return results


def _check_file_exists(filename):
    try:
        return open(filename, "r")
    except FileNotFoundError:
        print(f"The file {filename} does not exist!")
        return None


def _parse_girl(girl, a1, a0, cim, cof):
    girl_name = girl.find("h4").get_text(strip=True)

    location = girl.find("div", class_="g-location")
    hrefs = location.find_all("a") if location else []

    stadt = bezirk = strasse = ""
    if len(hrefs) > 0:
        stadt = hrefs[0].get_text()
    if len(hrefs) > 1:
        bezirk = hrefs[1].get_text()
    if len(hrefs) > 2:
        strasse = hrefs[2].get_text()

    try:
        fancount = girl.select_one("span[id*=girl-fancount]").text
    except Exception:
        fancount = 0

    try:
        score = girl.find("div", class_="girl-score").text
    except Exception:
        score = ""

    try:
        short_str = girl.find("div", class_="girl-subtitle")
        short = short_str.get_text(strip=True, separator=" ")
        short = short[short.index(" ") + 1:]
    except Exception:
        short = ""

    try:
        tel = girl.find("a", {"class": "pull-right"})["href"]
    except Exception:
        tel = "-"

    try:
        gurl = girl.find("h4").find("a")["href"]
    except Exception:
        gurl = ""

    try:
        purl = girl.find("source", srcset=True)["srcset"]
    except Exception:
        purl = None

    try:
        sid = girl["data-id"]
        gid = girl["class"][2].split("-")[1]
    except Exception:
        sid = None
        gid = None

    return {
        "Girl": girl_name,
        "Stadt": stadt,
        "Bezirk": bezirk,
        "Strasse": strasse,
        "Fans": fancount,
        "Score": score,
        "Short": short,
        "Preis": extract_price(short),
        "Tel": tel,
        "Gurl": gurl,
        "Purl": purl,
        "a1": a1,
        "a0": a0,
        "cim": cim,
        "cof": cof,
        "sid": sid,
        "gid": gid,
        "t": "",
    }