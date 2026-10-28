# Inventário da revisão visual

## Elenco ativo fornecido pelo usuário

| GLB | Triângulos | Ossos | Clipes |
|---|---:|---:|---:|
| pam_usuario_rig | 49.970 | 22 | 12 |
| npc_januri_rig | 50.004 | 25 | 11 |
| npc_inimigo_rig | 50.000 | 32 | 11 |
| npc_lar_rig | 50.000 | 30 | 11 |

Os quatro usam os modelos recebidos. Os novos NPCs mantêm texturas PBR 4K e têm fontes editáveis em `assets/source/npcs/`. [Rigs e verificação](NPCS_USUARIO.md). As entradas `jaburanga`, `guardian`, `guardian_scout` e `assassin` na tabela histórica abaixo representam os modelos anteriores, que já não são instanciados pelo elenco ativo. O ambiente continua usando os assets de apoio abaixo.

## Inventário histórico e ambiente

Malhas e texturas originais geradas localmente. Contagens obtidas diretamente dos GLB exportados; não incluem instâncias da fase.

| Asset | Triângulos | Bytes |
|---|---:|---:|
| amulet | 492 | 48784 |
| assassin | 1696 | 194876 |
| bridge_board | 124 | 142280 |
| bridge_rails | 416 | 95888 |
| broadleaf | 360 | 131612 |
| bromeliad | 300 | 28496 |
| crate | 1236 | 290892 |
| fern | 868 | 117536 |
| gate | 668 | 192944 |
| guardian | 1794 | 385500 |
| guardian_scout | 1709 | 260344 |
| jaburanga | 2230 | 572596 |
| leaf_litter | 60 | 119920 |
| pam | 1825 | 199436 |
| raft | 436 | 171492 |
| rock | 140 | 130584 |
| root | 172 | 78448 |
| ruin_lintel | 618 | 237944 |
| ruin_pillar | 420 | 224240 |
| seed | 150 | 17648 |
| shrine | 414 | 160660 |
| thicket | 576 | 95732 |
| tnt | 1300 | 367784 |
| tree0 | 1672 | 334532 |
| tree1 | 1672 | 334528 |
| tree2 | 540 | 225696 |

## Estudos separados da fase

| Asset | Triângulos | Bytes | Estado |
|---|---:|---:|---|
| pam_ps1_estudo | 715 | 65184 | Revisão 04, pivôs rígidos históricos |
| pam_ps1_rig | 1099 | 152712 | Revisão 05: 22 ossos, skin e 5 clipes |
| pam_ps1_cartoon | 1131 | 295976 | Revisão 06: 22 ossos, 9 clipes e piscada, em avaliação |
| pam_usuario_sem_rabo | 49970 | 27833748 | Modelo do usuário: T-pose, reparação localizada |
| pam_usuario_rig | 49970 | 28790812 | Modelo do usuário: 22 ossos, 9 clipes |

A base atual é o [modelo fornecido pelo usuário](MODELO_USUARIO.md). Os estudos anteriores permanecem no histórico: [CARTOON_PAM.md](CARTOON_PAM.md) e [RIG_PAM.md](RIG_PAM.md).
