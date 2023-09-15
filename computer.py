from ctypes import c_int16
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(init=False)
class Command:
    name: str
    arg: int | None

    def __init__(self, init_string: str):
        if init_string == "":
            self.name = ""
            self.arg = None
            return
        parts = init_string.split()
        self.name = parts[0]
        if len(parts) > 1:
            if parts[1].isdecimal():
                self.arg = int(parts[1])
            else:
                self.arg = 0
        else:
            self.arg = None

    def is_input(self):
        return (self.name == "LA" or self.name == "LB") and self.arg // 32

    def repr(self):
        if self.arg is not None:
            return f"{self.name} {self.arg}"
        return self.name


@dataclass
class State:
    program_data: Sequence[Command]
    instruction_pointer: int = 0
    clock_cycle: int = 0
    _a = c_int16(0)
    _b = c_int16(0)
    cache_slots: Sequence[np.int16] = np.zeros(32, np.int16)
    ram: Sequence[np.int16] = np.zeros(1024, np.int16)
    loaded_bank: Sequence[np.int16] = np.zeros(16, np.int16)
    loaded_bank_index: int = 0
    running: bool = True
    inputs: Sequence[np.int16] = np.zeros(8, np.int16)

    @property
    def a(self) -> int:
        return self._a.value

    @a.setter
    def a(self, value: int):
        self._a.value = value

    @property
    def b(self) -> int:
        return self._b.value

    @b.setter
    def b(self, value: int):
        self._b.value = value


NON_COMMAND = Command("NON")


class Computer:
    def __init__(self, program_data: str):
        program = [Command(line) for line in program_data.split("\n")]
        self.state = State(program)
        self.output: Sequence[tuple[int, int]] = []

    def step(self):
        command = self.state.program_data[self.state.instruction_pointer]
        self.state.instruction_pointer += 1
        self.execute(command)
        self.state.clock_cycle += 1
        if self.state.instruction_pointer >= len(self.state.program_data):
            self.state.running = False
            return NON_COMMAND
        return self.state.program_data[self.state.instruction_pointer]

    def execute(self, command: Command):
        if command.is_input():
            if command.name == "LA":
                self.state.a = self.state.inputs[command.arg % 32]
            else:
                self.state.b = self.state.inputs[command.arg % 32]
            return
        match command.name:
            case "LA":
                self.state.a = self.state.cache_slots[command.arg]
            case "LB":
                self.state.b = self.state.cache_slots[command.arg]
            case "LAL":
                self.state.a = command.arg & 255
            case "LAH":
                self.state.a = self.state.a | (command.arg << 8)
            case "LBL":
                self.state.b = command.arg & 255
            case "LBH":
                self.state.b = self.state.b | (command.arg << 8)

            case "SVA":
                if command.arg >> 5:
                    print(self.state.a)
                    self.output.append((command.arg % 32, self.state.a))
                else:
                    self.state.cache_slots[command.arg] = self.state.a

            case "STP":
                self.state.running = False

            case "ADD":
                self.state.a += self.state.b
            case "SUB":
                self.state.a -= self.state.b
            case "AND":
                self.state.a &= self.state.b
            case "OR":
                self.state.a |= self.state.b
            case "XOR":
                self.state.a ^= self.state.b

            case "SUP":
                self.state.a <<= 1
            case "SDN":
                self.state.a >>= 1
            case "MUL":
                self.state.a *= self.state.b
            case "INB":
                self.state.b += 1

            case "RW":
                self.state.loaded_bank[self.state.b % 16] = self.state.a
            case "RR":
                self.state.a = self.state.loaded_bank[self.state.b % 16]
            case "RC":
                bank = (self.state.b // 16) % 64
                if bank != self.state.loaded_bank_index:
                    self.state.ram[
                    self.state.loaded_bank_index * 16:(self.state.loaded_bank_index + 1) * 16] = self.state.loaded_bank
                    self.state.loaded_bank = self.state.ram[bank * 16:(bank + 1) * 16]
                    self.state.loaded_bank_index = bank

            case "JMP":
                self.state.instruction_pointer = command.arg
            case "JE":
                if self.state.a == self.state.b:
                    self.state.instruction_pointer = command.arg
            case "JNE":
                if self.state.a != self.state.b:
                    self.state.instruction_pointer = command.arg
            case "JG":
                if self.state.a > self.state.b:
                    self.state.instruction_pointer = command.arg
            case "JL":
                if self.state.a < self.state.b:
                    self.state.instruction_pointer = command.arg
            case "JGE":
                if self.state.a >= self.state.b:
                    self.state.instruction_pointer = command.arg
            case "JLE":
                if self.state.a <= self.state.b:
                    self.state.instruction_pointer = command.arg
