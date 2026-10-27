"""Validate only the attached arithmetic, without claiming binary/ROM validation."""
from pathlib import Path
import csv, importlib.util
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dossier',root/'references/verificar_rotina_de_colisao.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with (root/'references/exemplos_subpassos.csv').open(encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))
for row in rows:
    actual=module.contagem_subpassos(*(int(row[k]) for k in ['dx_int','dy_int','dz_int']))
    assert actual==int(row['subpassos_esperados']),row['exemplo']
print(f'PASS {len(rows)} exemplos aritméticos. main.cs/ROM não fornecidos; evidência binária não testada.')
