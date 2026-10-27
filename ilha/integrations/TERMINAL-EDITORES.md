# Terminal, pacman/yay, VS Code e VSCodium

## Terminal externo

Use `ilha-run -- comando argumentos` para acompanhar um comando na Ilha. Funciona com qualquer terminal/shell que consiga executar programas; não troca seu shell, não instala aliases e não altera `.bashrc`, `.zshrc` ou configurações do Fish.

```sh
# Consulta local inofensiva, sem instalar pacotes:
ilha-run -- pacman -Q pacman

# Exemplos para quando você decidir instalar/atualizar:
ilha-run -- sudo pacman -S nome-do-pacote
ilha-run -- yay -S nome-do-pacote

# Qualquer build ou processo explícito:
ilha-run -- make
ilha-run --title "Compilação do projeto" -- cargo build
```

O wrapper roda como usuário. Quando necessário, `sudo` vem **depois** de `--`, junto do comando. A entrada, a saída e o erro são herdados diretamente pelo processo: o wrapper não lê senhas, prompts, logs ou argumentos para compor atividades. A Ilha mostra execução, sucesso, erro ou interrupção conforme o código de saída. Ctrl+C do terminal continua interrompendo o processo e o wrapper devolve 130 quando apropriado.

**Progresso indeterminado:** não há porcentagem de download, pacotes restantes ou reconhecimento da fase atual de pacman/yay. O wrapper não interpreta sua saída e não faz varredura de outros terminais/processos. Um `pacman`/`yay` iniciado sem `ilha-run` não gera essa atividade automaticamente. Use o terminal original para responder confirmações e ver detalhes da operação.

Argumentos são passados como uma lista, sem shell implícito. Para pipelines, a execução de um shell precisa ser explícita, por exemplo `ilha-run -- bash -lc 'comando1 | comando2'`; o código final será o desse shell, com a semântica de pipeline dele. Comandos que se desacoplam em segundo plano só são acompanhados até o processo inicial terminar. Em `--title`, use apenas texto que deseja exibir na tela.

Sem a Ilha aberta, o comando continua funcionando. Os eventos são locais, efêmeros e não impedem a execução se o shell estiver indisponível. O código de saída original é preservado.

## Editores

A extensão **Ilha — Atividades**, ID `bielodragon.ilha-activities`, acompanha:

- tarefas e builds iniciados pelo sistema de tarefas do editor;
- sessões de depuração, usando início/encerramento, sem inspecionar o protocolo do debugger;
- comandos do terminal integrado quando o shell integration do editor estiver ativo.

Não lê `commandLine`, stdout, task definitions, nomes de arquivos/projetos, configurações de depuração nem variáveis privadas. Usa títulos genéricos e não mostra porcentagem. Sucesso/erro exige código de saída; depuração encerrada e tarefas sem código não são declaradas bem-sucedidas. Não é um indicador de toda ação interna do editor: salvar, autocomplete, Git em background e downloads de extensões não são observados.

```sh
# Gerar apenas o VSIX local:
ilha-editor

# Instalar no perfil padrão de um editor já instalado:
ilha-editor --install codium
ilha-editor --install code
```

O pacote é feito com a biblioteca padrão do Python, sem npm ou downloads, e salvo em `$XDG_CACHE_HOME/ilha/extensions`. O instalador geral da Ilha cria o comando `ilha-editor`, mas não instala a extensão silenciosamente em todos os perfis. O comando `--install` instala/atualiza somente essa extensão local no editor escolhido. Em outros perfis, use **Extensions: Install from VSIX** e selecione o arquivo gerado.

Recarregue a janela do editor após instalar. Na paleta de comandos, execute **Ilha: mostrar atividade de teste**. Depois use **Terminal → Executar Tarefa**, uma depuração ou um terminal com shell integration. Se não aparecer, consulte o canal **Ilha** na aba Output. Veja [configurações e limites da extensão](vscode/README.md).

Precisa de VS Code/VSCodium desktop >= 1.93 e Python 3. Não instala o VS Code se ele estiver ausente. A extensão é local/UI; não é instalada em servidores remotos nem em navegadores. Não funciona em workspaces não confiáveis; não mude a confiança de um projeto desconhecido apenas para habilitá-la. Nenhum `tasks.json` ou `launch.json` é modificado.

## Desativar e reverter

Em **Configurações → Módulos → Atividades integradas**, Terminal e VS Code/VSCodium têm controles separados, persistidos no grupo `integrations`. Desligar o módulo geral de atividades esconde todas as fontes. Isso não cancela comandos, tarefas ou depurações.

No editor, use `ilhaActivities.enabled:false` ou desative/desinstale a extensão. `ilhaActivities.terminal:false` impede a observação de novos comandos integrados. Para instalações em caminho personalizado, defina `ilhaActivities.bridgePath` no escopo do usuário. Preferências da extensão são de aplicação; workspaces não escolhem o programa da ponte.

## Validação

Testes cobrem passagem direta de stdin/stdout/stderr e exit7, ausência de conteúdo privado nos eventos, Ctrl+C em PTY e exit130, protocolo NDJSON sem execução de comandos, códigos finais/desconexão, filtros e remoção dos eventos QML, limite de atividades e empacotamento XML/VSIX. Testes JS usam objetos que lançam erro se o adapter tentar ler nomes/comandos/logs.

VSCodium 1.143 instalado nesta máquina: VSIX aceito em perfil temporário, tarefa real concluída, tarefa com exit7, terminal Bash com shell integration e sessão de depuração com adaptador sintético validados. Capturas `/tmp/ilha-editor-tarefa.png` e `/tmp/ilha-terminal-atividade.png` mostram as atividades na Ilha; comando externo também foi acompanhado até a conclusão. Consulta real `ilha-run -- pacman -Q pacman` passou; nenhum pacote foi instalado/atualizado para testar pacman/yay. VS Code não estava instalado; compatibilidade usa a mesma API pública, mas não foi testada no binário Microsoft.

Referências oficiais: [eventos da API VS Code](https://code.visualstudio.com/api/references/vscode-api), [manifesto de extensão](https://code.visualstudio.com/api/references/extension-manifest), [shell integration](https://code.visualstudio.com/docs/terminal/shell-integration) e [pacman](https://man.archlinux.org/man/pacman.8). Nomes/tipos também conferidos no `vscode.d.ts` do VSCodium instalado. Código próprio, sem trechos copiados de outras extensões.
