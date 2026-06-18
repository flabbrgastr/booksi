"""HTML parsing — extract gal data from category pages."""

import os
import re
from bs4 import BeautifulSoup
from tqdm import tqdm


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


def get_gals(dir_path, category, test=False):
    """Parse a category HTML file and return list of gal dicts."""
    f = category
    fh = _check_file_exists(os.path.join(dir_path, f))
    if not fh:
        raise FileNotFoundError(f"Category file not found: {f}")

    a0 = a1 = cim = cof = ""
    if "analsex" in category:
        a1 = "✓"
    if "natur" in category:
        a0 = "✓"
    if "cum_in_mouth" in category:
        cim = "✓"
    if "cum_on_face" in category:
        cof = "✓"

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