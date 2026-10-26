# Comparação de referências — fase 10

O usuário escolheu explicitamente **Combinação recomendada** antes da implementação: morph do Ukishima, organização de busca do Ambxst, continuidade das transições do Caelestia e cards de temas inspirados no Noctalia Quickshell. Todo código da Ilha foi escrito para este projeto; não foram copiados componentes, bibliotecas, imagens ou instaladores desses shells.

| Projeto | Pesquisa/launcher observado | Seleção de temas observada | Ideia aproveitada |
| --- | --- | --- | --- |
| Ambxst | Launcher compacto ligado ao notch, busca fuzzy, lista e modos por prefixo; composição cresce com os resultados | Editor amplo de cores/aparência e sistema de presets | Organizar a pesquisa e as fontes em uma área compacta e legível |
| Caelestia | Painel com busca, lista, foco e navegação por teclado; wrapper coordena deslocamento/opacidade e mantém conteúdo durante o fechamento | Schemes apresentados em linhas com nome/variante e amostra circular dividida | Continuidade de abertura/fechamento e seleção consistente por teclado |
| Ukishima | O launcher é uma superfície do corpo da pílula, com campo de busca acima da lista e dimensões associadas ao estado da própria ilha | Modos Light/Dark/Dynamic/Manual e ajustes próprios, em vez de uma grade de presets com cards grandes | Geometria da pesquisa crescendo a partir da ilha no mesmo centro visual |
| Noctalia Quickshell v4.7.7 | SmartPanel com núcleo de providers, lista/grade e prévia de clipboard | Grade de esquemas com nome, amostras de cores e destaque do selecionado | Manter cards com identidade da paleta e seleção evidente no editor já existente |

Minha avaliação foi que **Ukishima** combina mais diretamente com “pesquisa saindo da ilha”; **Noctalia Quickshell** combina melhor com “cards de pré-visualização”. Ambxst e Caelestia complementam a organização e o comportamento. Isso é uma escolha de design a partir da leitura das implementações, não uma alegação de que todos os projetos oferecem exatamente a mesma animação ou o mesmo seletor.

O endereço `noctalia-shell` atualmente redireciona para `noctalia`, cujo branch principal é uma implementação nativa Wayland/OpenGL ES, sem Qt. Para a comparação solicitada em Quickshell foi consultada separadamente a tag **v4.7.7**. Não se deve tratar o código C++ atual como documentação de tipos QML.

## Revisões e licenças conferidas

| Referência | Revisão consultada | Licença do repositório |
| --- | --- | --- |
| Ambxst | `37ee0fcd13c8bf6fd2498e5322a175ac4edbc48f` | AGPL-3.0 |
| Caelestia | `0b0beb520a36f6972999c2afc97b311a27ba87f0` e arquivos da instalação local | GPL-3.0 |
| Ukishima | `23bdfbef847fda75c6ed4b8bea1ecdc3592f68b1` | MIT |
| Noctalia Quickshell | v4.7.7, `3abfa1fc09b62dc4cdeeb7b787886f075696f0b7` | MIT |
| Noctalia nativo atual | `5f90509b7d0a4bc0c2c6d124cc0bf9ec101909c5` | MIT |

Fontes principais: [Ambxst LauncherView](https://github.com/Axenide/Ambxst/blob/37ee0fcd13c8bf6fd2498e5322a175ac4edbc48f/modules/widgets/launcher/LauncherView.qml), [notch Ambxst](https://github.com/Axenide/Ambxst/blob/37ee0fcd13c8bf6fd2498e5322a175ac4edbc48f/modules/notch/Notch.qml), [Caelestia Wrapper](https://github.com/caelestia-dots/shell/blob/0b0beb520a36f6972999c2afc97b311a27ba87f0/modules/launcher/Wrapper.qml), [Caelestia SchemeItem](https://github.com/caelestia-dots/shell/blob/0b0beb520a36f6972999c2afc97b311a27ba87f0/modules/launcher/items/SchemeItem.qml), [Ukishima Pill](https://github.com/amanhex/Ukishima/blob/23bdfbef847fda75c6ed4b8bea1ecdc3592f68b1/Pill.qml), [Ukishima Launcher](https://github.com/amanhex/Ukishima/blob/23bdfbef847fda75c6ed4b8bea1ecdc3592f68b1/surfaces/Launcher.qml), [Ukishima ThemeSurface](https://github.com/amanhex/Ukishima/blob/23bdfbef847fda75c6ed4b8bea1ecdc3592f68b1/surfaces/ThemeSurface.qml), [Noctalia Launcher QML](https://github.com/noctalia-dev/noctalia/blob/3abfa1fc09b62dc4cdeeb7b787886f075696f0b7/Modules/Panels/Launcher/Launcher.qml) e [cards Noctalia QML](https://github.com/noctalia-dev/noctalia/blob/3abfa1fc09b62dc4cdeeb7b787886f075696f0b7/Modules/Panels/Settings/Tabs/ColorScheme/ColorsSubTab.qml).
