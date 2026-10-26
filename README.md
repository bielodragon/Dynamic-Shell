# Ilha

Shell de desktop em Quickshell para Hyprland: ilha animada, workspaces, notificações, mídia, atividades de desenvolvimento, privacidade/OBS, KDE Connect, Control Center, temas com editor e launcher.

Código próprio, com referências visuais documentadas em [comparação dos shells](ilha/integrations/REFERENCIAS-LAUNCHER.md). Testado em Arch Linux, Quickshell **0.3.1** e Hyprland **0.56.2/Lua**. [Dependências](DEPENDENCIAS.md) · [Uso completo](ilha/README.md) · [Instalação, reversão e limites](ilha/integrations/INSTALACAO.md).

## Instalar

Depois de baixar/clonar este repositório, escolha **uma** opção:

```sh
# Só para o usuário atual, sem sudo:
./install.sh

# Código disponível para todos os usuários:
sudo ./install-system.sh
```

Os scripts listam dependências, mas não instalam pacotes. Temas e configurações pessoais ficam separados em `~/.config/ilha/` e são preservados. A instalação global não altera os arquivos pessoais nem ativa sessões de outros usuários. Cada usuário revisa a integração com `ilha setup` e a aplica com `ilha setup --apply`.

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
