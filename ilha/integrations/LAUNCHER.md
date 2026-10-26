# Lançador da Ilha — fase 10

Clique com o botão direito no **fundo da ilha** para abrir a pesquisa. Clique normal continua abrindo temas; puxar para baixo continua abrindo o Control Center. A combinação visual foi escolhida pelo usuário após a [comparação das referências](REFERENCIAS-LAUNCHER.md).

O painel cresce na posição da ilha, animando largura, altura e raio, e volta à geometria da pílula ao fechar. O conteúdo permanece durante a animação de saída e é descarregado depois. Relógio, workspaces compactos, privacidade/OBS e bateria do celular continuam disponíveis no cabeçalho, conforme os módulos habilitados.

## Modos de pesquisa

| Entrada | Resultado | Ação com Enter/clique |
| --- | --- | --- |
| Nome de aplicativo | Busca por nome, descrição e palavras-chave, aceitando acentos e correspondência aproximada | Abre o aplicativo |
| `= sqrt(144) + 2` | Resultado matemático local | Copia o resultado |
| `: trecho` | Filtra itens do histórico cliphist | Copia o item selecionado, incluindo imagens compatíveis |
| `>` | Wallpaper, claro/escuro, wallpaper aleatório, esquemas e bloqueio | Abre o seletor ou aplica a ação escolhida |
| `> wallpaper ` | Imagens de `~/Pictures/Wallpapers`, com miniaturas | Aplica a imagem escolhida |
| `> scheme ` | Temas prontos e personalizados, com amostras de cores | Aplica e salva o tema da Ilha |
| `> comando` sem ação correspondente | Mostra o comando como ação explícita | Executa em um terminal |

Também há botões Apps/Calculadora/Clipboard/Ações. Setas para cima/baixo e Tab/Shift+Tab selecionam os resultados; Escape, o × ou um clique fora fecham. O link **Temas** abre a aba com cards e editor já existentes nas Configurações.

As ações também aceitam buscas como `> light`, `> dark`, `> random`, `> schema` e `> lock`. Selecionar **Mudar wallpaper** ou **Mudar esquema de cores** apenas abre a respectiva lista; só o segundo Enter/clique aplica o item. A pasta de wallpapers é `~/Pictures/Wallpapers`, incluindo subpastas; não movemos, baixamos ou apagamos imagens existentes. Imagens grandes carregam miniaturas de forma assíncrona. Acrescente texto depois de `> wallpaper ` ou `> scheme ` para filtrar.

Neste computador, wallpaper e bloqueio usam o Caelestia instalado: `caelestia wallpaper -f <arquivo> -N` e `caelestia shell lock lock`. Nenhum shell é parado ou substituído. O `-N` preserva o modo claro/escuro do Caelestia, mas a rotina de wallpaper dele ainda atualiza suas cores e executa seus hooks já configurados. Claro/escuro e esquemas do menu alteram **os temas da Ilha**, persistidos pelo ThemeStore; a sincronização geral com outros aplicativos continua prevista para a fase 11. Sem o CLI do Caelestia, essas duas integrações exibem erro legível; ainda será necessário um provedor independente nos instaladores.

