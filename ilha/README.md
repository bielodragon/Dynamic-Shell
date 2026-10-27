# Ilha — fases 1 a 11

Configuração nomeada de Quickshell para Hyprland, com instalação por usuário ou para o sistema. [Instaladores e comandos](../README.md) · [Integração, sincronização e reversão](integrations/INSTALACAO.md).

O checkpoint de desenvolvimento local fica em `../RETOMADA.md`; ele é excluído do pacote de distribuição.

Atividades de qualquer programa, protocolo CLI/IPC e instruções para Claude Code/OpenCode 2: [guia de integrações](integrations/README.md).

Steam, LocalSend e Minecraft Java: [catálogos na pesquisa, atividades e wrappers](integrations/APPS-JOGOS.md).

Terminal/pacman/yay e VS Code/VSCodium: [wrapper explícito e extensão local](integrations/TERMINAL-EDITORES.md).

Privacidade e gravação do OBS: [funcionamento, testes e limites](integrations/PRIVACIDADE.md).

Celular, bateria, notificações e chamadas: [integração KDE Connect](integrations/KDECONNECT.md).

Arraste a ilha para baixo ou clique na alça logo abaixo dela para abrir o **Control Center**. Feche pela alça superior, arrastando para cima, por Escape ou clicando fora. [Controles, testes e limites](integrations/CONTROL-CENTER.md).

No Control Center, **Configurações** abre a janela com módulos, aparência, temas e editor de cores; **HyprMod** abre o app existente ou informa sua ausência. [Preferências e integração HyprMod](integrations/CONFIGURACOES.md).

Clique com o botão direito no fundo da ilha para abrir a pesquisa: aplicativos, `= cálculo`, `: clipboard` e `> comando` no terminal. Use ↑↓/Tab para selecionar, Enter para confirmar e Escape para fechar. [Launcher e testes](integrations/LAUNCHER.md); [comparação visual aprovada](integrations/REFERENCIAS-LAUNCHER.md).

## Executar

```sh
/usr/bin/quickshell -c ilha
```

Passe o cursor sobre a pílula para vê-la passar pelo estado compacto e expandir. Ao sair, ela volta ao estado ocioso. O relógio e os workspaces ocupados ou ativos do monitor aparecem na ilha.

Clique em um workspace para ir até ele. A roda do mouse sobre a ilha percorre os workspaces ocupados e o ativo; um workspace vazio só aparece quando está ativo. Os ícones dos apps mostram um contador quando há mais de uma janela; se houver mais de seis workspaces visíveis, surge um contador `+N`. A seleção de estilo fica em `~/.config/ilha/config.json` e pode ser alternada sem reiniciar:

```sh
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 setWorkspaceStyle icons
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 setWorkspaceStyle dots
```

Para testar a compactação que será usada pelas atividades das próximas fases:

```sh
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 showActivity Teste
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 hideActivity
```

As notificações aparecem numa bolha ao lado da ilha e expandem ao passar o cursor. A ilha só recebe notificações reais quando é dona de `org.freedesktop.Notifications`; outro shell, como o Caelestia, pode continuar ativo, mas apenas um servidor atende esse nome D-Bus de cada vez. Uma prévia visual funciona mesmo quando o Caelestia está atendendo:

```sh
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 previewNotification
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 setDoNotDisturb true
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 setDoNotDisturb false
```

O modo não perturbe fica salvo em `~/.config/ilha/config.json`. O controle também aparecerá no Control Center da fase 8.

Players que anunciam MPRIS aparecem na ilha quando estão tocando em segundo plano ou em outro workspace. A capa e barras animadas aparecem no estado compacto; ao passar o cursor, aparecem título, artista e controles de play/pause, próxima e anterior, conforme as capacidades anunciadas pelo player. Ao pausar, os controles ficam disponíveis por mais 20 segundos para retomar. Se chegar uma notificação junto com a mídia, a bolha de notificação ocupa um espaço próprio ao lado da ilha. As barras indicam reprodução; ainda não são um medidor da amplitude real do áudio.

Para testar sem tocar som, execute `python3 ilha/tests/mock_mpris.py` a partir da pasta `~/.config/quickshell`. O script usa os bindings D-Bus do Python que já estavam disponíveis neste computador. Com a Ilha ativa, os comandos abaixo permitem verificar os controles; encerre o script de teste ao terminar:

```sh
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 getMedia
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 toggleMedia
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 nextMedia
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 previousMedia
```

Clique na ilha para abrir o seletor de temas. Os cards aplicam o tema com um clique, sem reiniciar. O painel também abre por comando, substituindo `eDP-1` pelo nome de outro monitor:

```sh
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 toggleThemes
```

No editor, clique numa amostra de cor para abrir o seletor visual, digite `#RRGGBB` ou use os controles HSV. As mudanças aparecem imediatamente na ilha e nas miniaturas dos painéis. **Salvar tema** cria uma cópia pessoal de um preset; se o tema atual já for pessoal, salva as alterações nele. **Descartar prévia** volta às cores salvas. Os cards pessoais podem ser duplicados ou apagados. Para importar ou exportar, informe o caminho completo do arquivo JSON; a exportação pede um nome de arquivo ainda não existente.

Os dez presets estão em `themes/*.json`. Temas pessoais e seleção atual são gravados em `~/.config/ilha/themes/` e `~/.config/ilha/config.json`. Os três ajustes globais — destaque, opacidade e intensidade de blur — ficam separados dos temas. O preset OLED força opacidade total e blur zero. O blur usa as regras `ilha-island` e `ilha-themes` em `~/.config/hypr/hyprland.lua`; a intensidade ajusta quanto do fundo desfocado fica visível. O raio do blur continua sendo a configuração global do Hyprland.

O alerta de contraste usa 4,5:1 como referência para texto normal e não impede salvar. A geração de cores a partir do wallpaper é opcional e ainda não foi implementada. Os controles de temas serão ligados ao Control Center e às Configurações quando esses painéis forem construídos.

Não há autostart ou atalho global nesta fase. O Hyprland recebeu somente as regras de blur dos namespaces da Ilha.
