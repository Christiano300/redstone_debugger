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
    code = [line.strip() for line in f if line.strip()]

vars: dict[str, int] = {}

code_segments: list[tuple[str, list[str]]] = []
code_segment_index = -1
jump_marks: dict[str, int] = {}

for idx, line in enumerate(code):
    parts = line.split()
    parts = [decode_part(part) for part in parts]
    line = code[idx] = " ".join(str(i) for i in parts)
    
    if line.endswith(":") and not line.startswith("#"):
        code_segments.append((line[:-1], []))
        code_segment_index += 1
    
    else:
        code_segments[code_segment_index][1].append(line)

offset = 0
for idx, (name, lines) in enumerate(code_segments):
    jump_marks[name] = offset
    offset += len(lines)

for segment in code_segments:
    for idx, line in enumerate(segment[1]):
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("->"):
            segment[1][idx] = f"{parts[0]} {jump_marks[parts[1][2:]]}"

out = []
for segment in code_segments:
    out.append("\n".join(segment[1]))

    

with open("code.txt", "w") as f_out:
    f_out.write("\n".join(out))