# Wallpaper animado nativo

Vídeos e GIFs são reproduzidos dentro da Ilha com **Qt Multimedia/AnimatedImage**. Não é necessário mpvpaper, não há servidor externo nem processo de player para gerenciar. Qt Multimedia, seu backend FFmpeg e ffmpeg já estavam instalados na máquina de teste; esta etapa não instalou pacotes.

## Escolher

Coloque os arquivos em **`~/Pictures/Wallpapers`**, incluindo subpastas. Formatos reconhecidos: GIF, MP4, WebM, MKV, MOV e M4V. A extensão não garante que o codec seja compatível; o arquivo é validado com ffprobe, e erros de reprodução aparecem na aba Wallpapers.

- Abra Configurações → **Wallpapers** ou use o botão **Wallpapers** no Control Center.
- Digite o caminho de um GIF/vídeo e clique em **Aplicar GIF/vídeo**.
- Alternativamente, abra **Super+Espaço**, digite `> wallpaper ` e selecione o arquivo. A lista identifica vídeos/GIFs; vídeos passam a ter miniatura em cache após a primeira seleção.
- **Pausar/Retomar** guarda a preferência. **Desativar fundo animado** descarrega o player e revela o fundo do provedor anterior.

O arquivo selecionado e as opções ficam em `~/.config/ilha/config.json`, grupo `wallpaper`. A seleção volta na próxima inicialização. Wallpaper associado a um tema também aceita GIF/vídeo pela integração já existente; a sincronização de wallpaper por tema continua opt-in. Escolher uma imagem estática pelo launcher usa o provedor estático existente e desativa o fundo animado após a aplicação bem-sucedida.

## Reprodução e recursos

São criadas superfícies independentes por monitor, carregadas sob demanda. O vídeo é recortado preservando a proporção para preencher a tela, repete em loop e não emite áudio. GIF usa cache de quadros desativado para evitar guardar animações inteiras na memória. A Ilha não muda GPU, driver, clocks ou configuração global de decodificação.

Pausas automáticas, ligadas por padrão e configuráveis separadamente:

| Opção | Condição |
| --- | --- |
| Na bateria | A bateria do computador está descarregando; retoma quando carrega ou não está na bateria. |
| Em tela cheia | Há aplicativo/jogo em tela cheia naquele monitor; os demais monitores continuam independentes. |
| No modo desempenho | O modo desempenho da Ilha está ativo; retoma quando desligado. |

Pausa manual continua valendo quando uma condição automática termina. Leituras de bateria seguem o serviço do dispositivo, com seu intervalo de atualização. Vídeos de alta resolução, GIFs grandes e múltiplos monitores aumentam o custo de decodificação; o FPS da fonte é preservado, sem promessa de 60 fps em qualquer arquivo/hardware.

Não há suporte a projetos/cenas interativas do Wallpaper Engine. Os formatos desta etapa são arquivos locais de vídeo/GIF. Miniaturas usam `~/.cache/ilha/wallpapers`; não são adicionadas ao repositório. Fontes remotas e arquivos fora de Pictures/Wallpapers, inclusive links que escapam dessa pasta, não são aceitos.

## Convivência com outros shells

A superfície `ilha-wallpaper` fica no layer **Bottom**, acima do fundo do Caelestia atual (Background), abaixo das janelas e sem região de entrada. O Caelestia continua rodando; seus arquivos, wallpaper estático, bloqueio e notificações não são alterados pela reprodução animada. Não há script para matar outro provedor. Ao desativar ou encerrar a Ilha, a superfície desaparece e o fundo de baixo reaparece.

Se outro ambiente já renderizar seu desktop no layer Bottom, será preciso revisar a ordem das superfícies antes de trocar de provedor. Essa arquitetura foi validada em Hyprland; não é um plugin de wallpaper do KDE Plasma. A instalação global apenas disponibiliza o código e mantém configurações por usuário.

## Controle por IPC

```sh
/usr/bin/quickshell -c ilha ipc call wallpaper status
/usr/bin/quickshell -c ilha ipc call wallpaper select "$HOME/Pictures/Wallpapers/animacao.mp4"
/usr/bin/quickshell -c ilha ipc call wallpaper pause true
/usr/bin/quickshell -c ilha ipc call wallpaper pause false
/usr/bin/quickshell -c ilha ipc call wallpaper stop
```

`select` retorna um identificador e inicia validação/carregamento assíncronos; `status` informa busy, ready e message. O backend do launcher aguarda a prontidão e apresenta o erro quando necessário. A configuração é gravada pela fila única do ThemeStore, e prévias do editor não alteram esse grupo. Mudar/pausar o fundo não reaplica automaticamente o wallpaper associado ao tema; selecionar o tema explicitamente pode reaplicá-lo.

## Validação

- **51 testes Python e 3 testes JS** passaram. Cobertura inclui restrição de caminhos, symlinks, arquivos inválidos, módulo ausente, persistência atômica e associação de vídeo a tema.
- `check_wallpaper_integration.py`: instância privada com Qt Multimedia real, vídeo com espaço/# no nome, GIF, pausa/retomada, bateria simulada e descarregamento. Janela offscreen é usada porque PanelWindow/layer-shell exige compositor Wayland; não confundir esse teste com a camada real.
- `check_wallpaper_desktop.py`: opt-in. Gera padrões próprios pequenos, abre área de trabalho vazia, verifica vídeo/GIF reais, pausa manual, pausa por desempenho e tela cheia com janela de terminal própria. Restaura opções/workspace e encerra/remove somente recursos de teste. Não mexe em wallpapers pessoais.
- Regressões do launcher e das preferências QML passaram. Capturas reais de vídeo/GIF e da aba Wallpapers foram inspecionadas: fundo preenchido, ilha e cantos acima dele e controles legíveis. Preferências anteriores e wallpaper original restaurados. Corrigida uma mensagem falsa de erro ao limpar a fonte durante o descarregamento.
- Não houve teste físico com dois monitores, notebook na bateria, NVIDIA, vídeos 4K/60 fps ou todas as combinações de codecs. O teste usou padrões de baixa resolução a 8 fps para validar reprodução e ciclo de vida.

Fontes primárias: [MediaPlayer](https://doc.qt.io/qt-6/qml-qtmultimedia-mediaplayer.html), [AnimatedImage](https://doc.qt.io/qt-6/qml-qtquick-animatedimage.html), [VideoOutput](https://doc.qt.io/qt-6/qml-qtmultimedia-videooutput.html), [LazyLoader Quickshell](https://quickshell.org/docs/v0.3.2/types/Quickshell/LazyLoader/) e [Toplevel](https://quickshell.org/docs/v0.3.2/types/Quickshell.Wayland/Toplevel/). Código próprio, sem cópia de implementação desses projetos.
