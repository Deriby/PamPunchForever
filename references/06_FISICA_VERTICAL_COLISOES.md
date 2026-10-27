# Etapa 6 — Gravidade, movimento vertical e subdivisão de colisões

Analisado a partir de `/mnt/data/crash_engine_sources/main.cs`, proveniente do ZIP do usuário. Endereços são relativos ao executável NTSC-U do PS1 e não ao código escrito originalmente em alto nível. Não executamos a ROM nesta etapa.

## 1. Estrutura do objeto em memória [CONFIRMADO]

Para objetos do Crash 1 (verificado contra a tabela de campos da wiki Cbhacks):

| Campo relativo ao objeto | Interpretação |
|---|---|
| `+0x80`, `+0x84`, `+0x88` | posição X, Y, Z |
| `+0xA4`, `+0xA8`, `+0xAC` | velocidade X, Y, Z |
| `+0xC8` | status flags A |
| `+0xCC` | status flags B |
| `+0x11C` | altura do chão (`groundy`) |
| `+0x120` | flags do estado GOOL |
| `+0x124` | velocidade escalar de controle |
| `+0x130`, `+0x134` | informações de aterrissagem |

## 2. Física vertical em `func_8001F30C_Impl` [CONFIRMADO]

- Bit `0x40` de `statusb` (`+0xCC`) ativa a aplicação automática do deslocamento ao objeto.
- Se bit `0x08` também está ligado, o deslocamento é entregue a `func_8002BE8C`, que realiza a trajetória com tratamento de colisões. Caso contrário, X/Y/Z são incrementados diretamente.
- Bit `0x20` ativa gravidade. Mais adiante na rotina, após o bloco de integração do deslocamento, o código limita o tempo interno a `102` unidades e efetua:

```text
vely_novo = max(vely_antigo - 4000 * min(ticks_internos, 102), -3072000)
```

- A constante de limite é o inteiro com sinal `0xFFD12000` = `-3.072.000`.
- **Ordem dentro da função:** atualização de posição antes do bloco de gravidade; portanto a gravidade calculada afeta o valor de velocidade usado nas próximas atualizações dessa rotina. A sequência global de chamadas em um quadro ainda depende do game loop.
- Não se pode converter esses inteiros em m/s² sem examinar as escalas, chamadas de tempo e a simulação por quadro.
- Em um caminho distinto, o bit `0x4000` aplica um plano de chão (`groundy` em `+0x11C`): se Y estiver abaixo desse plano, reposiciona Y, ativa flag de contato (`statusa |= 1`) e zera uma velocidade vertical descendente. Isto não substitui a colisão de geometria regular.

## 3. `func_8002BE8C` e `func_8002C184` [CONFIRMADO]

`func_8002BE8C` recebe o objeto e o vetor de deslocamento e encaminha para `func_8002C184`.

Na segunda rotina, o número inicial de partes (`N`) é escolhido conforme a magnitude dos três componentes inteiros do deslocamento:

```text
partes_x = abs(dx) // 25600
partes_y = abs(dy) // 153600
partes_z = abs(dz) // 25600
N = max(partes_x, partes_y, partes_z) + 1
```

Derivado das multiplicações por `0x51EB851F` (X/Z) e `0x1B4E81B5` (Y), seleção do máximo e incremento de `1` em `func_8002C184`. Esta equivalência é para valores normais sem overflow/edge cases extremos da aritmética de 32 bits. A função divide os três deslocamentos por N, processa incrementos sucessivos, compara os incrementos com o restante e chama `func_8002D384` em cada iteração. Após resolver uma etapa, subtrai o deslocamento efetivo do restante, permitindo que colisões alterem o movimento.

**Interpretação física:** esta é uma forma de *substepping* de colisão; mesmo um movimento longo pode ser resolvido em submovimentos. Os eixos X/Z possuem limiar diferente do Y. Ainda falta reconstruir a geometria da colisão e seu comportamento exato nas bordas.

### Exemplos aritméticos, não medições de gameplay

| Deslocamento inteiro | Nº inicial de subpassos |
|---|---:|
| `(10000,0,0)` | 1 |
| `(25600,0,0)` | 2 |
| `(65536,0,0)` | 3 |
| `(0,65536,0)` | 1 |
| `(0,153600,0)` | 2 |
| `(65536,65536,65536)` | 3 |

Os valores são unidades fixas internas do motor; não são metros do mundo real.

## 4. Próxima parte da cadeia [CONFIRMADO / PENDENTE]

`func_8002D384` monta posições candidatas a partir do incremento, chama `func_8002C8EC` e `func_8002DF50`, e realiza consultas de obstáculos por `func_8002E3F8`. O papel completo de cada rotina, da máscara de ocupação e das resoluções de choque ainda exige análise de todos os ramos.

É preciso reconstruir, nesta ordem:

1. Geometria de colisão associada a ZDAT/WGEO e o fluxo da função `func_8002E3F8`.
2. Choques laterais, piso e teto (normal e flags associadas).
3. Diferença entre quicar em caixa, cair em plataforma e pousar em geometria.
4. Modelo de tempo e integração vertical em várias atualizações.
5. Medições dinâmicas no emulador para fechar altura real do pulo e tempo de queda.

## 5. Referências internas reproduzíveis

A origem dos trechos abaixo é o arquivo C# recompilado do próprio usuário (numeração de linhas desta extração):

| Rotina | Linha aproximada em `main.cs` | Evidência |
|---|---:|---|
| `func_8001F30C_Impl` | 18111 | física do objeto |
| `L8001F78C` | 18469 | flag de aplicação automática (`0x40`) |
| `L8001F8AC` | 18549 | posição sem colisão |
| `L8001F9D0` | 18641 | plano `groundy` |
| `L8001FA28` | 18667 | bloco gravidade `0x20` |
| `func_8002BE8C` | 35154 | entrada no colisor |
| `func_8002C184` | 35400 | número de subpassos e divisão |
| `func_8002D384` | 36859 | verificações de colisão por subpasso |

*As linhas aproximadas devem ser conferidas no arquivo C# local antes de automatizar referências e patches.*

## Limites e cuidados

- Este estudo não recupera integralmente o motor físico só por achar endereços ou constantes.
- A fonte GOOC de outra região serve para comparação, mas não substitui o binário NTSC-U.
- Usaremos as regras verificadas para **conceber implementação própria** quando a fase de investigação terminar; sem copiar o executável nem reutilizar assets do jogo comercial.
