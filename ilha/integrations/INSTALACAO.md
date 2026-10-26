# Instalação, integração e reversão

## Dois escopos

`./install.sh` copia `ilha/` para `$XDG_CONFIG_HOME/quickshell/ilha` (padrão `~/.config/quickshell/ilha`) e cria `ilha`/`ilha-activity` em `~/.local/bin`. Executar do próprio destino não recopia nem remove o código.

`sudo ./install-system.sh` instala o código em `/etc/xdg/quickshell/ilha` e os comandos em `/usr/local/bin`. Nenhum diretório pessoal é escrito como root e nenhum autostart global é imposto. Cada usuário habilita sua integração com `ilha setup --apply`. Configurações pessoais de Quickshell têm precedência sobre `/etc/xdg`; mantenha apenas a versão que pretende executar, fazendo backup antes de mover a anterior.

Atualizações fazem backup do código anterior e dos comandos substituídos. Nunca sobrescrevem `~/.config/ilha/config.json`, seus temas, imagens, configurações do OBS ou aplicativos de desenvolvimento. `--destdir` redireciona toda a instalação para staging e desativa interação/ativação; wrappers apontam para o destino final, para empacotamento. `--dry-run` não grava nada.

## Hyprland

`ilha setup` mostra o bloco completo sem gravar. `ilha setup --apply` faz backup, acrescenta um bloco delimitado, recarrega e verifica `hyprctl configerrors`. Em caso de erro de validação, restaura o backup e recarrega novamente. Reaplicar substitui o próprio bloco, sem acumular autostarts.

Atalhos: Super+Espaço para launcher, Ctrl+Super+I para a ilha e Ctrl+Shift+Super+I para o shell inteiro. Super+Espaço substitui explicitamente o vínculo anterior com `hl.unbind`. Os atalhos com I precisam estar livres. Na máquina de desenvolvimento não havia vínculo anterior para esses dois atalhos.

Lua usa `hl.on("hyprland.start", ...)`, equivalente ao propósito de exec-once. Configuração antiga `.conf` recebe `exec-once` e binds de hyprlang; só o caminho Lua 0.56.2 foi validado em compositor real. O bloco Lua também inclui as regras de blur/no_anim nos namespaces exclusivos da Ilha; o blur global precisa estar habilitado no compositor. Em versões antigas, confira manualmente as regras da documentação daquela versão antes de ativar o vidro.

`ilha reload` encerra e inicia somente a Ilha; atividades temporárias são perdidas. O comando tem trava para chamadas simultâneas e usa `-n` para evitar instâncias duplicadas. `ilha island-toggle` guarda a visibilidade sem parar observadores/notificações. O launcher e Configurações podem reabrir o shell se ele estiver parado.

`ilha start` inicia observadores de cliphist somente quando não encontra `wl-paste` do usuário; observadores compartilhados continuam independentes do ciclo da Ilha e não são encerrados por `ilha stop`.

## Convivência

Os instaladores detectam Caelestia, Omarchy, Waybar, mako e dunst ativos. No modo interativo por usuário, perguntam se você deseja habilitar a Ilha e, no caso do Caelestia, ocultar somente a barra/sidebar dele. O modo não interativo nunca faz essa troca. A instalação global apenas disponibiliza o código; cada usuário faz a revisão na própria sessão.

`ilha bars` mostra a alteração proposta. `ilha bars --hide` faz backup de `~/.config/caelestia/shell.json`, salva os campos anteriores e altera somente `bar.excludedScreens` para `["^.*$"]` e `sidebar.enabled` para false. O Caelestia requer âncoras para interpretar esse filtro como expressão regular. Wallpaper, bloqueio, notificações, frame e processo continuam ativos; não se perde o atalho alternativo dele. `ilha bars --restore` restaura apenas os campos alterados, preservando outros ajustes. Se esses campos forem editados manualmente depois, a restauração para para evitar sobrescrevê-los; use o backup para uma revisão manual.

Há apenas um servidor `org.freedesktop.Notifications` por sessão. Ocultar a barra não transfere esse serviço para a Ilha. Para uma troca completa de shell, decida também o provedor de wallpaper/bloqueio e o autostart concorrente. Nenhum instalador encerra ou desinstala Caelestia/Omarchy por conta própria. KDE Connect pode mostrar notificações pelos dois shells enquanto coexistirem.

## Sincronização opcional

Começa **desligada**, por integração, em Configurações → Aparência. Usa temas salvos e o destaque global; prévias do editor não alteram aplicativos externos. Falhas aparecem nas configurações e em `quickshell -c ilha ipc call theme-sync status`.

| Opção | Efeito e limite |
| --- | --- |
| Preferência claro/escuro | `gsettings set org.gnome.desktop.interface color-scheme prefer-dark/prefer-light`. Qt precisa respeitar o portal; não impõe um estilo Qt nem reescreve qt5ct/qt6ct. |
| Kitty | Gera `~/.config/ilha/kitty-colors.conf`, com cores derivadas dos tokens, e inclui no `kitty.conf` com backup. Não ativa remote control. Recarregue janelas existentes pelo mecanismo do Kitty. Links de configuração são materializados como arquivo pessoal; seus destinos não são escritos. |
| Bordas | `hyprctl keyword` para active_border/inactive_border; outro gerenciador pode reaplicar cores. Nenhuma regra NVIDIA/monitor/driver é alterada. |
| Wallpaper | Associe uma imagem existente de `~/Pictures/Wallpapers` ao tema atual. Aplicação pelo provedor disponível; o CLI Caelestia pode atualizar também suas próprias cores/hooks. Sem provedor, a Ilha informa o erro. |

Desligar uma integração impede sincronizações futuras; não restaura automaticamente o valor externo anterior. Restaure o backup do Kitty ou use seu tema anterior do desktop. Limpar a associação com caminho vazio deixa o wallpaper atual intacto.

Cantos arredondados são quatro superfícies pequenas por monitor, estáticas e sem região de entrada, controladas por tokens do Theme. Raio de 1–48 e ativação ficam em Aparência. Hot corners são um extra opcional ainda não implementado.

## Reverter e publicar

1. Execute `ilha bars --restore` se ocultou a barra do Caelestia.
2. Execute `ilha stop`.
3. Remova apenas o bloco entre `-- >>> ilha >>>` e `-- <<< ilha <<<` de `hyprland.lua` (ou os marcadores com `#` em `.conf`), após backup, e recarregue. O backup original completo também fica ao lado do arquivo; não o restaure cegamente se houve outras edições depois.
4. Remova os comandos/cópias do código somente quando decidir desinstalar. Seus temas pessoais ficam em `~/.config/ilha/` para backup/reutilização.

O arquivo de distribuição em `dist/` é gerado com `git archive`, incluindo apenas arquivos versionados e respeitando `.gitattributes`. O checkpoint local `RETOMADA.md` é excluído da distribuição. Nenhum wallpaper pessoal, token, senha, histórico de clipboard ou screenshot é incluído. O repositório remoto não é criado nem recebe push automaticamente.

Referências: [autostart Hyprland](https://wiki.hypr.land/Configuring/Basics/Autostart/), [regras de layers](https://wiki.hypr.land/configuring/core/rules/layer-rules/), [Quickshell PanelWindow 0.3.1](https://quickshell.org/docs/v0.3.1/types/Quickshell/PanelWindow/), [Kitty](https://sw.kovidgoyal.net/kitty/remote-control/) e [Caelestia](https://github.com/caelestia-dots/shell).
