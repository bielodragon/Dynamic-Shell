# Privacidade e gravação — fase 6

A ilha mostra pontos para microfone (`Theme.warning`), câmera (`Theme.success`) e tela (`Theme.accent`). Ao expandir, aparecem os rótulos. As cores acompanham o tema; não são uma paleta fixa. A captura fica visível mesmo com não perturbe ativado e com mídia ou atividades de desenvolvimento na ilha. Os indicadores se repetem nos monitores porque a captura pertence à sessão, não a um workspace.

`privacy_monitor.py` mantém uma conexão `pw-dump -m -N` e acompanha eventos do grafo, sem ler áudio, imagens ou conteúdo compartilhado. Um dispositivo disponível, mas suspenso, não acende o indicador. O microfone exige uma fonte de áudio em execução conectada a uma entrada de captura ativa; monitor de saída não conta como microfone. Fontes de vídeo em execução são classificadas por metadados: câmera, tela/portal ou vídeo de origem não identificada. Este último recebe o rótulo **Vídeo**, sem adivinhar a origem. Remoção de objetos e mudanças parciais são aplicadas ao grafo em memória.

Se o observador desconectar, aparece um ponto de erro e, na expansão, **PipeWire indisponível**. Ele tenta reconectar a cada três segundos. Ausência de dados não deve ser apresentada como certeza de que não há captura.

## OBS

No OBS, abra **Ferramentas → Configurações do servidor WebSocket**, ative o servidor e mantenha a autenticação. O OBS instalado neste computador já inclui esse recurso. A Ilha usa somente `GetRecordStatus`, conectado a `127.0.0.1`, e não inicia, pausa ou para gravações. Lê o estado e a duração do OBS a cada segundo e também reage a eventos de mudança de gravação. A bolha mostra o tempo; ao expandir, mostra **Gravando** ou **Pausa**. A contagem respeita a duração fornecida pelo OBS, inclusive depois de conectar a uma gravação já em andamento.

A configuração é lida de `$XDG_CONFIG_HOME/obs-studio/plugin_config/obs-websocket/config.json`, normalmente `~/.config/obs-studio/plugin_config/obs-websocket/config.json`. O helper Python calcula a resposta SHA-256 ao desafio de autenticação. A senha não é copiada para o repositório, passada na linha de comando ou enviada ao QML. Para OBS com configuração portátil ou Flatpak, `ILHA_OBS_CONFIG` pode apontar para o arquivo de configuração correspondente antes de iniciar a Ilha. A porta é lida desse arquivo; o endereço continua restrito ao loopback.

Com WebSocket desativado, OBS fechado, autenticação recusada ou perda de conexão, o estado fica indisponível e a Ilha não afirma que há gravação. Isso não significa que o OBS parou de gravar. Consulte `available` pelo IPC para distinguir indisponibilidade de OBS conectado e ocioso. A leitura da configuração e as tentativas de conexão se repetem a cada cinco segundos; não é preciso reiniciar a Ilha ao ativar o servidor.

Dependências usadas: Python padrão, `pw-dump` do PipeWire e módulo QML `QtWebSockets` (`qt6-websockets` no Arch). Todos já estavam instalados; nenhum pacote foi instalado nesta fase.

## Conferir e testar

```sh
/usr/bin/quickshell -c ilha ipc call privacy status
```

O JSON separa o grafo PipeWire, o sinalizador de prévia e os campos OBS `enabled`, `available`, `recording`, `paused`, `durationMs`.

Uma prévia explícita de doze segundos mostra os três indicadores com o rótulo **Prévia**, sem alterar os dados reais ou ligar dispositivos:

```sh
/usr/bin/quickshell -c ilha ipc call privacy previewIndicators
/usr/bin/quickshell -c ilha ipc call privacy endPreview
```

Teste manual: abra um aplicativo que capture pelo PipeWire, observe os indicadores e feche a captura para conferir a remoção. No OBS, grave por alguns segundos, pause, retome e pare; a bolha deve acompanhar os estados. O shell não faz essas ações por conta própria.

Verificações automatizadas, a partir de `~/.config/quickshell`:

```sh
python3 -m unittest discover -s ilha/tests -q
python3 ilha/tests/check_obs_integration.py
```

O segundo comando cria um servidor WebSocket simulado somente em loopback e um ambiente QML temporário. Confere autenticação, início, pausa, retomada, parada e desconexão usando o `ObsState.qml` real. Não modifica nem controla o OBS pessoal, e encerra seus processos ao terminar.

Nesta máquina foram observadas capturas reais de câmera FaceTime, entrada de áudio e tela pelo portal Hyprland, além da conexão autenticada ao OBS. Os estados de gravação foram validados automaticamente com o servidor simulado; a validação manual de gravação real é separada.

## Limites

- Aplicativos que acessam V4L2/ALSA diretamente, sem publicar a captura no PipeWire, não são cobertos. O indicador não é uma garantia de ausência de captura no computador inteiro.
- Fontes virtuais podem representar captura de áudio sem um microfone físico. A indicação informa a entrada em uso no grafo, não prova qual dispositivo físico está por trás de filtros.
- Captura de tela fora do PipeWire também não é detectada. Metadados de produtores desconhecidos podem resultar no indicador genérico **Vídeo**.
- A bolha OBS representa gravação normal, não transmissão ao vivo, câmera virtual ou replay buffer. OBS apenas aberto não significa gravando.
- Múltiplos monitores usam o mesmo estado global; ainda falta teste físico com dois monitores. Não foi medido FPS nesta fase.

Referências de implementação, sem copiar código: [pw-dump](https://pipewire.pages.freedesktop.org/pipewire/page_man_pw-dump_1.html), [propriedades do PipeWire](https://github.com/PipeWire/pipewire/blob/master/doc/dox/config/pipewire-props.7.md), [protocolo OBS WebSocket](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md) e [WebSocket QML do Qt](https://doc.qt.io/qt-6/qml-qtwebsockets-websocket.html). Tipos QtWebSockets também foram conferidos nos metadados QML instalados.
