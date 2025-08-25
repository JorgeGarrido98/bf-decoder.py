#!/usr/bin/env python3
"""
Uso:
  # Desde archivo:
  python3 bf_tool.py -f programa.bf

  # Pegando el comentario HTML directamente:
  python3 bf_tool.py -p "<!--++++++>>-.>+.-->"

  # Con entrada para ',':
  python3 bf_tool.py -p ",[.,]" -i "hello"

  # Ajustar límites:
  python3 bf_tool.py -p "+++[>+++<-]." --tape-size 65536 --max-steps 5000000
"""

from __future__ import annotations
import argparse
import sys
from typing import Dict, List

BF_CHARS = set("+-<>[],.")

def sanitize(program: str) -> str:
    """Conserva solo tokens válidos de Brainfuck (puedes pegar HTML/ruido)."""
    return "".join(c for c in program if c in BF_CHARS)

def build_bracket_map(program: str) -> Dict[int, int]:
    """Precalcula pares de corchetes para saltos rápidos."""
    stack: List[int] = []
    bracket_map: Dict[int, int] = {}
    for pos, ch in enumerate(program):
        if ch == '[':
            stack.append(pos)
        elif ch == ']':
            if not stack:
                raise SyntaxError(f"Unmatched ']' en posición {pos}")
            start = stack.pop()
            bracket_map[start] = pos
            bracket_map[pos] = start
    if stack:
        raise SyntaxError(f"Unmatched '[' en posición {stack[-1]}")
    return bracket_map

class BrainfuckInterpreter:
    def __init__(self, tape_size: int = 30000, max_steps: int = 2_000_000):
        if tape_size <= 0:
            raise ValueError("tape_size debe ser > 0")
        self.tape = [0] * tape_size
        self.ptr = 0
        self.max_steps = max_steps

    def run(self, program: str, inbuf: str = "") -> str:
        program = sanitize(program)
        bracket_map = build_bracket_map(program)
        ip = 0  # instruction pointer
        steps = 0
        out_chars: List[str] = []

        in_idx = 0
        tape_len = len(self.tape)
        
        while ip < len(program):
            if steps >= self.max_steps:
                raise RuntimeError(
                    f"Max steps superado ({self.max_steps}). "
                    "Puede haber un bucle infinito. Usa --max-steps para ampliar."
                )
            steps += 1

            cmd = program[ip]
            if cmd == '>':
                self.ptr += 1
                if self.ptr >= tape_len:
                    self.ptr = 0  # wrap-around
            elif cmd == '<':
                self.ptr -= 1
                if self.ptr < 0:
                    self.ptr = tape_len - 1  # wrap-around
            elif cmd == '+':
                self.tape[self.ptr] = (self.tape[self.ptr] + 1) % 256
            elif cmd == '-':
                self.tape[self.ptr] = (self.tape[self.ptr] - 1) % 256
            elif cmd == '.':
                out_chars.append(chr(self.tape[self.ptr]))
            elif cmd == ',':
                if in_idx < len(inbuf):
                    self.tape[self.ptr] = ord(inbuf[in_idx])
                    in_idx += 1
                else:
                    self.tape[self.ptr] = 0
            elif cmd == '[':
                if self.tape[self.ptr] == 0:
                    ip = bracket_map[ip]  # salta a ']'
            elif cmd == ']':
                if self.tape[self.ptr] != 0:
                    ip = bracket_map[ip]  # vuelve a '['
            ip += 1

        return "".join(out_chars)

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Intérprete/decoder de Brainfuck.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("-f", "--file", help="Ruta a archivo Brainfuck.")
    src.add_argument("-p", "--program", help="Programa Brainfuck como string (se puede pegar HTML/ruido).")
    parser.add_argument("-i", "--input", default="", help="Entrada para instrucciones ','.")
    parser.add_argument("--tape-size", type=int, default=30000, help="Tamaño de cinta (por defecto 30000).")
    parser.add_argument("--max-steps", type=int, default=2_000_000, help="Límite de pasos para seguridad.")
    parser.add_argument("--no-sanitize", action="store_true", help="No limpiar caracteres no-BF.")
    args = parser.parse_args(argv)

    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            program = fh.read()
    else:
        program = args.program or ""

    if not args.no_sanitize:
        program = sanitize(program)
    
    try:
        interp = BrainfuckInterpreter(tape_size=args.tape_size, max_steps=args.max_steps)
        output = interp.run(program, inbuf=args.input)
        sys.stdout.write(output)
        return 0
    except (SyntaxError, RuntimeError, ValueError) as e:
        sys.stderr.write(f"[bf_tool] Error: {e}\n")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())