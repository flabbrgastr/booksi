# gallib.py — backwards-compat import shim
# All functions moved to booksi/ package modules.

from booksi.parse import (
    cat_files,
    ex_names,
    get_gals,
)
from booksi.normalize import (
    dfComprehend,
    dups,
    fancy_print,
    get_top_10_rows,
    someStats,
)
from booksi.render import convert_dataframe_to_html
from booksi.storage import (
    check_file_exists,
    count_occurrences,
    findhtmls,
    getlastdir,
    matchdir,
    newsidlist,
    prune_items,
    update_dataframe,
)
