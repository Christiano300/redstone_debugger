with open("code.skript") as f:
    code = [line.strip() for line in f.readlines()]

vars: dict[str, int] = {}

for idx, line in enumerate(code):
    parts = line.split()
    parts = [vars.setdefault(part, len(vars)) if part.startswith("$") else part for part in parts]
    code[idx] = " ".join(str(i) for i in parts)

with open("code.txt", "w") as f_out:
    f_out.write("\n".join(code))