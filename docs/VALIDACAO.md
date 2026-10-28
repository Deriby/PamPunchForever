# Verificação atual: elenco fornecido com rig

**Revisão atual de animação:** 21 clipes no Pam, 20 por NPC, **18/18 testes de estados em cada execução a 30/120 FPS**, além de 35/35 de integração, 20/20 de combate em ambas as taxas e travessia completa sem mortes em ambas. Prévia, comandos, preservação da arte e limites: [ANIMACOES_VIVAS.md](ANIMACOES_VIVAS.md). Os resultados abaixo registram as etapas anteriores.

Mestre (`Januri.glb`), inimigo e Lar têm skins nativas, cotovelos, joelhos, acessórios e caudas articuladas, e já substituem o elenco anterior na fase. No Godot 4.4.1: **35/35 testes de integração**, **20/20 de combate em cada execução a 30/120 FPS** e travessia integral nas duas taxas, **0 mortes e 6 inimigos derrotados**. Verificação independente da geometria/UVs/normais/texturas e reabertura das três fontes Blender também passaram. Prévia, comandos, logs e limites: [NPCS_USUARIO.md](NPCS_USUARIO.md). As imagens são renders reais; não houve avaliação manual com controle ou GPU dedicada.

# Histórico: combate de dois botões

O novo Pam está integrado à fase. O combate usa ação para giro → médio → forte e um botão de pulo. A validação atual passou 20/20 testes de combate em 30/120 FPS simulados, 33/33 de integração e percurso completo nas duas taxas, sem mortes. Configuração, comandos, resultados e limites atuais: [COMBATE_DOIS_BOTOES.md](COMBATE_DOIS_BOTOES.md).

Os registros abaixo documentam a primeira versão da fase, anterior à troca do modelo e dos controles.

# Validação executada

**Revisão visual mais recente:** integração **32/32**, travessia completa sem mortes e quatro capturas de arte no Godot. Ver [DIRECAO_VISUAL.md](DIRECAO_VISUAL.md) e os logs `style-*`. Nesta revisão o renderizador por software marcou cerca de **2–3 FPS**; as medições anteriores abaixo são do primeiro conjunto de assets. O Pam aprovado foi preservado; elenco e ambiente de apoio foram atualizados.

Ambiente Linux x86_64. Godot 4.4.1 stable oficial `49a5bc7b6`; arquivo ZIP verificado contra SHA-512 do release oficial, sem desativar TLS ou integridade. Blender 4.3.2 gerou os GLB. O projeto também executou na versão 4.4 stable; ela exibiu erro interno do diálogo de progresso do editor ao importar. A correção 4.4.1 eliminou esse diagnóstico e é a versão fixada nos scripts.

## Resultados

| Verificação | Resultado observado |
|---|---|
| `tools/setup.sh` | Download/cache verificado, extração, importação headless e integração concluídos; código de saída 0 |
| Importação de cópia limpa sem `.godot` | Recursos GLB, WAV, PNG, TTF e scripts importados; integração 32/32 no ZIP extraído. O primeiro import headless emite diagnósticos do renderizador dummy descritos abaixo. |
| `tests/integration.gd` | **32/32 verificações passaram** |
| `tests/traverse.gd`, renderização simulada 120 FPS, física 120 Hz | `mode=ending deaths=0 checkpoint=true kills=5 seeds=24 jumps=4 hits=14` |
| Mesmo percurso a 30 FPS, física 120 Hz | Mesmo desfecho e contagens; código de saída 0 |
| `tests/check_dossier.py` | **8/8 exemplos aritméticos** conferidos; não valida ROM/main.cs ausentes |
| `tools/render_review.sh` | Xorg dummy iniciou, Godot renderizou quatro vistas, capturas gravadas; encerrou apenas seu Xorg |

As 32 verificações cobrem mapeamento de setas/F3, menu, abertura, participação no confronto, pose da derrota, transição à fase, contato de piso, aceleração, frenagem, pulo completo e curto, teto, parede, rampa, hitbox/hurtbox, knockback, deduplicação de dano, sequência jab/cross/chute, quebra de caixa, ataque fora de alcance, ataque real da IA, esquiva acionada por Input, checkpoint/curar, morte/reaparecimento, transporte pela balsa, segredo, arena/guardiões, remoção do bloqueio da saída, conclusão, armamento e explosão TNT.

O teste de percurso usa o controlador real e as janelas de ataque. Não teletransporta, não concede invulnerabilidade, não chama dano remoto e não força abertura do portão. Elimina cinco dos seis guardiões do percurso; um inimigo opcional é contornado. O segredo é validado separadamente na integração, não nessa rota. A suíte isolada cria fixtures e reposiciona o jogador entre testes; isso é distinto do percurso de ponta a ponta.

## Renderização e limites

As [capturas](captures/menu.png) são imagens reais do Godot 4.4.1, OpenGL Compatibility / Mesa llvmpipe, 1152×720. As posições de revisão são preparadas por `capture.gd`, não constituem comprovação de jogo manual. Foram inspecionados menu, prólogo, início da trilha e checkpoint. A inspeção corrigiu iluminação excessiva, enquadramento do menu e ocultação do jogador pelo lintel das ruínas. Lintéis usam um recorte de câmera deliberado durante a passagem; colisores laterais ficam ativos.

O renderizador por software desta máquina atingiu aproximadamente **4–5 FPS** nas capturas após agrupamento estático de terreno/vegetação e redução de sombras (antes: cerca de 2 FPS). Esse ambiente serve para importação, testes e revisão visual, **não para validar fluidez de jogo manual**. Não foi medida uma GPU real nem hardware de destino. Os testes a 30/120 FPS usam tempo de renderização simulado e demonstram comportamento da simulação, não desempenho gráfico real nessas taxas. Continua necessária uma sessão em GPU para perfil de desempenho, sensação de combate, leitura dos saltos e ergonomia com controle.

O aviso de V-Sync não suportado é do display virtual. A primeira importação de uma cópia sem cache concluiu com código 0, mas emitiu **13 diagnósticos `Parameter "t" is null`** em `servers/rendering/dummy/storage/texture_storage.h`, um ao salvar cada GLB pelo importador headless. Isso não foi erro de GDScript: todos os modelos resultantes foram carregados nos testes e os modelos da cena foram renderizados nas capturas. A importação com editor gráfico/software também terminou com código 0, mas o editor registrou ausência da extensão Vulkan `VK_KHR_surface`, inclusive quando OpenGL foi explicitado. Portanto, **não classificamos o editor gráfico do cloud como livre de diagnósticos**. A execução do jogo em OpenGL funciona para captura; uma estação com GPU continua necessária para validar o fluxo gráfico completo. Os logs de instalação com cache, testes e captura finais não tiveram erros de script/recurso. Os logs de importação limpa e editor/software foram incluídos para transparência. A trilha e efeitos foram gerados, importados e disparados pelo código, mas **não foram ouvidos/avaliados por uma pessoa** neste ambiente.

Não houve validação dinâmica de Crash em emulador, leitura de binário ausente, teste manual prolongado, teste de controle físico, exportação para consoles ou garantia de taxa de quadros em dispositivos. O checkpoint é volátil e não há save persistente. Arte/animação/áudio ainda precisam da produção e aprovação descritas em [ARTE_PENDENTE.md](ARTE_PENDENTE.md).

Logs finais estão em `docs/test-logs/`. Não confundir implementação funcional da fase com aprovação artística ou produção comercial final.
