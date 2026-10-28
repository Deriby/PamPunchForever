# PAM: PUNCH FOREVER

**A Trilha da Vingança** · Godot **4.4 / 4.4.1 stable** · GDScript · plataforma 3D e combate original.

O Pam jogável usa o **modelo fornecido pelo usuário**, sem rabinho, com rig de 22 ossos, mãos corrigidas e animações cartunescas. O combate usa **um único botão**: **giro → soco médio → soco forte de longo alcance**. O outro botão é o pulo. Três toques encadeiam os golpes; segurar ação executa só o giro. O combo também funciona no ar.

[Prévia dos controles na fase](docs/captures/pam-combo-acao.gif) · [Vídeo](docs/captures/pam-combo-acao.mp4) · [Regras do combate](docs/COMBATE_DOIS_BOTOES.md). F5 inicia o jogo; `scenes/pam_combat_review.tscn` continua disponível para revisar os clipes com F6.

Uma primeira fase compacta, do prólogo ao antigo porto. Pam perde Jaburanga no confronto de abertura, enfrenta brevemente o assassino e inicia a jornada. A trilha ensina movimento, caixas e combate antes de introduzir ponte, raízes inclinadas, altar de checkpoint, balsa móvel, desvio secreto, fenda e arena de saída. A arena só abre após a derrota dos dois guardiões.

## Download no GitHub

