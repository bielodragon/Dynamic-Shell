# Configurações da Ilha — fase 9

Abra **Configurações** no Control Center. A janela tem três abas:

- **Módulos**: relógio, workspaces, notificações do desktop, mídia, atividades de desenvolvimento, privacidade/gravação e KDE Connect.
- **Aparência**: animações, duração das transições, opacidade, intensidade do vidro desfocado e estilo/quantidade de workspaces.
- **Temas e cores**: o mesmo editor do painel de temas, com cards, presets protegidos, temas pessoais, HSV/hex, contraste, duplicação, exclusão, importação e exportação.

As alterações de preferências são aplicadas e salvas automaticamente. Alterações do editor de temas mantêm o fluxo de prévia e **Salvar tema**. Fechar/descartar uma prévia restaura o tema salvo. A janela é carregada sob demanda e pode ser fechada pelo botão, Escape ou comando normal do compositor. Ela usa uma superfície normal de aplicativo, sem novas regras do Hyprland.

## Persistência e efeitos

O arquivo continua sendo `~/.config/ilha/config.json` (ou o diretório XDG configurado). As operações usam a fila de `ThemeStore` e gravação atômica. Preferências antigas são mantidas, e arquivos sem as chaves novas recebem os defaults em memória. As chaves são mescladas; salvar um módulo não sobrescreve a seleção/overrides de tema, outros módulos ou campos adicionais.

```json
{
  "modules": {
    "clock": true,
    "workspaces": true,
    "notifications": true,
    "media": true,
    "activities": true,
    "privacy": true,
    "phone": true
  },
  "animations": {"enabled": true, "scale": 1.0}
}
```

`animations.scale` aceita de 0,5 a 2, como multiplicador de duração. Desativar animações zera as durações e interrompe barras decorativas/progresso animado; a animação spring da ilha também fica desativada. Os tempos e as cores continuam centralizados no `Theme`.

O módulo de privacidade para seus observadores PipeWire e OBS, sem parar gravações ou capturas dos aplicativos. KDE Connect para apenas o observador da Ilha, sem desconectar ou desparear o celular. Notificações descarrega o servidor da Ilha; servidores de outros shells não são parados. Atividades rejeita novas atualizações por IPC enquanto desativado e limpa os indicadores pendentes. Mídia esconde seus componentes e controles, preservando os players externos. Relógio e workspaces controlam a exibição; workspaces desativado também bloqueia a navegação por roda/IPC da Ilha.

A ilha e o Control Center permanecem acessíveis, permitindo reativar os módulos. Os módulos carregam habilitados por padrão. Os dados de atividades/notificações descartados ao desligar não são recuperados ao religar.

O blur continua sendo efeito global do Hyprland limitado às layers da Ilha. A intensidade ajusta quanto fundo desfocado aparece; não muda o raio global. OLED mantém opacidade sólida e blur zero, mesmo com overrides salvos. Nenhuma preferência de GPU/NVIDIA ou regra do compositor é alterada por esta janela.

## HyprMod

O botão executa o comando `hyprmod` encontrado no PATH. Nesta máquina ele já estava instalado em `~/.local/bin/hyprmod`, com ambiente `uv` em `~/.local/share/uv/tools/hyprmod`. Não houve instalação nem atualização nesta fase.

Se o comando não existir, o painel mostra um aviso. Se ele falhar logo ao iniciar, a Ilha informa a falha e guarda detalhes em `~/.cache/ilha/hyprmod.log`. O botão não instala dependências e não salva configurações do Hyprland por conta própria. As mudanças feitas dentro do HyprMod são responsabilidade do próprio app.

O [README atual](https://github.com/BlueManCZ/hyprmod#readme) já apresenta outras formas de distribuição, incluindo AUR; isso difere do estado descrito no pedido original. A forma com checkout e `uv` solicitada pelo usuário também está documentada no [guia oficial de desenvolvimento](https://github.com/BlueManCZ/hyprmod/blob/main/CONTRIBUTING.md):

```sh
git clone https://github.com/BlueManCZ/hyprmod.git
cd hyprmod
uv sync
uv run hyprmod
```

Esses comandos **não foram executados**. Caso uma instalação por checkout seja necessária no futuro, primeiro conferir Python 3.12+, GTK4/libadwaita e dependências de introspecção da distribuição, listar o que faltar e confirmar a instalação. Para o botão continuar abrindo pelo nome `hyprmod`, será necessário expor esse comando no PATH do usuário apontando para o checkout/ambiente escolhido. Não substituir automaticamente a instalação já existente.

## Comandos e testes

```sh
/usr/bin/quickshell -c ilha ipc call settings open modules
/usr/bin/quickshell -c ilha ipc call settings open appearance
/usr/bin/quickshell -c ilha ipc call settings open themes
/usr/bin/quickshell -c ilha ipc call settings status
/usr/bin/quickshell -c ilha ipc call settings close
```

Na pasta `~/.config/quickshell`:

```sh
python3 -m unittest discover -s ilha/tests -q
python3 ilha/tests/check_preferences_integration.py
python3 ilha/tests/check_obs_integration.py
python3 ilha/tests/check_kdeconnect_integration.py
```

Foram aprovados 25 testes unitários e o teste de preferências QML/JSON temporário, que desliga/religa módulos, confere processos observadores parados/reiniciados, persistência e durações de animação sem reiniciar o shell. Os testes isolados de OBS e KDE Connect também passaram após integrar as preferências. O caso HyprMod ausente é validado sem instalar ou executar o aplicativo.

Foram inspecionadas capturas de Módulos, Aparência e Temas: texto legível, controles alinhados e editor compartilhado com espaço e rolagem para os tokens. A detecção da instalação HyprMod foi conferida; sua abertura pelo botão ainda precisa de teste manual. Não houve alterações na configuração pessoal do usuário durante os testes automatizados, instalação de pacotes ou alteração de arquivos do Hyprland.
