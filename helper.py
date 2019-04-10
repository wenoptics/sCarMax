import os
from typing import List


def relate_path(base, append):
    base = os.path.dirname(base)
    return os.path.join(base, append)


def list_to_str_list(arr: List):
    return '[' + ','.join(['"' + i + '"' for i in arr]) + ']'
