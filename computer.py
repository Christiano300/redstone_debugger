from dataclasses import dataclass
from typing import Sequence
import numpy as np
from ctypes import c_int16

@dataclass(init=False)
class Command:
    name: str
    arg: int

    def __init__(self, init_string: str):
        if init_string == "":
            self.name = ""
            self.arg = None
            return
        parts = init_string.split()
        self.name = parts[0]
        if len(parts) > 1:
            self.arg = int(parts[1])
        else:
            self.arg = None

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
    loaded_bank_index: int = -1
    running: bool = True
    
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

    def execute(self, command: Command):
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
                self.state.b = self.state.a | (command.arg << 8)
                
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

            case "RW":
                pass
            case "RR":
                pass
            case "RC":
                pass

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
            
            

