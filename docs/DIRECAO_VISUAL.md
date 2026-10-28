# Direção visual — histórico e nova referência PS1

**Atualização do elenco:** `Januri.glb` (Jaburanga), `Inimigo.glb` e `Lar.glb`, fornecidos pelo usuário, substituem os três desenhos de NPC abaixo. As malhas recebidas, texturas e acessórios são a referência ativa; foram acrescentados rigs e clipes. O mestre atual não tem cajado e Lar tem a katana embainhada. Veja [NPCS_USUARIO.md](NPCS_USUARIO.md), a prévia e os limites de skinning. As descrições e números de validação abaixo são históricos.

**Diretriz atual:** o usuário substituiu os estudos anteriores pelo seu próprio GLB em T-pose. O [modelo do usuário](MODELO_USUARIO.md) é a base visual prioritária do Pam. A edição remove o rabinho e adapta o rig e os movimentos cartunescos às suas proporções. As texturas fornecidas e a forma da cabeça/corpo foram preservadas fora da reparação localizada. A construção/animação PS1 continua como referência de linguagem; este modelo não é uma recuperação de dados comerciais.

O restante deste documento registra a revisão anterior. O **Pam, estudo 03**, visível em `docs/captures/pam-modelo-v3.png`, chegou a ser aprovado, mas essa aprovação foi retirada. O GLB dessa revisão foi substituído no personagem jogável pelo modelo fornecido pelo usuário. `assets/source/approved_pam.sha256` conserva apenas sua identificação histórica, sem representar aprovação vigente.

A revisão anterior usou volumes facetados desenhados, pintura integrada ao rosto, silhuetas reconhecíveis, couro/tecido foscos, cores quentes nas roupas e verdes naturais no ambiente. Naquela etapa o rosto do Pam e suas proporções foram preservados. Não foram usados modelos de jogos comerciais.

## Elenco presente na fase

- **Jaburanga:** rosto de jabuti com expressão firme e escamas pintadas; barba volumétrica; chapéu de palha com trama e borda; casco com escudos e espirais; roupa bege/vermelha, membros fortes, mãos no cajado, garras e fitas. O cajado acompanha o braço articulado. A rapidez narrativa e o papel de mestre poderoso permanecem.
- **Assassino:** volume de capuz com máscara esculpida, marca vermelha, gola dobrada, casaco dividido e faixas presas aos antebraços. É um design original provisório para uma identidade oculta, não uma concept aprovada.
- **Guardiões:** duas variações originais com máscaras de madeira pintadas, tecido, ombreiras, braçadeiras e amarrações. Os nomes de desenvolvimento são Guardião do Jatobá e Sentinela do Igarapé. São habitantes fictícios do mundo; não representam povos ou símbolos reais. As duas variações usam a IA já existente e têm o mesmo balanceamento.

## Ambiente e objetos

Foram substituídos os modelos de árvores, folhas, samambaias, rochas, caixas, explosivos, altar e amuleto. Foram acrescentados palmeiras/folhas largas, bromélias estilizadas, moitas altas, raízes e folhas caídas. O solo tem uma faixa de terra irregular entre margens de musgo; rochas quebram a silhueta das ilhas e margens do curso d'água. Ruínas, portão, balsa e ponte têm módulos próprios, madeira/pedra pintadas e detalhes de construção.

Sementes e lembrança agora possuem modelos diferentes. Caixas têm tábuas, encaixes, marcas originais e pinos; explosivos têm pintura de alerta e pavio. O altar integra entalhe, raízes e cristal de jade. Os grafismos são originais e fictícios.

A distribuição da vegetação ganhou camadas de altura e variações de espécie/silhueta. Os modelos estáticos usam MultiMesh em setores espaciais; plantas pequenas não projetam sombras adicionais. Terreno estático é agrupado por material, sem misturar madeira e terra na mesma superfície. Materiais, névoa, céu e água foram ajustados para a paleta da fase.

## Integração e verificação

O percurso, as áreas de colisão, as velocidades, o tamanho dos saltos e os hitboxes não foram redesenhados nesta tarefa. O plano da ponte e o topo da balsa foram alinhados às colisões que já existiam. A troca de arte foi validada com **32/32 verificações de integração** e travessia completa: `ending`, 0 mortes, checkpoint ativo, 5 inimigos derrotados, 24 sementes, 4 saltos e 14 contatos de ataque. Todos os GLB foram inspecionados para referências de textura; os personagens mantêm os pivôs Head/Torso/ArmL/ArmR/LegL/LegR. Contagens de triângulos em `ASSETS.md`.

As prévias `elenco-fase1.png` são renders dos GLB usados no jogo, em Blender. `cenario-fase1.png` contém capturas reais do Godot com câmeras e atores preparados para revisão de arte, sem retoque. Elas não substituem o teste de percurso nem representam uma gravação de gameplay manual. As capturas individuais e logs da revisão acompanham o projeto.

Nesta máquina o renderizador Mesa llvmpipe por software ficou em aproximadamente **2–3 FPS** nas capturas da revisão. Desempenho em uma GPU real, conforto de controle e legibilidade em movimento continuam sem validação humana. A primeira importação headless de GLB pode emitir os diagnósticos de textura do renderizador dummy já descritos em `VALIDACAO.md`; as capturas e testes usam os recursos resultantes. Não se deve descrever o editor virtual como livre de diagnósticos.

## Reproduzir a arte

```sh
python3 tools/style/paint.py
blender -b -t 4 -P tools/build_world_art.py
./tools/godot.sh --headless --editor --import
PAM_REVIEW_SCRIPT=tools/review_stage.gd ./tools/render_review.sh
blender -b -t 4 -P tools/preview_cast.py
python3 tools/compose_style_review.py
```

A reprodução das imagens usa Python, Pillow e NumPy; a geração de malhas usa Blender 4.3.2. Esses pacotes são ferramentas de autoria opcionais: os GLB e PNG já estão incluídos e o jogo só precisa do Godot 4.4.1. `tools/build_art.py` mantém o modelo anterior por padrão. A opção legada `PAM_REBUILD_APPROVED_PAM=1` regenera essa versão anterior; o novo estudo tem geradores independentes em `tools/ps1/`.

O próximo acabamento é avaliar artisticamente estes novos modelos com o usuário, pintar variações adicionais e substituir animações procedurais por clipes com antecipação, impacto e recuperação dirigidos. Não houve regravação de áudio, dublagem, nova campanha ou redesenho da IA nesta revisão.
