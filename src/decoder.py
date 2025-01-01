import base64


def b64padanddecode(b) -> str:
    b += (-len(b) % 4) * "="
    return base64.b64decode(b, altchars="+,", validate=True).decode("utf-16-be")


def imaputf7decode(s):
    lst = s.split("&")
    out = lst[0]
    for e in lst[1:]:
        u, a = e.split("-", 1)
        if u == "":
            out += "&"
        else:
            out += b64padanddecode(u)
        out += a
    return out


def imaputf7encode(s) -> str:
    s = s.replace("&", "&-")
    unipart = out = ""
    for c in s:
        if 0x20 <= ord(c) <= 0x7F:
            if unipart != "":
                out += (
                    "&"
                    + base64.b64encode(unipart.encode("utf-16-be"))
                    .decode("ascii")
                    .rstrip("=")
                    + "-"
                )
                unipart = ""
            out += c
        else:
            unipart += c
    if unipart != "":
        out += (
            "&"
            + base64.b64encode(unipart.encode("utf-16-be")).decode("ascii").rstrip("=")
            + "-"
        )
    return out
