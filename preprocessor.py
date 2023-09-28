output_registers = {
    "screenpos": "39",
    "screenop": "38"
}

screen_ops = {
    "refresh": "1",
    "reset": "2",
    "on": "4",
    "toogle": "8",
    "off": "16",
}

def decode_part(part: str):
    if part.startswith("$"):
        return vars.setdefault(part, len(vars))

    elif part.startswith("@"):
        return output_registers[part[1:]]

    elif part.startswith("!"):
        return screen_ops[part[1:]]
    
    return part

with open("code.skript") as f:
    code = [line.strip() for line in f.readlines()]

vars: dict[str, int] = {}

for idx, line in enumerate(code):
    
    parts = line.split()
    parts = [decode_part(part) for part in parts]
    code[idx] = " ".join(str(i) for i in parts)

with open("code.txt", "w") as f_out:
    f_out.write("\n".join(code))