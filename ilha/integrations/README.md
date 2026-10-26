# Atividades de programas — fase 5

O serviço recebe atividades por IPC do Quickshell. Os adaptadores abaixo enviam estados do ciclo de uma resposta. Claude Code e OpenCode não fornecem uma porcentagem confiável de conclusão global; por isso, usam progresso indeterminado.

## Qualquer programa

Com a Ilha aberta, execute:

```sh
~/.config/quickshell/ilha/scripts/ilha-activity update build:meu-projeto \
  --title "Compilando projeto" --app Build --state running --progress 42
~/.config/quickshell/ilha/scripts/ilha-activity update build:meu-projeto \
  --state waiting --detail "Aguardando confirmação" --indeterminate
~/.config/quickshell/ilha/scripts/ilha-activity done build:meu-projeto
~/.config/quickshell/ilha/scripts/ilha-activity list
~/.config/quickshell/ilha/scripts/ilha-activity remove build:meu-projeto
```

Reutilize o identificador para atualizar, sem duplicar. Estados: `running`, `waiting`, `paused`, `success` e `error`. `--progress` aceita 0–100; `--indeterminate` limpa a porcentagem. `--ttl` controla a expiração em segundos (1–86400): padrão de uma hora para estados em andamento e oito segundos para estados finais. Programas longos devem renovar a atividade antes de expirar. Atividades são temporárias e desaparecem quando a Ilha reinicia.

Há limite de 16 atividades simultâneas. Clique no título ou no contador para alternar entre elas. O × remove o indicador quando só há uma atividade; não encerra o programa. Cores vêm do Theme. Os workspaces se compactam durante a atividade e voltam ao formato completo no hover.

A CLI `send` lê um objeto JSON de stdin. O esquema é:

```json
{
  "id": "build:meu-projeto",
  "title": "Compilando projeto",
  "app": "Build",
  "detail": "Compilação local",
  "state": "running",
  "progress": 42,
  "ttl": 3600
}
```

`id` e `title` são necessários ao criar; atualizações podem omitir os demais campos. `progress: null` representa duração desconhecida. O IPC direto é `quickshell -c ilha ipc call activities update '<JSON>'`; os métodos `list` e `remove <id>` estão no mesmo alvo. A CLI usa `/usr/bin/quickshell` neste computador, pois o primeiro Quickshell do PATH pertence ao Caelestia. `ILHA_QUICKSHELL` e `ILHA_CONFIG` permitem ajustar executável e configuração.

## Claude Code

O hook `scripts/claude_activity.py` lê o JSON oficial de stdin e traduz:

| Evento | Resultado |
| --- | --- |
| UserPromptSubmit / PreToolUse / PostToolUse | Trabalhando |
| PermissionRequest / Notification permission_prompt | Aguardando você |
| Stop | Resposta pronta |
| StopFailure | Erro |
| SessionEnd | Remove a atividade da sessão |

O identificador deriva da sessão e do agente. O hook não envia o prompt, a resposta ou os argumentos dos comandos à ilha. Se a Ilha estiver fechada, ele termina silenciosamente com sucesso e não modifica decisões de permissão.

Para ativar:

1. Faça backup de `~/.claude/settings.json`, se existir.
2. Abra o fragmento `integrations/claude-hooks.json`.
3. Acrescente os itens de cada evento à lista correspondente em `hooks` no seu settings. Preserve os hooks que já existirem; não substitua o arquivo inteiro pelo fragmento.
4. Inicie uma nova sessão e confira a configuração em `/hooks`.
5. Com a Ilha aberta, envie uma mensagem e confira os estados de trabalho e conclusão.

Os comandos do fragmento apontam para a configuração deste usuário. Se mudar o local de instalação, ajuste os caminhos.

Nesta máquina, o comando `claude --version` passou por um wrapper do mise que tentou buscar o executável; a consulta não concluiu. Não foi instalado pacote extra. O script foi testado com entradas do protocolo entregues ao IPC real, mas falta validar a ativação numa sessão do próprio Claude Code.

Referências: [hooks oficiais](https://code.claude.com/docs/en/hooks), [configuração dos hooks](https://code.claude.com/docs/en/hooks#configuration).

## OpenCode 2

Foi detectado `opencode v2.0.20`. O adaptador `integrations/opencode-v2/` usa a definição `id/setup` e a assinatura `ctx.event.subscribe` da v2. A configuração usa **plugins**, no plural.

Ele observa `session.execution.started/succeeded/failed/interrupted`, `session.step.started`, `session.tool.called`, `session.retry.scheduled`, `permission.asked/replied` e `session.deleted`. Os dados da sessão vêm de `event.data.sessionID`. Eventos de texto/transcrições são ignorados. Ao descarregar o plugin, as atividades acompanhadas são removidas.

Para ativar, acrescente a pasta ao array `plugins` do seu `~/.config/opencode/opencode.json(c)`, preservando os itens existentes:

```json
{
  "plugins": [
    "/home/gabriel/.config/quickshell/ilha/integrations/opencode-v2"
  ]
}
```

Ajuste o caminho se instalar em outro usuário. O adaptador é local e não tem dependências npm. Ele usa o Python e o Quickshell existentes para enviar atividades. O processo do OpenCode precisa ter acesso à mesma sessão de usuário/Wayland da Ilha.

Inicie uma nova sessão do OpenCode e confira o plugin na lista de plugins ativos. Teste um pedido, uma solicitação de permissão e a conclusão. Para desativar, remova só o item da Ilha do array e reinicie/recarregue o aplicativo.

O teste automatizado simulou o contexto público do plugin e entregou eventos ao serviço real da Ilha, incluindo a limpeza ao descarregar. A configuração do seu OpenCode não foi alterada; falta validar o plugin dentro do host após ativá-lo. Não usar este adaptador como plugin da v1.

Referências: [plugins v2](https://dev.opencode.ai/v2/docs/build/plugins/), [ativação](https://dev.opencode.ai/v2/docs/plugins), [eventos oficiais de sessão](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/session-event.ts), [eventos de permissão](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/permission.ts).

## Validação de desenvolvimento

Na pasta `~/.config/quickshell`:

```sh
node ilha/tests/test_activity_model.cjs
python3 -m unittest discover -s ilha/tests -q
```

Com uma única instância da Ilha aberta e acesso ao IPC da sessão:

```sh
python3 ilha/tests/check_activity_ipc.py
node ilha/tests/check_opencode_adapter.mjs
```

Os testes de integração só removem os identificadores que criaram.
