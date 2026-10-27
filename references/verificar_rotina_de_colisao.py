#!/usr/bin/env python3
"""Verifica o encadeamento entre física, subdivisão de deslocamento e checagem de colisão.
Usa o main.cs local fornecido pelo usuário; NÃO executa código do jogo nem é um motor.
"""
from pathlib import Path
import argparse
import csv


def contagem_subpassos(dx: int, dy: int, dz: int) -> int:
    """Modelo algébrico do cálculo em func_8002C184 para deslocamentos inteiros.

    Não simula truncamentos de 32 bits com overflow ou ramificações de colisão.
    """
    return max(abs(dx) // 25600, abs(dy) // 153600, abs(dz) // 25600) + 1


def check_main(src):
    tests = {
        'entrada da física func_8001F30C': 'func_8001F30C_Impl(c, m);',
        'integração / flag de colisão': 'CrashBandicoot.func_8002BE8C(c, m);',
        'deslocamento subdividido': 'public static void func_8002C184(CpuContext c, IMemory m)',
        'colisão por subpasso': 'CrashBandicoot.func_8002D384(c, m);',
        'gravidade flag 0x20': 'c.V0 = c.V0 & 0x0020u;',
        'limite de queda': 'c.A0 = c.A0 | 0x2000u;',
    }
    return {k: v in src for k, v in tests.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--main', default='/mnt/data/crash_engine_sources/main.cs')
    ap.add_argument('--out', default='exemplos_subpassos.csv')
    args = ap.parse_args()
    source = Path(args.main).read_text(encoding='utf-8')
    status = check_main(source)
    for label, passed in status.items():
        print(('OK  ' if passed else 'ERRO') + label)
    if not all(status.values()):
        raise SystemExit('Uma evidência não foi encontrada no arquivo atual')
    samples = [
        ('zero',0,0,0),
        ('horizontal pequeno',10000,0,0),
        ('horizontal no limite',25600,0,0),
        ('horizontal 1 Q16.16',65536,0,0),
        ('vertical 1 Q16.16',0,65536,0),
        ('vertical no limite',0,153600,0),
        ('diagonal',65536,65536,65536),
        ('vertical 3 Q16.16',0,3*65536,0),
    ]
    with Path(args.out).open('w', newline='', encoding='utf-8-sig') as f:
        writer=csv.writer(f)
        writer.writerow(['exemplo','dx_int','dy_int','dz_int','subpassos_esperados'])
        for label,dx,dy,dz in samples:
            writer.writerow([label,dx,dy,dz,contagem_subpassos(dx,dy,dz)])
    assert contagem_subpassos(0,0,0) == 1
    assert contagem_subpassos(25600,0,0) == 2
    assert contagem_subpassos(0,153600,0) == 2
    assert contagem_subpassos(65536,65536,65536) == 3
    print('Testes de subpassos: OK')

if __name__ == '__main__':
    main()
