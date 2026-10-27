# Steam, LocalSend e Minecraft Java

Abra a pesquisa com **Super+Espaço**, digite `>` e escolha Steam, LocalSend ou Minecraft Java. Enter abre o catálogo; outro Enter abre o item selecionado. Também é possível filtrar diretamente com `> steam nome`, `> minecraft nome` ou `> localsend LocalSend`.

Em **Configurações → Módulos → Atividades integradas**, cada fonte pode ser desligada separadamente. O módulo **Atividades de aplicativos** desliga todas as atividades, inclusive as de desenvolvimento; os atalhos continuam disponíveis. Preferências ficam em `~/.config/ilha/config.json`, grupo `integrations`.

## Steam

O catálogo lê os `appmanifest_*.acf` das bibliotecas locais e abre jogos com `steam://rungameid/ID`. Não consulta contas nem a biblioteca remota. Uma Steam ainda não inicializada só apresenta o atalho para abrir o cliente. Metadados de instalação podem incluir jogos em transferência; a própria Steam decide como abrir o jogo selecionado.

Downloads aparecem quando **BytesDownloaded realmente aumenta**, com o cliente Steam ativo. A porcentagem é dos bytes de `BytesToDownload`, não da descompressão, atualização em disco ou instalação completa. Se os contadores pararem por 15 segundos, a atividade desaparece. O formato desses arquivos é interno da Steam e pode mudar; não se usa StateFlags para inventar progresso.

Para mostrar um jogo em execução e permitir o controle de FPS da Ilha, coloque nas **opções de inicialização do jogo na Steam**:

```sh
ilha-game -- %command%
# Jogos OpenGL que precisem de interposição:
ilha-game --opengl -- %command%
```

Isso exige MangoHud e a variável SteamAppId fornecida pela Steam. Nenhuma opção de jogo é modificada automaticamente. Ao remover o wrapper dessas opções, volta a execução anterior. Jogos iniciados sem wrapper não têm detecção garantida. [FPS e métricas](MONITORAMENTO.md).

## LocalSend

O catálogo oferece o aplicativo gráfico e **Transferências na Ilha — LocalSend CLI**. O segundo abre um terminal com `ilha-localsend`, que envolve o `localsend-cli` oficial. A GUI continua independente: **seu progresso não é observado**.

```sh
ilha-localsend
ilha-localsend -f "$HOME/Downloads/arquivo.zip"
ilha-localsend --help
```

No CLI 1.18.2, `D` mostra dispositivos, os números escolhem o destino e `Y/N/P` aceitam, recusam ou aceitam e pareiam pedidos. Ctrl+C cancela ou sai. Todas essas escolhas continuam manuais; a Ilha não injeta respostas. Use os controles do próprio CLI para escolher os arquivos e o destino.

O CLI apresenta contadores arredondados, então a porcentagem na Ilha é **aproximada**. Envio e recebimento podem gerar atividades separadas. Somente mensagens explícitas de conclusão geram sucesso; sair com código zero não prova que um arquivo chegou. Falha/cancelamento tem estado próprio. Nomes de arquivos, dispositivos, chaves e saída bruta não são guardados nos eventos.

## Minecraft Java / Prism Launcher

O catálogo descobre as instâncias do Prism e usa `prismlauncher --dir RAIZ --launch PASTA`. O wrapper não altera Java, mods, contas ou parâmetros do jogo. Em outros launchers, é possível chamar `ilha-minecraft -- comando-java ...` quando houver suporte a wrapper.

Para integrar uma instância do Prism:

```sh
ilha-apps list minecraft
# Copie o id da instância desejada; primeiro revise:
ilha-apps setup-minecraft ID
ilha-apps setup-minecraft ID --apply
```

O comando cria backup de `instance.cfg`, ativa OverrideCommands e define WrapperCommand para `ilha-minecraft`. Recusa comandos personalizados existentes em vez de substituí-los. Só configura a instância indicada e não inicia o jogo. Para desfazer, feche a instância e restaure o backup informado, ou remova o wrapper nos comandos personalizados do Prism. Não restaure um backup antigo por cima de modificações posteriores sem revisá-las.

A Ilha acompanha inicialização, execução, alguns marcos conhecidos do log (recursos, cliente, conexão, mundo local) e encerramento. Não inventa porcentagem nem mostra chat/endereço do servidor. A saída original continua chegando ao Prism; apenas os eventos da Ilha são filtrados. Para FPS opcional, altere o wrapper no Prism para `ilha-minecraft --fps`; exige MangoHud. O instalador não configura todas as instâncias automaticamente.

## Dependências, testes e limites

São opcionais `steam`, `localsend` com `localsend-cli`, `prismlauncher` e um terminal (`xdg-terminal-exec`, Foot ou Kitty). Nesta máquina já estavam instalados; nenhum pacote foi adicionado nesta etapa. O shell gráfico continua sendo executado pelo usuário, nunca como root.

Eventos efêmeros próprios ficam em `$XDG_RUNTIME_DIR/ilha/app-activities`; expiram e são ignorados quando o processo termina sem enviar um estado final. Observação em processo separado, a cada dois segundos. Os wrappers continuam executando seus programas mesmo sem a Ilha aberta.

Validados: parser VDF, catálogo, argumentos de abertura sem shell, backup/conflito do Prism, contadores, leitura fragmentada do CLI, remoção/expiração de eventos, wrapper Java e códigos de saída, LocalSend interativo em PTY com programa sintético e serviço QML privado. Teste nativo com prévias identificadas e pesquisa real, sem jogos nem transferências. Ainda precisam de validação pelo usuário: download Steam real, transferência entre dispositivos e sessão real do Minecraft. Não foi encontrado catálogo Steam inicializado nesta máquina durante o desenvolvimento.

Referências de API/formato, sem copiar código: [comandos personalizados do Prism](https://prismlauncher.org/wiki/help-pages/custom-commands/), [CLI do Prism](https://www.prismlauncher.org/wiki/getting-started/command-line-interface/), [LocalSend 1.18.2 e seu CLI](https://github.com/localsend/localsend/tree/v1.18.2/cli) e [protocolo Steam](https://developer.valvesoftware.com/wiki/Steam_browser_protocol). Os formatos de texto do LocalSend e metadados Steam podem exigir adaptação em versões futuras.
