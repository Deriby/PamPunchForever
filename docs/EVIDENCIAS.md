# Dossiê disponível e decisões de implementação

Foram lidos integralmente os quatro anexos preservados em `references/` e analisadas as duas folhas de personagem exibidas na conversa. Instruções históricas nos anexos (como “nenhum protótipo nesta fase”) descrevem a investigação anterior; a solicitação atual autoriza o desenvolvimento original.

## Evidência relatada, não revalidada contra o executável
O relatório 06 descreve posição antes de gravidade na rotina estudada, flags distintas para integração e colisão, limite de queda e divisão do deslocamento em N partes. A fórmula `max(abs(dx)//25600, abs(dy)//153600, abs(dz)//25600)+1` pode ser verificada aritmeticamente com o CSV. Não é uma medida de gameplay. Os binários e main.cs citados não estão entre os anexos; não foi possível confirmar as instruções ou o encadeamento completo. A busca textual do verificador também não demonstraria por si só semântica de execução.

## Parcial ou pendente no mapa mestre
Física horizontal, tempo global, curvas de pulo, colisão de bordas/piso/teto, trilhos exatos de câmera, estados GOOL, animação, formato das fases e som. Não foram anexados os ZIPs/estudos anteriores listados no mapa. Não alegamos ter analisado materiais ausentes nem reconstruído o motor do Crash.

## Projeto independente
Godot CharacterBody3D com varredura nativa `move_and_slide`, simulação fixa a 120 Hz, floor snap e limite de inclinação; não copiamos os limiares de subpassos de ponto fixo. Pulo variável por corte da velocidade ascendente, coyote time e buffer são decisões próprias. SI aproximado: 1 unidade = 1 metro. Parâmetros em resources/pam_tuning.tres e scripts/tuning.gd.

Estados explícitos de movimento/ataque/dano; ataques com antecipação, janela ativa e recuperação. Area3D de ataque consulta hurtboxes e deduplica por golpe. Inimigos têm patrulha, perseguição, antecipação, ataque, atordoamento e derrota. Câmera amostra Curve3D original e interpola com resposta exponencial. Zonas por progressão espacial; nenhum GOOL/bytecode original.

A progressão seguro → caixa → oponente → travessia → checkpoint → plataforma → segredo → arena → saída segue princípios gerais de ensino e ritmo. Não utiliza geometria de N. Sanity Beach. Tudo no projeto é original ou gerado localmente; não há conteúdo comercial extraído.
