# Dependências

Os instaladores **não executam pacman, AUR helpers nem downloads**. Revise os pacotes e escolha o que instalar. Nenhuma imagem, fonte, ícone de terceiros ou senha do OBS é empacotada.

| Uso | Necessário |
| --- | --- |
| Shell | Arch Linux/Wayland, Hyprland, `quickshell >= 0.3.1`, `python` |
| Serviço OBS em QML | `qt6-websockets` |
| Controles/KDE Connect e abertura de apps | `python-dbus`, `python-gobject` |
| Ícones Nerd Font | JetBrainsMono Nerd Font, como `ttf-jetbrains-mono-nerd` ou sua variante `-basic` |
| Capturas e testes visuais | `grim`, opcionalmente `wtype`; não necessários para executar a Ilha |
| Testes JS | Node.js; não necessário para executar o shell |
| Histórico | `wl-clipboard`, `cliphist`; `ilha start` reutiliza observadores existentes |
| Áudio e privacidade | PipeWire; `wireplumber` fornece `wpctl` |
| Rede/Bluetooth | NetworkManager (`nmcli`), BlueZ (`bluez-utils`) |
| Brilho/perfis | `brightnessctl`, `power-profiles-daemon`, quando suportados pelo hardware |
| Telefone | KDE Connect, com aparelho pareado pelo próprio usuário |
| Wallpaper | Caelestia ativo; alternativamente um daemon `awww`/`swww` já configurado e iniciado |
| Bloqueio | Caelestia ativo; alternativamente `hyprlock` ou `swaylock` configurado |
| Preferência claro/escuro | `gsettings`/GSettings desktop schemas e portal do desktop; aplicativos precisam respeitar a preferência |
| Cores do terminal | Kitty, opcional; outros terminais não são modificados |

O HyprMod é opcional e não é instalado por estes scripts. O botão detecta `hyprmod` e avisa se estiver ausente. Consulte [o guia](ilha/integrations/CONFIGURACOES.md) antes de instalar.

O sistema de teste já tinha os pacotes básicos; esta fase não instalou pacotes. Instalações globais ainda precisam dos serviços e permissões de sessão de cada usuário. Não execute o shell gráfico como root.