Referências de comportamento e interface de comandos: [Caelestia Shell](https://github.com/caelestia-dots/shell) e [CLI oficial](https://github.com/caelestia-dots/cli). Código próprio; nenhum trecho foi copiado.

Digitar uma pesquisa **não executa resultados**. Aplicativos, cópia e comandos só são ativados por Enter, clique ou IPC de ativação. As mensagens e os títulos são texto simples, sem interpretar marcação.

Aplicativos são indexados por `DesktopEntries.applications` do Quickshell instalado, com limite de 40 resultados. A abertura usa Gio para interpretar o arquivo `.desktop`, inclusive seu diretório e `Terminal=true`; a documentação do Quickshell 0.3.1 avisa que `DesktopEntry.execute()` ainda ignora Terminal e field codes. Não reconstruímos `Exec` como uma string de shell.

A calculadora aceita números com ponto decimal, parênteses, `+`, `-`, `*`, `/`, `//`, `%` (resto), `**`, `pi`, `e`, `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `abs` e `round`. Funções trigonométricas usam radianos. Expressões têm tamanho/complexidade limitados, sem avaliação de código Python. Não há conversão de unidades, moedas ou acesso à rede.

No modo de comandos, a confirmação abre `xdg-terminal-exec sh -lc <comando>`, com fallback para foot/kitty quando necessário. A interpretação pelo shell é específica desse modo, após confirmação do resultado; nomes de aplicativos e conteúdo de clipboard nunca viram comandos de shell. O terminal segue seu comportamento normal de saída após a conclusão do comando.

## Clipboard

O launcher usa o banco existente do `cliphist`, consultando até 60 prévias quando esse modo é aberto e filtrado. Os observadores `wl-paste --type text --watch cliphist store` e `wl-paste --type image --watch cliphist store` já estavam ativos neste computador. A Ilha **não iniciou observadores duplicados** e não alterou o banco pessoal nos testes.

Itens são recuperados pelo identificador numérico, passando o delimitador exigido pela versão instalada do `cliphist decode`, e copiados via `wl-copy`. Bytes e novas linhas são preservados. Itens maiores que 8 MiB não são copiados pelo helper. Os resultados são mantidos só para exibição/animação e descartados ao terminar o fechamento; não há novo histórico de pesquisas da Ilha.

Em uma instalação sem observador cliphist, o histórico ficará vazio/indisponível. Esse caso precisa ser tratado na integração de autostart/instaladores da fase 11, verificando processos existentes antes de criar um observador. Não habilitamos novos serviços nesta fase. Desativar o módulo do launcher não encerra observadores externos de clipboard.

## Módulo, monitor e IPC

Configurações → Módulos possui a opção **Lançador**, habilitada por padrão, com persistência no JSON. Desativar fecha a pesquisa e impede novas aberturas. Cada ilha abre o launcher no seu próprio monitor; a sessão usa uma pesquisa por vez.

```sh
/usr/bin/quickshell -c ilha ipc call ilha.eDP-1 openLauncher
/usr/bin/quickshell -c ilha ipc call launcher open eDP-1
/usr/bin/quickshell -c ilha ipc call launcher search '= 2+3*4'
/usr/bin/quickshell -c ilha ipc call launcher status
/usr/bin/quickshell -c ilha ipc call launcher close
```

Substitua `eDP-1` pelo monitor desejado. O comando da própria ilha captura sua geometria atual para o morph. No IPC global, monitor vazio usa a primeira tela disponível; monitor inexistente é informado sem criar uma superfície perdida. `launcher activate` confirma o resultado selecionado e pode abrir um aplicativo, copiar conteúdo ou executar o comando explicitamente pesquisado. O diagnóstico retorna modo, contagem, índice, estado e erros; não retorna o conteúdo do histórico pessoal.

**Super+Espaço** abre a pesquisa no monitor em foco, conforme solicitado pelo usuário. O primeiro vínculo usava `open_launcher.py`; na fase 11 passou a chamar `ilha launcher` pelo bloco gerenciado do Hyprland, com backup e unbind explícito do vínculo anterior. O comando consulta o monitor em foco e chama `ilha.<monitor>.openLauncher`, preservando o morph a partir da geometria atual. Ctrl+Super+Espaço foi preservado. [Atalhos, autostart e instaladores](INSTALACAO.md).

## Blur e composição

A regra Lua de blur foi estendida para incluir `launcher`, com backup antes da alteração:

```lua
hl.layer_rule({ match = { namespace = "ilha-(island|themes|notifications|control-center|launcher)" }, blur = true, ignore_alpha = 0.1 })
hl.layer_rule({ match = { namespace = "ilha-launcher" }, no_anim = true })
```

A segunda regra remove a animação extra do compositor **somente** nessa layer: o morph é feito pelo QML da Ilha, seguindo os tokens de animação, cores e opacidade atuais. OLED permanece sólido. O backup é `~/.config/hypr/hyprland.lua.bak.ilha-fase10-20261024-084150`; reload/configerrors foram validados sem erros.

## Testes

Na pasta `~/.config/quickshell`:

```sh
python3 -m unittest discover -s ilha/tests -q
node ilha/tests/test_launcher_search.cjs
python3 ilha/tests/check_launcher_integration.py
python3 ilha/tests/check_preferences_integration.py
```

Os 30 testes Python e os dois testes novos de busca passaram. A integração usa um `.desktop` de teste real que só grava um marcador temporário, banco cliphist privado, substitutos para wl-copy/terminal e QML real. Confere abertura do app, cálculo, clipboard byte a byte, execução somente na ativação e módulo desativado. Não executa comandos arbitrários nem usa o clipboard pessoal.

`check_launcher_desktop.py` é opt-in: usa a sessão real, sem executar/copiar resultados. Confere digitação, cálculo, navegação, Escape/retorno da ilha e capturas claro/OLED, restaurando o tema anterior no `finally`. Deve ser executado sem interação simultânea e sem editar os QML durante a rodada. O script verifica bloqueio antes de enviar teclas e interrompe se a sessão estiver bloqueada.

Nos testes foram corrigidas a ordem de atualização do modo antes de consultar a fonte, a tabulação exigida pelo cliphist e o fechamento com retenção de conteúdo/fallback de descarregamento. As capturas foram inspecionadas para busca, cálculo, claro, OLED e cabeçalho com workspaces/privacidade. Uma rodada foi interrompida pelo bloqueio da sessão; nenhuma senha foi submetida e não houve tentativa de desbloqueio.

Não houve instalação de pacotes, alteração/parada de outros shells ou acesso a APIs de mídia para simular apps. Segundo monitor físico, FPS e GPU híbrida NVIDIA ainda não foram medidos/testados. A validação de comandos usa um terminal de teste e a de clipboard usa banco privado; o uso com seu terminal/clipboard real pode ser conferido manualmente sem os testes alterarem seu conteúdo.

Referências técnicas: [DesktopEntries](https://quickshell.org/docs/v0.3.1/types/Quickshell/DesktopEntries/), [limitações de DesktopEntry.execute](https://quickshell.org/docs/v0.3.1/types/Quickshell/DesktopEntry/), [cliphist oficial](https://github.com/sentriz/cliphist) e [regras Lua de layers](https://wiki.hypr.land/Configuring/Basics/Window-Rules/#layer-rules).
