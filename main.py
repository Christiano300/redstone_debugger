import json
import pygame

from computer import Computer, Command
pygame.init()

size = width, height = 1080, 720
screen = pygame.display.set_mode(size, pygame.RESIZABLE)
clock = pygame.time.Clock()
FPS = 60

pygame.key.set_repeat(750, 33)

font_code = pygame.font.SysFont("Consolas", 20)
font_code_bold = pygame.font.SysFont("Consolas", 20, True)

font_line = pygame.font.SysFont("Consolas", 18)
icon = pygame.image.load("redstone.png").convert_alpha()
pygame.display.set_icon(icon)
pygame.display.set_caption("Redstone Debugger")

edit_mode = False
selected_command_idx = 0
selected_command = ""

with open("theme.json") as f:
    theme = json.load(f)

with open("code.txt") as f:
    computer = Computer(f.read())

auto_running = False
commands_per_second = 25
auto_max_cooldown = FPS / commands_per_second
auto_cooldown = auto_max_cooldown


def text(text, pos, color=0xffffffff, bold=False, font=None):
    if font is None:
        font = font_code_bold if bold else font_code
    screen.blit(font.render(text, True, color), pos)


def draw_value(value, label, pos):
    text(label, pos, 0x9f9f9fff, True)
    text(f"{value}",
         (pos[0] + font_code_bold.size(label)[0], pos[1]), 0xf0f0f0ff)


def draw_command(command: Command, pos: tuple[int, int]):
    command_color = theme["commands"].get(
        command.name, {"type": "unknown", "arg": "unknown"})
    text(command.name, pos, theme["colors"][command_color["type"]])
    if command.arg is not None:
        text(f" {command.arg}", (pos[0] + font_code.size(command.name)[0], pos[1]),
             theme["colors"][command_color["arg"]])


def draw_program():
    col_width = font_code_bold.size("LAL -128")[0] + 10
    row_height = font_code_bold.size("LAL -128")[1]

    hofs = 10
    vofs = 10 + row_height
    pad = 2
    linenumpad = font_code_bold.size("63")[0] + 6

    text("Program:", (hofs, vofs - row_height), 0xffffffff, True)

    for i in range(64):
        text(str(i), (hofs + pad * 2 + i // 32 * (col_width + linenumpad + pad),
                      vofs + pad + i % 32 * row_height),
             0x707070ff, font=font_line)

    for i, command in enumerate(computer.state.program_data):
        text_x = hofs + pad * 2 + linenumpad + \
            i // 32 * (col_width + linenumpad + pad)
        text_y = vofs + pad + i % 32 * row_height
        if edit_mode:
            if i == selected_command_idx:
                pygame.draw.rect(screen, 0x070707,
                                 (text_x, text_y, col_width - pad, row_height))

                pygame.draw.rect(screen, 0xf0f0f0,
                                 (text_x, text_y, col_width - pad, row_height), 1)
                cursor_ofs = font_code.size(selected_command)[0]
                pygame.draw.line(screen, 0xf0f0f0,
                                 (text_x + cursor_ofs, text_y + 2),
                                 (text_x + cursor_ofs, text_y + row_height - 2), 2)
        else:
            if computer.state.running and i == computer.state.instruction_pointer:
                pygame.draw.rect(screen, 0x404040,
                                 (text_x, text_y, col_width - pad, row_height))

        draw_command(command, (text_x, text_y))

    # outline
    pygame.draw.rect(screen, 0xd0e0e0,
                     (hofs, vofs, col_width * 2 + pad * 2 +
                      linenumpad * 2, row_height * 32 + pad),
                     2, 2)
    # splitter
    splitter_x = hofs + pad + col_width + linenumpad
    pygame.draw.line(screen, 0xd0e0e0,
                     (splitter_x, vofs), (splitter_x, vofs + row_height * 32), 1)

    if not computer.state.running:
        text("Program stopped", (hofs, vofs + pad *
             2 + row_height * 32), 0xf07676ff, True)