[Baixar o projeto completo (.zip)](https://github.com/Deriby/PamPunchForever/archive/refs/heads/main.zip). Extraia o arquivo e importe `project.godot` no Godot 4.4.1. O ZIP inclui os assets; não exige Git LFS nem plugins.

## Abrir e jogar

1. Extraia o projeto mantendo as pastas. No **Godot 4.4.1** (correção da série 4.4), importe `project.godot`.
2. Espere a importação dos GLB, fontes e WAV. Pressione **F6** com `scenes/trail.tscn` aberta ou **F5** para o projeto.
3. No menu, escolha **Começar**. Enter durante a introdução avança ao confronto jogável; a derrota faz parte da história.

No ambiente preparado: `./tools/godot.sh --editor` abre o editor; `./tools/godot.sh` inicia o jogo quando houver display. `./tools/setup.sh` reproduz a instalação Linux x86_64 com SHA-512 e executa a suíte de integração. Sem display, use os testes headless abaixo. Não são necessários plugins, credenciais ou serviços externos. Os assets já estão incluídos; Blender não é dependência de execução.

## Controles

| Ação | Teclado | Controle padrão Godot / Xbox |
|---|---|---|
| Mover | WASD / setas | Analógico esquerdo |
| Pular (segurar = mais alto) | Espaço | A |
| Ação: giro → soco médio → soco forte | J, J, J | X, X, X |
| Pausar / controles | Esc | Back / View |
| Começar / avançar ao confronto | Enter | Start / Menu |
| Retornar ao checkpoint | R | Teclado |
| FPS, velocidade, estado, câmera | F3 | Teclado |

O checkpoint é ativado por aproximação do altar dourado. Cura Pam e guarda a posição **durante a sessão**. Cair ou perder toda a vida retorna a esse ponto; objetos coletados e inimigos derrotados permanecem resolvidos. R no final reinicia toda a fase. O menu e a pausa também têm botões clicáveis.

## Implementação

- CharacterBody3D com aceleração, frenagem, controle aéreo, chão inclinado, snap, teto, pulo variável, buffer, coyote time e limite de queda; 120 passos físicos/s.
- Giro → soco médio → soco forte no mesmo botão, com fila de entradas, tolerância entre toques e recuperação do finalizador. Funciona no chão e no ar. Volumes dos golpes acompanham os punhos animados, com varredura entre passos, bloqueio por paredes e um dano por alvo/golpe. Knockback, atordoamento, hitstop, estilhaços e efeitos sonoros. Inimigos patrulham, perseguem, antecipam, atacam e reagem.
- Quique sobre inimigos/caixas, caixas quebráveis, explosivos com pavio de 3 segundos e reação em cadeia, sementes, checkpoint e amuleto secreto.
- Camera3D sobre Curve3D própria, suavização exponencial, enquadramento de segredo, tremor e planos do prólogo.
- Floresta com assets low-poly originais: panda de jaqueta, jabuti com chapéu/casco/cajado, guardiões, assassino, árvores com raízes e cipós, samambaias, rochas, ruínas e porto. Vegetação agrupada com MultiMesh. Paleta, iluminação, neblina, textura de solo e água animada.
- Pam com skin e clipes de esqueleto amostrados na física; transições de pose, esticamento temporário e rastros. Animação procedural dos NPCs e pequenas sequências no motor. HUD, dicas contextuais, pausa, conclusão e depuração.
- Áudio sintetizado original: percussão, baixo, cordas dedilhadas e camada sutil de sintetizador. **Trilha e efeitos temporários**, com gerador incluído, sujeitos a direção musical posterior.

## Testes reproduzíveis

```sh
./tools/godot.sh --headless --editor --import
./tools/godot.sh --headless --fixed-fps 120 --script tests/action_combat.gd
./tools/godot.sh --headless --fixed-fps 30 --script tests/action_combat.gd
./tools/godot.sh --headless --fixed-fps 120 --script tests/integration.gd
./tools/godot.sh --headless --fixed-fps 120 --script tests/traverse.gd
./tools/godot.sh --headless --fixed-fps 30 --script tests/traverse.gd
python3 tests/check_dossier.py
```

`integration.gd` cria fixtures físicas para testar sistemas isolados. `traverse.gd` percorre a fase com movimento, pulos e ataques reais: não teletransporta, não altera vida e não abre o portão por chamada de teste. As capturas em `docs/captures/` são renderizadas pelo Godot; o runner `tests/capture.gd` requer display e grava imagens em `/tmp`. Para repetir a revisão gráfica no cloud, use `./tools/render_review.sh` (Xorg dummy local; sem preview web). Resultados e limites em [VALIDACAO.md](docs/VALIDACAO.md).

## Arquitetura e autoria

`scenes/trail.tscn` é a entrada. `scripts/trail.gd` monta o percurso autoral e coordena narrativa/progresso; `player.gd`, `enemy.gd`, `prop.gd`, `rail_camera.gd`, `forest.gd` e `hud.gd` separam as responsabilidades. Os valores de ajuste estão em `resources/pam_tuning.tres` / `scripts/tuning.gd`; use o Inspector para os parâmetros exportados. `resources/combat_moves.tres` centraliza a ordem, os tempos, dano, impulso, raios e marcadores de animação; o autor de animações no Blender lê o mesmo recurso. `pam_animator.gd` conecta o modelo aprovado ao controlador e às colisões.

Os quatro documentos recebidos foram lidos e preservados em `references/`. [EVIDENCIAS.md](docs/EVIDENCIAS.md) distingue o que o relatório afirma, o que pode ser testado aqui e as escolhas originais. Não foram fornecidos o executável, main.cs nem os ZIPs citados pelo mapa mestre. Não há código, modelos, música ou geometria comercial do Crash neste projeto.

`tools/build_world_art.py` regenera os modelos de apoio com Blender 4.3.2, preservando o Pam anterior. As texturas de apoio são geradas por `python3 tools/style/paint.py`. `tools/build_art.py` usa essa mesma biblioteca e só refaz a versão anterior do Pam se a opção legada `PAM_REBUILD_APPROVED_PAM=1` for definida explicitamente. O novo estudo usa `tools/ps1/`. `tools/build_audio.py` requer Python e NumPy; os WAV gerados já estão no projeto. A textura de solo é original. As fontes DejaVu mantêm sua licença em `assets/fonts/LICENSE.txt`.

## Escopo e acabamento pendente

Esta entrega é uma Fase 1 curta e jogável, não a campanha completa nem uma produção comercial finalizada. O modelo do Pam é o fornecido e aprovado pelo usuário; os NPCs e o restante da arte ainda precisam da revisão final. Os NPCs ainda precisam de revisão de animações e o Pam não tem novas expressões faciais. Não há dublagem, tela de configurações, remapeamento de teclas, gravação em disco ou exportação assinada. A música é temporária; instrumentação sintetizada não substitui gravações/direção musical final.

Não houve teste manual de conforto com teclado/controle nem avaliação auditiva humana neste ambiente. A primeira importação headless sem cache emite diagnósticos internos de textura do Godot; a integração atual passou 33/33; o registro de 32/32 do ZIP extraído refere-se à versão inicial. O editor virtual também registra uma extensão Vulkan ausente; detalhes nos logs e em docs/VALIDACAO.md. No renderizador por software deste ambiente, as capturas da revisão visual atingiram cerca de 2–3 FPS; desempenho e fluidez em GPU ainda precisam ser validados. O código e as capturas não comprovam sensação de controle, qualidade artística final ou fidelidade técnica ao Crash. Esses itens requerem revisão humana. Consulte [ARTE_PENDENTE.md](docs/ARTE_PENDENTE.md) antes de tratar qualquer asset como aprovado.
