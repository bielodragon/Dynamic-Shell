# KDE Connect — fase 7

Integração escrita para as interfaces conferidas no KDE Connect **26.08.0** instalado. Não envia mensagens, solicita pareamento, ativa plugins ou altera o firewall. O observador só lê o D-Bus da sessão; não depende de comandos periódicos do `kdeconnect-cli`.

## O que funciona e o que a API permite

| Recurso | Suporte na Ilha |
| --- | --- |
| Bateria | Percentual e carregamento de celular/tablet pareado e alcançável; valor desconhecido aparece como `—`, nunca como 0% inventado |
| Vários celulares | Mostra um de cada vez; ao expandir, clique no nome para alternar. O contador indica os demais |
| Notificações | Título, aplicativo e texto em uma bolha; acompanha atualização e remoção, respeita notificações silenciosas e não perturbe |
| Chamadas | Contato/número recebido no evento; alerta temporário de chamada recebida ou perdida |
| Atender/recusar | Não disponível na interface D-Bus da versão conferida. Use o celular |
| Silenciar toque | O KDE Connect possui ação na notificação nativa, mas o método `sendMutePacket` é privado e não é exportado por D-Bus. A rota direta da Ilha não inventa esse botão |
| Fim da chamada | A interface `callReceived` não anuncia cancelamento/fim. Na rota direta, o alerta expira em 25 segundos ou pode ser fechado localmente; não representa uma chamada comprovadamente ainda tocando |

O indicador de bateria aparece na ilha de cada monitor; ao expandir, mostra o nome se não houver outras atividades exigindo espaço. A bolha usa o monitor focado e a superfície de notificações já existente, com cores exclusivamente do `Theme`.

## Duas rotas de notificação

Quando a Ilha possui `org.freedesktop.Notifications`, o KDE Connect já envia as notificações e chamadas ao servidor normal do shell. Essa rota preserva as ações e o fechamento que o próprio KDE Connect anunciar. O observador compara o PID do proprietário desse nome D-Bus com o processo da Ilha e desativa a bolha direta para não duplicar a entrega dentro da Ilha.

Quando outro shell possui esse nome, a Ilha acompanha os sinais D-Bus do KDE Connect e mostra sua própria bolha. Isso permite testar sem parar o Caelestia ou o Omarchy. O outro shell ainda pode mostrar sua própria notificação; não alteramos suas preferências. Na rota direta, fechar a bolha é uma ação **local**, não apaga a notificação no celular. Não há resposta de mensagens ou execução de ações remotas nessa rota.

Na rota direta, o alerta de chamada tem prioridade sobre uma notificação de celular, que por sua vez tem prioridade sobre notificações desktop enquanto a bolha estiver visível. Notificações de celular duram até oito segundos; chamadas, até 25 segundos. A desconexão do dispositivo remove as bolhas diretas e esconde sua bateria. Não reexibimos o histórico de notificações ao abrir o shell ou sair de não perturbe.

## Preparar um celular para o teste real

1. Abra o KDE Connect no celular e no computador, na mesma rede, e faça o pareamento pela interface do KDE Connect.
2. No celular, habilite os recursos e as permissões que quiser testar: bateria, acesso às notificações e, para identificação de chamadas, telefone/contatos conforme a plataforma permitir.
3. Confira os dispositivos e o diagnóstico da Ilha:

```sh
kdeconnect-cli --list-devices
/usr/bin/quickshell -c ilha ipc call phone status
```

4. Verifique a bateria, gere uma notificação no celular e receba uma chamada de teste. Expanda a bolha para ler o conteúdo. Atenda e encerre pelo próprio celular.

Se o aparelho não aparecer, resolva a descoberta/pareamento no KDE Connect primeiro. A Ilha não muda rede nem permissões automaticamente. Um daemon que já foi encerrado também não é autoativado pelo observador; ele acompanha a entrada/saída do serviço e tenta reconectar. Há reconciliação periódica a cada 30 segundos, além dos sinais de mudança.

## Prévia e verificações automatizadas

```sh
/usr/bin/quickshell -c ilha ipc call phone previewCall
/usr/bin/quickshell -c ilha ipc call phone endPreview
```

A prévia usa **Prévia · Celular**, dura 12 segundos e não liga para ninguém. Fica separada dos alertas reais e não os apaga. Para verificar a bolha, faça isso com a tela desbloqueada e ligada; não perturbe esconde a prévia como as demais bolhas.

Na pasta `~/.config/quickshell`:

```sh
python3 -m unittest discover -s ilha/tests -q
python3 ilha/tests/check_kdeconnect_integration.py
```

O teste de integração cria um barramento D-Bus **privado**, um serviço simulado e um ambiente QML sem janelas. Valida bateria, carregamento, título literal, atualização, remoção, chamada com contato, silêncio, DND, troca para entrega nativa sem duplicação, desconexão e encerramento do daemon. As configurações graváveis ficam num diretório temporário; o teste não usa o serviço KDE Connect real nem um celular.

Nesta etapa, o daemon real respondeu corretamente, mas não havia celulares e o usuário preferiu parear depois. Portanto, os recursos foram validados contra o serviço simulado, **não em um celular real**. A primeira captura com `grim` ficou esperando porque o monitor estava com DPMS desligado; foi encerrada sem desbloquear ou acender a tela. Durante a fase 8, a prévia compacta foi capturada com o monitor ligado e inspecionada: contato de teste legível, bolha ao lado da ilha. O visual da bateria e o funcionamento com um aparelho real continuam pendentes.

Dependências já instaladas: `kdeconnect`, `python-dbus` e `python-gobject`, além do Quickshell. Nenhum pacote extra foi instalado. Não houve alterações no Hyprland, no Caelestia ou no Omarchy.

## Fontes consultadas

Foram lidos os cabeçalhos e a implementação oficiais da versão instalada no GitLab do KDE, usando apenas os contratos das interfaces, sem copiar trechos de implementação. Os arquivos têm licença `GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL`.

- [Dispositivos e plugins disponíveis](https://invent.kde.org/network/kdeconnect-kde/-/blob/v26.08.0/core/device.h).
- [Bateria e sinal refreshed](https://invent.kde.org/network/kdeconnect-kde/-/blob/v26.08.0/plugins/battery/batteryplugin.h).
- [Chamadas: interface pública](https://invent.kde.org/network/kdeconnect-kde/-/blob/v26.08.0/plugins/telephony/telephonyplugin.h) e [eventos realmente emitidos](https://invent.kde.org/network/kdeconnect-kde/-/blob/v26.08.0/plugins/telephony/telephonyplugin.cpp).
- [Notificações e sinais](https://invent.kde.org/network/kdeconnect-kde/-/blob/v26.08.0/plugins/notifications/notificationsplugin.h) e [propriedades dos objetos](https://invent.kde.org/network/kdeconnect-kde/-/blob/v26.08.0/plugins/notifications/notification.h).

A introspecção XML do daemon instalado também foi conferida. O `busctl introspect` desta máquina rejeita métodos sobrecarregados duplicados do Qt; a leitura do XML bruto e as chamadas D-Bus com assinatura explícita funcionam.
