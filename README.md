# Ilha

Shell de desktop em Quickshell para Hyprland: ilha animada, workspaces, notificações, mídia, atividades de desenvolvimento, privacidade/OBS, KDE Connect, Control Center, temas com editor e launcher.

Código próprio, com referências visuais documentadas em [comparação dos shells](ilha/integrations/REFERENCIAS-LAUNCHER.md). Testado em Arch Linux, Quickshell **0.3.1/0.3.2** e Hyprland **0.56.2/Lua**. [Dependências](DEPENDENCIAS.md) · [Uso completo](ilha/README.md) · [Instalação, reversão e limites](ilha/integrations/INSTALACAO.md).

Esta distribuição inclui bateria na ilha, desempenho/métricas, wallpaper animado, Steam/LocalSend/Minecraft Java, terminal e editores, além do instalador de dependências. [Notas e limites da versão](RELEASE-NOTES.md) · [Histórico das etapas](ilha/integrations/EXPANSAO.md).

No código atual, bateria condicional e os controles separados de desempenho, métricas e FPS já estão disponíveis. Para FPS real, inicie jogos com `ilha-game -- programa` (ou `--opengl -- programa`). [Uso, dependências e limites](ilha/integrations/MONITORAMENTO.md).

Wallpapers animados já funcionam pelo Qt Multimedia: coloque vídeos/GIFs em `~/Pictures/Wallpapers` e escolha em **Configurações → Wallpapers** ou na pesquisa `> wallpaper `. Há pausa manual e automática por bateria, tela cheia e desempenho. [Funcionamento e testes](ilha/integrations/WALLPAPERS.md).

Steam, LocalSend e Minecraft Java já têm catálogos na pesquisa `>` e adaptadores de atividades. Use `ilha-localsend` para transferências com progresso; instâncias do Prism podem usar `ilha-minecraft`. [Como ativar, testar e desfazer](ilha/integrations/APPS-JOGOS.md). O progresso da GUI do LocalSend não é observado.

Terminal e editores: `ilha-run -- comando` acompanha execução e término, incluindo pacman/yay. A extensão local de VS Code/VSCodium acompanha tarefas, depuração e terminal integrado. Instale em um editor existente com `ilha-editor --install codium` ou `--install code`. [Uso, privacidade e testes](ilha/integrations/TERMINAL-EDITORES.md).

## Instalar

Depois de baixar/clonar este repositório, revise as dependências e escolha **uma** opção de instalação:

```sh
# Prévia de dependências; só instala se acrescentar --apply e confirmar:
./install-deps.sh --profile full

# Só para o usuário atual, sem sudo:
./install.sh

# Código disponível para todos os usuários:
sudo ./install-system.sh
```

Os instaladores de código preservam temas e configurações em `~/.config/ilha/`. O script separado `install-deps.sh` tem perfis, seleção de módulos, prévia e confirmação; AUR exige `--allow-aur` e nunca roda como root. [Opções e serviços a configurar](DEPENDENCIAS.md). A instalação global não ativa sessões de outros usuários. Cada usuário revisa a integração com `ilha setup` e a aplica com `ilha setup --apply`.

No instalador por usuário, a ativação é perguntada depois de mostrar a configuração. Shells concorrentes são identificados; você escolhe se quer usar a Ilha e ocultar a barra/sidebar do Caelestia. Nenhum shell é removido ou encerrado automaticamente. `--non-interactive` apenas instala; `--dry-run` mostra os caminhos; `--destdir /tmp/pacote` permite testar sem tocar na sessão.

Se `ilha` não estiver no PATH, use `~/.local/bin/ilha` ou abra outro terminal. Uma instalação pessoal em `~/.config/quickshell/ilha` tem prioridade sobre a global.

## Usar

- **Super+Espaço:** pesquisa. Digite `>` para ações, `=` para calcular ou `:` para clipboard.
- **Ctrl+Super+I:** ocultar/mostrar a ilha.
- **Ctrl+Shift+Super+I:** ligar/desligar o shell inteiro.
- Puxar a ilha para baixo abre o Control Center. Clique normal abre temas; botão direito abre pesquisa.

```sh
ilha start
ilha stop
ilha reload
ilha settings
ilha status
```

Wallpapers: `~/Pictures/Wallpapers`. As opções de sincronização com GTK/Qt, Kitty, bordas e wallpaper por tema ficam em Configurações → Aparência e começam desligadas. [O que cada integração altera](ilha/integrations/INSTALACAO.md).

Para reexibir a barra/sidebar do Caelestia: `ilha bars --restore`. Para testar sem ativar a integração, execute `/usr/bin/quickshell -c ilha`.

## Desenvolvimento

```sh
python3 -m unittest discover -s ilha/tests -q
node ilha/tests/test_launcher_search.cjs
python3 ilha/tests/check_preferences_integration.py
python3 ilha/tests/check_launcher_integration.py
```

Os testes de integração usam configurações temporárias. Testes com nome `desktop` podem interagir com a sessão e devem ser executados explicitamente. OBS, celular real, múltiplos monitores e GPU NVIDIA têm limites de validação descritos nos guias; não há medição automática de 60 fps.

Licença MIT para o código deste repositório. Fontes, ícones, imagens e os programas integrados são fornecidos separadamente por seus respectivos projetos.

## GitHub e pacote

Envie o conteúdo da pasta extraída como código do repositório. O `.tar.gz` e seu `.sha256` podem ser anexados a uma Release. [Como preparar e conferir](GITHUB.md). Nenhum remoto é criado e nenhum arquivo é publicado automaticamente.