def draw_cache():
    col_width = font_code_bold.size("-32762")[0] + 10
    row_height = font_code_bold.size("-32762")[1]

    hofs = 290
    vofs = 10 + row_height
    pad = 2
    linenumpad = font_code_bold.size("63")[0] + 6

    text("Cache:", (hofs, vofs - row_height), 0xffffffff, True)

    for i in range(32):
        text(str(i),
             (hofs + pad * 2 + i // 16 * (col_width + linenumpad + pad),
              vofs + pad + i % 16 * row_height),
             0x707070ff, font=font_line)

    for i, slot in enumerate(computer.state.cache_slots):
        text_x = hofs + pad * 2 + linenumpad + \
            i // 16 * (col_width + linenumpad + pad)
        text_y = vofs + pad + i % 16 * row_height

        text(str(slot), (text_x, text_y))

    # outline
    pygame.draw.rect(screen, 0xd0e0e0,
                     (hofs, vofs,
                      col_width * 2 + pad * 2 + linenumpad * 2, row_height * 16 + pad),
                     2, 2)
    # splitter
    splitter_x = hofs + pad + col_width + linenumpad
    pygame.draw.line(screen, 0xd0e0e0,
                     (splitter_x, vofs), (splitter_x, vofs + row_height * 16), 1)


def draw_info():
    line_height = font_code_bold.size("A: ")[1]
    hofs = 290
    vofs = 10 + line_height * 18

    draw_value(computer.state.a, "A: ", (hofs, vofs))
    draw_value(computer.state.b, "B: ", (hofs, vofs + line_height))
    draw_value(computer.state.clock_cycle, "Clock Cycle: ",
               (hofs, vofs + line_height * 2))
    draw_value(computer.state.instruction_pointer,
               "Instruction: ", (hofs, vofs + line_height * 3))


def draw_output():
    line_height = font_code_bold.size("0")[1]
    col_width = font_code_bold.size("0: -32768")[0] + 10

    hofs = 290
    vofs = 10 + line_height * 24
    pad = 3

    text("Output:", (hofs, vofs - line_height), 0xffffffff, True)
    for i in range(1, 10):
        if i > len(computer.output):
            break
        value = computer.output[-i]
        draw_value(str(value[1]), f"{value[0]}: ",
                   (hofs + pad, vofs + pad + line_height * (i - 1)))

    # outline
    pygame.draw.rect(screen, 0xd0e0e0,
                     (hofs, vofs,
                      col_width + pad * 2, line_height * 9 + pad),
                     2, 2)

