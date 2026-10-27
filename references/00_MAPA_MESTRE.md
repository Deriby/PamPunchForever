# Crash Bandicoot (1996) — Dossiê mestre de engenharia reversa

**Alvo:** versão americana NTSC-U do primeiro Crash Bandicoot (disco com `SCUS_949.00`).
**Escopo:** entender tecnicamente o motor e os dados originais antes de desenvolver outro jogo.
**Decisão de projeto:** NENHUM protótipo de jogo nesta fase. Os relatórios anteriores que incluem experimentos Godot são separados; eles não significam engenharia reversa concluída.

## Materiais primários disponíveis

- `crash font code.zip`: `main.cs`, `Entry.cs`, `Stubs.cs` (recompilação C# de instruções MIPS, não código-fonte C# escrito pela Naughty Dog).
- `SCUS_949.zip`: executável PS1 original `SCUS_949.00` com as tabelas estáticas do motor.
- `S0000009.zip`: NSD/NSF de N. Sanity Beach. Inclui `WillC` e dados de zona/câmera.
- `S0000004.zip`: par NSD/NSF relacionado a conteúdo de desenvolvimento (caverna).

## Legenda de evidência

- **Confirmado:** bytes, instruções e comportamento algébrico inspecionados diretamente nos arquivos NTSC-U enviados.
- **Comparado:** interpretação sustentada por outra revisão do jogo/documentação; diferenças regionais ainda possíveis.
- **Pendente:** falta engenharia ou experimento que demonstre o comportamento real.

## Sequência de investigação

| Fase | Tópicos | Progresso | Critério de saída |
|---|---|---|---|
| 1 | Boot, estrutura PS-X EXE, memória e ciclo do motor | Parcial | Diagrama de chamadas e fluxo de inicialização checado |
| 2 | NSD/NSF, chunk, entry, ZDAT, GOOL, recursos | Parcial | Extratores para todos os tipos relevantes com testes |
| 3 | Interpretador GOOL, eventos, estados, botões | Parcial | Fluxo de estados do jogador comprovado na NTSC-U |
| 4 | Física horizontal, tabelas, aceleração, frenagem | Parcial | Coeficientes, flags e tempo de atualização validados |
| 5 | Física vertical, pulo, queda, colisão e chão | **Em andamento** | Integração e resolução de colisão rastreadas de ponta a ponta |
| 6 | Câmera, seus trilhos, zonas e transições | Parcial | Projeção e interpolação de câmera reconstruídas |
| 7 | Caixas, itens, inimigos, dano, progresso e chefes | Pendente | Diagramas de estados/colisões para scripts GOOL |
| 8 | Animação, geometria, textura, iluminação, PS1 GPU | Pendente | Estruturas, decodificação e pipeline descritos |
| 9 | Som, música, streaming, alocação de memória | Pendente | Canais, eventos, paging e formatos documentados |
| 10 | Validação em execução, medidas por quadro | Pendente | Diferenças estático/dinâmico registradas; limites claros |
| 11 | Síntese e especificação independente | Pendente | Documento técnico completo sem código ou assets protegidos copiados |

**Importante:** "completa" é objetivo de cobertura dos sistemas relevantes, não promessa de recuperar automaticamente todo o código original ou nomes de funções. Hipóteses nunca serão rotuladas como descobertas.

## Artefatos já gerados em etapas anteriores

- `Analise_Crash_Caverna_04.zip`
- `Analise_Crash_N_Sanity_Beach_09.zip`
- `Crash_PS1_WillC_Analise_01.zip` e `Crash_PS1_WillC_Etapa_02.zip`
- `Crash_PS1_Fisica_Etapa_03.zip` e `Crash_PS1_Fisica_Etapa_04.zip`

**Próxima análise:** detalhar `func_8002D384`, que recebe cada subpasso e chama `func_8002C8EC`, `func_8002DF50` e `func_8002E3F8`, e relacionar os resultados com `Status Flags A` (`0x1`, `0x40000`, etc.) e o estado GOOL.

## Fontes de apoio (secundárias)

- https://wiki.cbhacks.com/w/Object
- https://wiki.cbhacks.com/w/Memory_Map
- https://github.com/ManDude/goocdump/blob/master/Crash%201/NTSC-J/WillC.gooc (região diferente)
