import os
import shutil
import sys

import pandas as pd

from booksi.parse import get_gals, cat_files, ex_names
from booksi.storage import findhtmls
from booksi.normalize import dfComprehend, someStats
from booksi.render import convert_dataframe_to_html
from booksi.storage import prune_items, getlastdir, newsidlist, update_dataframe

if "-h" in sys.argv:
    print("""
    Usage:
        python booksi.py [options]
        -h  help
        -v  verbose
        -ci csv import instead of html analysis. Faster for testing.
        -s show stats""")
    sys.exit()

# Specify the directory
dir_path = "./data"  # replace with your directory

if "-v" in sys.argv:
    verbose = True
else:
    verbose = False


# leave only one, ie the newest, zip file for each date
pruned_items = prune_items(dir_path, test_mode=False)
if pruned_items:
    print(str(pruned_items) + "   items pruned")

# get the last directory
lastdir = getlastdir(dir_path)

if lastdir is None:
    print("No data directories found in " + dir_path)
    exit(1)

# get the names of categories in the last directory
# summarize each category into a single file
names = ex_names(lastdir)
if names:
    print("html preprocessing " + lastdir)
    for name in names:
        catted = cat_files(lastdir, name, remove=True)
#        print('    '+name + ' ... ' + str(catted))
else:
    print("no files found in " + lastdir)

pdall = pd.DataFrame()

if "-ci" not in sys.argv:
    # extract gals out of each category file
    # and save them in a separate csv file
    print("⌵ getgals " + lastdir[2:])
    html_files = findhtmls(lastdir)

    for file in html_files:
        category = os.path.splitext(file)[0]

        arr = get_gals(lastdir, file)
        df = pd.DataFrame(arr)
        #   print(df.head(3))
        pdall = pd.concat([pdall, df], ignore_index=True)

    pdall = dfComprehend(pdall)

    if "-s" in sys.argv:
        someStats(pdall)

    # Create the directory if it doesn't exist
    if not os.path.exists(lastdir + "/gen/"):
        os.makedirs(lastdir + "/gen/")
    # Write DataFrame to CSV file (overwrite if exists)
    csv_file = lastdir + "/gen/" + "all.csv"
    pdall.to_csv(csv_file, index=False, mode="w")
else:
    # ingest existing csv file
    pdall = pd.read_csv(lastdir + "/gen/all.csv")
    if "-s" in sys.argv:
        someStats(pdall)

print("⌵ writing... csv and html")
print("     all.csv")

new = 0
old = 5

pdall["sid"] = pdall["sid"].astype(int)

for old in range(old, new, -1):
    new_sids = newsidlist(old, new, verbose=verbose)
    changed_sids = update_dataframe(old, new, verbose=verbose)
    print(f"     New{old} {len(new_sids)} : Upd{old} {len(changed_sids)}")
    # Update the 't' column in pdall for new and changed 'sid' values
    pdall.loc[pdall["sid"].isin(new_sids), "t"] = "new" + str(old)
    pdall.loc[pdall["sid"].isin(changed_sids), "t"] = "upd" + str(old)

# Create the HTML table
html_table = convert_dataframe_to_html(pdall)
html_file = lastdir + "/gen/" + "all.html"
with open(html_file, "w") as hfile:
    hfile.write(html_table)
shutil.copy2(lastdir + "/gen/" + "all.html", "./all.html", follow_symlinks=True)
shutil.copy2(lastdir + "/gen/" + "all.html", "/var/www/booksi/all.html", follow_symlinks=True)
print("     all.html -> ./all.html, /var/www/booksi/all.html")
# all.html is the file that is used by the webserver
exit(0)