def draw_ram():
    col_width = font_code_bold.size("-32762")[0] + 10
    row_height = font_code_bold.size("-32762")[1]

    hofs = 530
    vofs = 10 + row_height
    pad = 2
    linenumpad = font_code_bold.size("63")[0] + 6

    text(f"Loaded Bank: {computer.state.loaded_bank_index}", (hofs, vofs - row_height), 0xffffffff, True)

    for i in range(16):
        text(str(i),
             (hofs + pad * 2 + i // 16 * (col_width + linenumpad + pad),
              vofs + pad + i % 16 * row_height),
             0x707070ff, font=font_line)

    for i, slot in enumerate(computer.state.loaded_bank):
        text_x = hofs + pad * 2 + linenumpad + \
            i // 16 * (col_width + linenumpad + pad)
        text_y = vofs + pad + i % 16 * row_height

        text(str(slot), (text_x, text_y))

    # outline
    pygame.draw.rect(screen, 0xd0e0e0,
                     (hofs, vofs,
                      col_width + pad * 2 + linenumpad, row_height * 16 + pad),
                     2, 2)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                edit_mode = not edit_mode
                pygame.display.set_caption(
                    "Redstone Debugger" + (" (edit mode)" if edit_mode else ""))
                if edit_mode:
                    selected_command_idx = computer.state.instruction_pointer
                    selected_command = computer.state.program_data[selected_command_idx].repr(
                    )
                    auto_running = False

            if edit_mode:
                if event.key == pygame.K_DOWN:
                    if pygame.key.get_mods() & pygame.KMOD_ALT and selected_command_idx < len(computer.state.program_data) - 1:
                        computer.state.program_data[selected_command_idx], computer.state.program_data[selected_command_idx +
                                                                                                       1] = computer.state.program_data[selected_command_idx + 1], computer.state.program_data[selected_command_idx]
                        selected_command_idx += 1
                    else:
                        selected_command_idx = min(
                            selected_command_idx + 1, len(computer.state.program_data) - 1)
                        selected_command = computer.state.program_data[selected_command_idx].repr(
                        )

                elif event.key == pygame.K_UP:
                    if pygame.key.get_mods() & pygame.KMOD_ALT and selected_command_idx > 0:
                        computer.state.program_data[selected_command_idx], computer.state.program_data[selected_command_idx -
                                                                                                       1] = computer.state.program_data[selected_command_idx - 1], computer.state.program_data[selected_command_idx]
                        selected_command_idx -= 1
                    else:
                        selected_command_idx = max(selected_command_idx - 1, 0)
                        selected_command = computer.state.program_data[selected_command_idx].repr(
                        )

                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    if (selected_command_idx + 32) % 64 < len(computer.state.program_data):
                        selected_command_idx = (selected_command_idx + 32) % 64
                        selected_command = computer.state.program_data[selected_command_idx].repr(
                        )

                elif event.key == pygame.K_BACKSPACE:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        selected_command = ""
                    elif selected_command == "" and len(computer.state.program_data) > 1:  # delete line
                        del computer.state.program_data[selected_command_idx]
                        selected_command_idx = max(selected_command_idx - 1, 0)
                        selected_command = computer.state.program_data[selected_command_idx].repr(
                        )
                    else:
                        selected_command = selected_command[:-1]
                    computer.state.program_data[selected_command_idx] = Command(
                        selected_command)

                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    with open("code.txt", "w") as f:
                        f.write("\n".join(command.repr()
                                for command in computer.state.program_data))

                elif event.key in (pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                   pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
                                   pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e,
                                   pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j,
                                   pygame.K_k, pygame.K_l, pygame.K_m, pygame.K_n, pygame.K_o,
                                   pygame.K_p, pygame.K_q, pygame.K_r, pygame.K_s, pygame.K_t,
                                   pygame.K_u, pygame.K_v, pygame.K_w, pygame.K_x, pygame.K_y,
                                   pygame.K_z, pygame.K_SPACE):

                    new = selected_command + event.unicode.upper()
                    parts = new.split()
                    if len(parts) > 1 and not parts[1].isdecimal():
                        continue
                    selected_command = new
                    computer.state.program_data[selected_command_idx] = Command(
                        selected_command)

                elif event.key == pygame.K_RETURN:
                    computer.state.program_data.insert(
                        selected_command_idx + 1, Command(""))
                    selected_command_idx += 1
                    selected_command = computer.state.program_data[selected_command_idx].repr(
                    )

                elif event.key == pygame.K_DELETE:
                    del computer.state.program_data[selected_command_idx]
                    if len(computer.state.program_data) == 0:
                        computer.state.program_data.append(Command(""))
                    elif selected_command_idx == len(computer.state.program_data):
                        selected_command_idx -= 1
                    selected_command = computer.state.program_data[selected_command_idx].repr(
                    )

            else:
                if event.key in (pygame.K_RETURN, pygame.K_DOWN, pygame.K_RIGHT):
                    if computer.state.running:
                        auto_running = False
                        computer.step()

                elif event.key == pygame.K_SPACE:
                    auto_running = not auto_running

    if auto_running and computer.state.running and not edit_mode:
        auto_cooldown -= 1
        if auto_cooldown <= 0:
            computer.step()
            auto_cooldown += auto_max_cooldown

    screen.fill(0x16161e)
    draw_program()
    draw_cache()
    draw_info()
    draw_output()
    draw_ram()

    pygame.display.update()
    clock.tick(FPS)
