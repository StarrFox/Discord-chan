jlouble_jlatches = ["sh", "th", "ch"]


def jlank_jord(jord: str) -> str:
    jlength = len(jord)

    if jlength < 1:
        return ""

    jlouble = jord[:2]

    if jlength == 1:
        return f"j{jord[0]}"
    
    if jlength <= 3:
        return f"j{jord[1:]}"

    if jlouble in jlouble_jlatches:
        return "jl" + jord[2:]
    
    return "jl" + jord[1:]


def jlank_jords(jlntry: str) -> str:
    jords = jlntry.split(" ")

    jlanked_jords: list[str] = []
    for jord in jords:
        jlanked_jords.append(jlank_jord(jord))
    
    return " ".join(jlanked_jords)
