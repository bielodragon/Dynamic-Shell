# Control Center — fase 8

Arraste o fundo da ilha para baixo ou clique na pequena alça abaixo dela. A alça de cima do painel permite arrastá-lo para fechar. Também fecha por Escape, pelo botão Fechar ou ao clicar fora da superfície. A ilha continua mostrando seus indicadores habituais quando o painel está fechado.

O painel é carregado por `LazyLoader` apenas quando necessário e mantém a instância até terminar a animação de fechamento. Sua largura, altura e posição animam a partir do topo. Um único monitor fica selecionado para o painel de cada vez; as ilhas continuam usando `Variants`. Em telas menores, o conteúdo tem rolagem vertical, e a faixa de temas tem rolagem horizontal.

## Controles

| Controle | Comportamento |
| --- | --- |
| Wi-Fi | Liga/desliga o rádio pelo NetworkManager e mostra a conexão principal. Não é um seletor de redes/senhas |
| Bluetooth | Liga/desliga adaptadores BlueZ e informa o número de dispositivos conectados. Pareamento continua no gerenciador Bluetooth |
| Modo avião | Desliga rádios Wi-Fi/WWAN geridos pelo NetworkManager e adaptadores Bluetooth. Ao desativar, restaura os estados salvos antes de ativar |
| Não perturbe | Usa o estado persistente já existente do servidor de notificações da Ilha |
| Volume | Saída padrão do PipeWire, de 0 a 100%, com botão mudo. O valor é enviado ao soltar o slider ou usar as teclas de ajuste |
| Brilho | Backlight da tela integrada, entre 1 e 100%, via brightnessctl. Não usa DDC/CI para monitores externos |
| Energia | Só oferece os perfis anunciados pelo power-profiles-daemon; não inventa um modo desempenho |
| Bateria | Lê baterias presentes no sysfs; mostra alimentação externa quando não existe bateria |
| Mídia | Player MPRIS disponível, mesmo se estiver em primeiro plano; título, artista e controles conforme as capacidades anunciadas |
| Temas | Cards com amostras e aplicação em um clique. “Editar cores” abre o editor já existente |
| Sessão | Bloquear, suspender, sair, reiniciar e desligar. Todos passam por confirmação dentro do painel |

Controles indisponíveis são desabilitados. Erros de permissão, serviço ou hardware aparecem no próprio painel; o shell não solicita `sudo` nem instala pacotes para contorná-los. A leitura ocorre ao abrir, a cada três segundos enquanto aberto e depois das ações. O painel fechado não mantém consultas periódicas desses controles.

O helper `system_controls.py` usa uma lista fechada de ações e listas de argumentos, sem interpretação por shell. Rejeita valores inválidos, porcentagens fora do intervalo e perfis não anunciados. Ações de sessão exigem confirmação também no helper. Volume limita a saída a 100%; brilho não chega a zero.

O bloqueio usa o comando do Omarchy quando disponível, ou hyprlock/swaylock existentes. Sair usa `uwsm stop`; os demais comandos usam `systemctl` e as permissões normais do logind/Polkit. Não foram executadas ações de desligamento, reinício, suspensão, bloqueio ou saída durante os testes.

## Modo avião e restauração

Os estados de Wi-Fi, WWAN e de cada adaptador Bluetooth ficam em `$XDG_RUNTIME_DIR/ilha/radios.json`, numa pasta privada do usuário. Não são configurações de tema. Uma falha ao desativar tenta restaurar o estado anterior e é informada no painel. Enquanto houver restauração pendente, a ação do card permite tentar restaurar novamente; controles individuais ficam desabilitados para preservar o estado salvo.

O destaque “ativo” exige estados realmente desligados, além do registro da Ilha. Uma alteração feita por outro programa não é escondida. O recurso cobre os rádios administrados por NetworkManager e BlueZ; não é uma garantia de bloqueio físico de todo transmissor do computador.

## Vidro e blur

