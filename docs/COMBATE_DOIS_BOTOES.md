# Uma ação, um pulo

O Pam aprovado está integrado à Fase 1. **J / X** encadeia **giro → soco médio → soco forte de longo alcance**. **Espaço / A** pula; segurar o pulo aumenta a altura. WASD/setas ou analógico movem o personagem. Os rótulos X/A seguem o controle Xbox; no PlayStation correspondem a quadrado/cruz.

Cada toque avança um golpe. Toques antecipados podem guardar os dois golpes restantes, sem pular suas animações nem iniciar outro ciclo automaticamente. Segurar ação executa só o giro. Após um golpe isolado há 0,22 s para continuar a sequência. O finalizador tem recuperação completa; depois dela, um novo toque volta ao giro. Dano, morte e reaparecimento limpam a fila. Os mesmos golpes funcionam no ar; não há botões separados de forte, giro, ataque aéreo ou esquiva.

## Animação e contato

`scripts/pam_animator.gd` carrega `assets/models/pam_usuario_rig.glb` e amostra os clipes na física. O modelo do usuário, sem rabo, substitui o Pam anterior no jogo. A fonte tem 22 ossos e 12 clipes: os novos `Medium`, `Strong`, `Jump` e o `Combo` recomposto coexistem com os clipes de edição anteriores. O jogo usa `Spin`, `Medium`, `Strong`, `Guard`, `Run` e `Jump`.

O soco médio usa extensão menor; o forte amplia a antecipação, extensão, avanço do ombro e recuperação. As mãos continuam com pesos corrigidos e escalonamento compensado. O comprimento do antebraço no impacto é 1,15 no médio e 1,34 no forte; os punhos chegam a 1,085 e 1,15. Essas alterações existem apenas nas poses de ataque. A geometria de repouso, normais, UVs, índices, matrizes de vínculo e imagens PBR foram comparados com a versão anterior e permanecem idênticos.

`resources/combat_moves.tres` centraliza ordem, janelas, dano, impulso, raios, avanço e marcadores dos clipes. `tools/user_model/animate.py` lê o mesmo recurso para gerar a sequência de revisão. O combo encadeado dura cerca de 1,31 s; o clipe combinado é amostrado a 30 FPS e termina em 1,333 s. O controlador não depende desse arredondamento: executa os tempos do recurso em passos físicos de 120 Hz.

Cada punho tem uma Area3D. Durante a janela ativa, uma consulta usa esfera na posição atual e cápsula ao longo do deslocamento desde o passo anterior. Isso cobre o movimento rápido de rotação/esticamento. A fila de alvos impede dano duplicado pelas duas mãos do giro ou pela permanência de uma mão na hurtbox. Paredes bloqueiam contato; a superfície de uma caixa permite acertá-la. O forte causa 3 de dano e impulso 8,5, contra 1 de dano e impulso 2 no médio. Inimigos usam atordoamento, knockback e hitstop mais fortes no finalizador.

Rastros acompanham os punhos. Na fase, os efeitos de impacto são disparados por contato confirmado. Os acentos de coreografia continuam disponíveis apenas na cena separada de revisão. Os NPCs ainda usam a animação anterior.

## Abrir e verificar

Abra `project.godot` no Godot **4.4.1** e pressione F5. Os controles novos aparecem no menu, pausa e dicas da fase. A cena `scenes/pam_combat_review.tscn` é uma ferramenta de autoria: F6 reproduz o combo; 1–5 selecionam combo, giro, médio, forte e pulo; Espaço pausa, setas avançam um quadro, V muda a câmera e 0 mostra a T-pose.

```sh
./tools/godot.sh --headless --editor --import
./tools/godot.sh --headless --fixed-fps 120 --script tests/action_combat.gd
./tools/godot.sh --headless --fixed-fps 30 --script tests/action_combat.gd
./tools/godot.sh --headless --fixed-fps 120 --script tests/integration.gd
./tools/godot.sh --headless --fixed-fps 120 --script tests/traverse.gd
./tools/godot.sh --headless --fixed-fps 30 --script tests/traverse.gd
PAM_HAND_REPORT=/workspace/deliverables/pam_action/hands.json blender -b -t 4 -P tools/user_model/check_hands.py
PAM_REVIEW_SCRIPT=tests/render_action.gd ./tools/render_review.sh --fixed-fps 30
python3 tools/user_model/compose_action.py
```

Os testes de combate passaram **20/20** em 30 e 120 FPS simulados: botões, segurar/pressionar, três toques antecipados, ordem, recuperação, tolerância, alcance físico, reação, deduplicação, parede, interrupção, pulo e reaparecimento. A integração passou **33/33**, incluindo prólogo, colisões, caixas, IA, checkpoint, morte, plataforma móvel, segredo, arena, conclusão e TNT. O percurso terminou em ambas as taxas com **zero mortes**, checkpoint e seis inimigos derrotados. O bot usa movimentação, pulo e o mesmo método da ação; não teletransporta nem causa dano por chamadas remotas.

A [prévia](captures/pam-combo-acao.gif) vem de 120 capturas reais de 640×480 da própria fase, com entradas de ação/pulo e câmera posicionada para revisão. [Vídeo](captures/pam-combo-acao.mp4) · [quadros dos três golpes](captures/pam-combo-acao.png) · [relatório](captures/pam-combo-acao-verificacao.json). Os tempos do render são fixados para registrar a sequência; isso não é medição de desempenho em GPU nem teste manual de conforto com controle. A primeira importação headless mantém o diagnóstico interno de textura do renderizador dummy, sem falha de script ou recurso nos testes.
