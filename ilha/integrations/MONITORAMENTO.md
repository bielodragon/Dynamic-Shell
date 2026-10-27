# Bateria, desempenho e FPS

O Control Center tem quatro controles independentes: **Modo desempenho**, **Status do dispositivo**, **FPS nos jogos** e **Bateria na ilha**. Nenhum deles altera clocks ou escolhe GPU dedicada globalmente.

## Bateria

A ilha e o cabeçalho da pesquisa mostram bateria somente quando há bateria de alimentação do computador. Usa o dispositivo agregado do UPower, com fallback para sysfs; mouse e outros periféricos são excluídos. Mostra porcentagem, carga e alerta de pouca bateria. Em desktop sem bateria não aparece um indicador fictício. O Control Center conserva seu resumo da alimentação.

A leitura sem métricas é a cada 15 segundos. Ativando métricas, usa intervalo de 2 segundos. Não foi testado em notebook físico nesta etapa; o teste QML simula presença/ausência/carga e confere o widget.

## Modo desempenho

Desliga blur, sombras e animações do Hyprland e reduz as animações da Ilha. Guarda os valores anteriores em arquivo próprio de runtime, separado por instância do compositor. Ao desligar, restaura o que gerenciou; mudanças externas posteriores têm prioridade. O comando `ilha stop`/`reload` restaura o modo antes de encerrar o shell. Não grava no arquivo do Hyprland, não modifica perfis de driver e não promete um aumento específico de FPS.

Suporta `hyprctl keyword` no parser antigo e `hyprctl eval`/`hl.config` no Lua. Em caso de falha ao aplicar, tenta reverter. Se a Ilha for encerrada externamente/abruptamente, o arquivo de recuperação permanece; reabra a Ilha e desligue o modo. Uma nova sessão do Hyprland usa sua configuração normal. Outros gerenciadores podem alterar os efeitos enquanto o modo estiver ativo.

## Status do dispositivo

Overlay por monitor no canto superior direito, sem capturar cliques. Mostra CPU por diferença de contadores de `/proc/stat`, RAM por MemAvailable, temperaturas reconhecidas e uso de GPU quando o driver exporta dados legíveis. Sensores indisponíveis são omitidos ou aparecem como “—”; não se usa taxa do monitor como FPS. A CPU precisa de duas amostras para a primeira medição.

O overlay usa tokens do Theme e abre espaço vertical quando há uma notificação. A preferência é persistente em `monitoring.metrics`.

## FPS real com MangoHud

É necessário iniciar o aplicativo com o wrapper **ilha-game**; não é possível injetar o medidor automaticamente em todo jogo já aberto. O FPS é calculado pelo MangoHud nas apresentações de frames, dentro do aplicativo, e não pelo overlay Qt da Ilha.

```sh
# Jogo/aplicativo Vulkan:
ilha-game -- /caminho/do/jogo argumento

# Aplicativo OpenGL que requer interposição dlsym:
ilha-game --opengl -- /caminho/do/jogo argumento
```

Na Steam, em Propriedades → Opções de inicialização do jogo, configure explicitamente:

```sh
/home/SEU_USUARIO/.local/bin/ilha-game -- %command%
```

Substitua o caminho pelo resultado de `command -v ilha-game`. Na instalação global o comando fica em `/usr/local/bin/ilha-game`. Ajustes da Steam não são escritos automaticamente nesta etapa. Integração com a biblioteca e estados de downloads continua na fase própria de Steam.

O wrapper inicia o MangoHud mesmo com o HUD inicialmente oculto, para permitir ligar/desligar pelo Control Center durante a execução. Usa socket abstrato e registro de runtime próprios; o controle não interfere em sessões de MangoHud iniciadas fora da Ilha. Estado inicial vem de `monitoring.fps`, que é persistente. O protocolo do MangoHud é um toggle sem leitura do estado: se alternar o HUD também pelo atalho interno do MangoHud, a indicação da Ilha pode ficar desencontrada; reiniciar pelo wrapper reaplica a preferência salva.

O HUD exibe FPS, frametime, CPU/temperatura e RAM. Não habilita por padrão campos de GPU/VRAM, pois alguns drivers exibem zero sem suporte; sensores de GPU validados ficam no status da Ilha. Cores vêm do tema salvo/destaque no início do jogo; o HUD externo não acompanha a prévia do editor ao vivo. A posição inicial fica abaixo da área da ilha. Argumentos são passados sem shell, e o wrapper não registra nomes de arquivos/documentos nem o comando completo do jogo.

Dependências opcionais: `mangohud` e `lib32-mangohud` para aplicativos 32 bits. Nesta máquina o usuário autorizou ambos; pacman instalou versão **0.8.4-1** com dependências. Nenhum pacote AUR foi utilizado. O suporte ao overlay depende do driver e do tipo de execução do jogo.

## Verificação

- 46 testes Python e 3 testes JS passaram; testes específicos cobrem amostras CPU/RAM, bateria e periféricos, ausência de sensores, restauração/rollback dos efeitos e comandos do socket.
- `check_device_integration.py`: QML offscreen, bateria simulada e configuração temporária; confere visibilidade, métricas ligadas/desligadas e persistência de FPS.
- `check_preferences_integration.py`: regressão das preferências existente passou.
- `check_monitor_desktop.py`: opt-in, abre **glxgears** com MangoHud, testa efeitos reais e restaura preferências no finally. Requer sessão desbloqueada e monitor eDP-1. Não inicia jogos da biblioteca, altera rádio ou executa ações de energia. O teste observou FPS real em OpenGL; isso não é benchmark de ganho de desempenho nem validação de jogo 32 bits/NVIDIA.
- Capturas `/tmp/ilha-fps-metricas.png` e `/tmp/ilha-monitor-control-center.png` inspecionadas. Preferências e efeitos restaurados, processo de teste encerrado. Os avisos de GPU radeon não suportada pelo MangoHud motivaram a omissão dos campos correspondentes.

Fontes primárias: [UPower](https://upower.freedesktop.org/docs/Device.html), [configuração MangoHud](https://github.com/flightlessmango/MangoHud/blob/master/data/MangoHud.conf), [protocolo de controle](https://github.com/flightlessmango/MangoHud/blob/master/src/control.cpp), [configuração Hyprland](https://wiki.hypr.land/configuring/core/config-options/). Código próprio, sem cópia de trechos desses projetos.