Todos os elementos usam tokens do `Theme`, incluindo brilho especular, bordas, sombra, tooltips e sliders. As amostras de cards vêm dos próprios arquivos de tema. No tema claro, a superfície mantém opacidade mínima de 92% para evitar perda de contraste. O OLED força superfície preta sólida, sem brilho especular/sombras translúcidas.

O Qt desenha apenas formas simples; o blur real é do compositor. A regra Lua existente foi estendida:

```lua
hl.layer_rule({ match = { namespace = "ilha-(island|themes|notifications|control-center)" }, blur = true, ignore_alpha = 0.1 })
```

Backup antes da alteração: `~/.config/hypr/hyprland.lua.bak.ilha-fase8-20261023-125941`. Reload e `hyprctl configerrors` foram validados sem erros. Nenhuma regra do Caelestia/Omarchy foi removida.

## Abrir por comando e diagnosticar

Substitua `eDP-1` pelo monitor desejado:

```sh
/usr/bin/quickshell -c ilha ipc call controlCenter open eDP-1
/usr/bin/quickshell -c ilha ipc call controlCenter close
/usr/bin/quickshell -c ilha ipc call controlCenter status
```

O diagnóstico contém estado aberto/fechado, monitor, consultas do sistema e indicação de ação em andamento. O IPC do painel não expõe um comando genérico para executar ações de sessão.

## Validação e limites atuais

- 21 testes Python passaram, incluindo rejeição de entradas inválidas, limite de volume, argumentos literais, confirmação de sessão, perfis realmente disponíveis, restauração dos rádios e falha isolada de um controle.
- O teste opt-in `python3 ilha/tests/check_controls_desktop.py` passou com a Ilha rodando. Envia teclas ao painel, verifica Escape, muda temporariamente volume e brilho em um ponto, faz capturas claro/OLED e restaura tema/volume/brilho no `finally`. Só execute sem interagir com outros apps durante o teste; requer `wtype`, `grim`, áudio e backlight disponíveis e o monitor `eDP-1` deste ambiente.
- A primeira execução revelou que a ligação condicional do slider restaurava zero durante foco/tecla. A correção usa `Binding.RestoreNone`; o teste real passou depois dela.
- Leituras reais: Wi-Fi, Bluetooth, áudio, backlight Radeon e perfis Equilibrado/Economia. O daemon oferece driver placeholder neste iMac; selecionar perfil não promete ganho de autonomia nesse hardware. Não há bateria física neste computador.
- As capturas `/tmp/ilha-control-center.png`, `/tmp/ilha-control-center-light.png` e `/tmp/ilha-control-center-oled.png` foram inspecionadas. Texto e controles legíveis, cards sem sobreposição, mídia disponível e OLED com pixel de fundo `(0, 0, 0)` confirmado. O tema pessoal, volume de 40% e brilho de 100% foram restaurados.
- Wi-Fi/Bluetooth e modo avião foram lidos no hardware real; a restauração foi testada com substitutos controlados. Não desligamos rádios para não interromper a sessão em uso. Ações de energia/sessão não foram acionadas. Gestos de mouse e segundo monitor físico ainda precisam de validação manual. Não foi medido FPS nem testada GPU híbrida NVIDIA.
- Nenhum pacote foi instalado. Dependências usadas já existentes: python-dbus, NetworkManager/nmcli, BlueZ, WirePlumber/wpctl, brightnessctl, powerprofilesctl, systemd/logind e locker disponível. `wtype`/`grim` são ferramentas do teste, não do painel.

Referências: [PanelWindow do Quickshell 0.3.1](https://quickshell.org/docs/v0.3.1/types/Quickshell/PanelWindow/), [regras Lua de layers do Hyprland](https://wiki.hypr.land/Configuring/Basics/Window-Rules/#layer-rules), [nmcli oficial](https://networkmanager.dev/docs/api/latest/nmcli.html), [interface BlueZ Adapter1](https://github.com/bluez/bluez/blob/master/doc/org.bluez.Adapter.rst) e [loginctl/logind](https://www.freedesktop.org/software/systemd/man/latest/loginctl.html). Argumentos de wpctl, brightnessctl e powerprofilesctl também foram conferidos no help dos executáveis instalados.
