# Dependências

`install.sh` e `install-system.sh` instalam somente o código. **`install-deps.sh` instala dependências apenas com `--apply` e confirmação no terminal**. Sem essa opção, consulta o banco local do pacman e apresenta uma prévia, sem rede ou alterações. Nenhuma imagem, fonte, ícone de terceiros ou senha do OBS é empacotada.

## Escolher módulos e revisar

```sh
./install-deps.sh --list
./install-deps.sh --profile minimal           # Base da Ilha
./install-deps.sh --profile desktop           # Padrão: controles, áudio, launcher e wallpapers
./install-deps.sh --profile full              # Acrescenta KDE Connect e FPS 64 bits
./install-deps.sh --profile full --json        # Mesma prévia em JSON

# Acrescentar recursos e apps opcionais, sem instalar ainda:
./install-deps.sh --profile full --modules fps32,steam,localsend,minecraft,vscodium

# Aplicar somente depois de revisar; rode como usuário, sem sudo:
./install-deps.sh --profile full --apply
```

`--modules` acrescenta à seleção do perfil; use `--profile minimal --modules phone` para base + celular. O módulo core sempre é incluído. `full` inclui os módulos do shell, não todos os aplicativos externos, ferramentas de teste ou jogos de 32 bits. Steam/FPS32 exigem multilib configurado em x86_64; se indisponível, o script informa a pendência sem editar pacman.conf.

O plano preserva dependências/provedores compatíveis já instalados, mostra pacotes oficiais e repositórios adicionais separadamente e respeita a prioridade do pacman. Na aplicação, mostra a transação resolvida com dependências antes da confirmação. No Arch usa `sudo pacman -S --needed`; se Omarchy estiver disponível, usa `omarchy pkg add` (esse comando usa `--noconfirm` internamente, portanto a confirmação da Ilha é a revisão anterior à instalação).

Não atualiza os bancos nem executa atualização geral. Use o procedimento normal da sua distribuição para manter o sistema e os bancos coerentes antes de instalar. Os pacotes solicitados podem exigir instalação/atualização de bibliotecas, conforme a transação mostrada. Se não houver pacote compatível ou houver outra pendência, bloqueia toda a aplicação antes de alterar pacotes.

## AUR e aplicativos opcionais

```sh
# Revisar a instalação de LocalSend quando não estiver nos repositórios configurados:
./install-deps.sh --profile minimal --modules localsend --allow-aur
# Aplicar exige confirmação geral, confirmação da etapa AUR e interação com o helper:
./install-deps.sh --profile minimal --modules localsend --allow-aur --apply
```

O AUR fica desativado por padrão. `--allow-aur` permite usar `yay` ou `paru` **já instalado**, como usuário, sem `--noconfirm`. `--aur-helper yay` ou `--aur-helper paru` escolhe explicitamente. O script não baixa, compila nem instala um helper por conta própria. Quando necessário inclui `base-devel` e `git` na transação dos repositórios, depois pede confirmação separada para revisar/instalar os PKGBUILDs pelo helper. Se você cancelar a etapa AUR, pacotes de repositório já instalados são mantidos.

Fallbacks de aplicativos: LocalSend → `localsend-bin`; VSCodium → `vscodium-bin`; VS Code → `visual-studio-code-bin`. A disponibilidade e a versão do AUR são verificadas pelo helper na execução, não pela prévia offline. Um CLI do editor já existente é preservado; o instalador não troca Code OSS por uma distribuição diferente. O pacote LocalSend escolhido precisa fornecer `localsend-cli` para atividades de transferências; a presença somente da GUI não garante esse recurso.

Referências: [LocalSend indica o pacote AUR](https://github.com/localsend/localsend#download), [VSCodium no Arch](https://vscodium.com/#install-on-arch-linux), [Quickshell no Arch oficial](https://archlinux.org/packages/extra/x86_64/quickshell/). O HyprMod segue sua instalação própria documentada em [Configurações](ilha/integrations/CONFIGURACOES.md); ele não é instalado por este catálogo.

## Depois dos pacotes

Execute `./install.sh` ou `sudo ./install-system.sh`. O comando `ilha-deps` fica disponível para revisões futuras com as mesmas opções de `install-deps.sh`. Se faltar Python para abrir os instaladores, instale-o primeiro com `sudo pacman -S --needed python`.

A instalação de pacotes não ativa NetworkManager, Bluetooth, PipeWire ou perfis de energia. Revise os serviços já usados antes de habilitar outro gerenciador. Permissões de brilho, suporte físico a bateria e integração com portais também dependem da sessão/hardware. O provedor estático awww/swww precisa de daemon configurado; a presença do Caelestia existente evita instalar um provedor redundante. Hyprlock/swaylock precisam da configuração de bloqueio do usuário. A extensão do editor é instalada separadamente com `ilha-editor --install codium` ou `--install code`.

## Catálogo de dependências

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
| Wallpaper animado nativo | `qt6-multimedia`, `qt6-multimedia-ffmpeg` e `ffmpeg` (ffprobe/miniaturas); sem mpvpaper |
| Bloqueio | Caelestia ativo; alternativamente `hyprlock` ou `swaylock` configurado |
| Preferência claro/escuro | `gsettings`/GSettings desktop schemas e portal do desktop; aplicativos precisam respeitar a preferência |
| Cores do terminal | Kitty, opcional; outros terminais não são modificados |
| FPS real em jogos iniciados pelo wrapper | `mangohud`; `lib32-mangohud` para jogos de 32 bits |
| Jogos Steam | `steam`, opcional; lê apenas bibliotecas locais inicializadas |
| Atividades de transferências | `localsend` com `localsend-cli` (validado 1.18.2), mais um terminal |
| Minecraft Java | `prismlauncher`, opcional; Java/mods continuam administrados pelo launcher |
| Atividades de terminal | Python 3 já exigido pelo shell; pacman/yay só quando escolhidos pelo usuário |
| Atividades de editor | VS Code ou VSCodium >= 1.93 já instalado e extensão local `bielodragon.ilha-activities`; empacotamento sem npm |

O HyprMod é opcional e não é instalado por estes scripts. O botão detecta `hyprmod` e avisa se estiver ausente. Consulte [o guia](ilha/integrations/CONFIGURACOES.md) antes de instalar.

O sistema de teste já tinha os pacotes básicos. Na expansão de 27/10/2026 o usuário autorizou a instalação de MangoHud e lib32-mangohud; foram instalados 0.8.4-1 com suas dependências oficiais. Na etapa do instalador, apenas prévias e testes em staging/processos simulados foram executados, sem instalar novos pacotes. Não houve teste em uma instalação Arch limpa nem execução real de transação AUR nesta etapa. Instalações globais ainda precisam dos serviços e permissões de sessão de cada usuário. Não execute o shell gráfico como root.
