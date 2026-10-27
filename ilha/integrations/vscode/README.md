# Ilha — Atividades para VS Code e VSCodium

Extensão local para o shell Ilha, sem serviços externos, telemetria ou dependências npm. Compatível com VS Code/VSCodium desktop >= 1.93; precisa de Python 3 e da Ilha instalada no mesmo usuário. Não é uma extensão publicada no Marketplace ou Open VSX.

Observa tarefas/builds, sessões de depuração e comandos de terminais com shell integration. Títulos genéricos: nenhum comando, log, nome de projeto, caminho, configuração de debug ou argumento é transmitido. A ponte Python envia eventos locais efêmeros para o observador da Ilha. A saída original dos programas continua no editor.

Instale pelo repositório da Ilha:

```sh
python3 ilha/scripts/editor_extension.py --install codium
# Ou, se o VS Code estiver instalado:
python3 ilha/scripts/editor_extension.py --install code
```

Recarregue a janela do editor para ativar. Na paleta de comandos, **Ilha: mostrar atividade de teste** apresenta uma tarefa de prévia por cinco segundos. Depois execute uma tarefa real pelo menu Terminal → Executar Tarefa, ou inicie uma depuração. Os comandos do terminal integrado só geram eventos se o shell integration do editor estiver ativo; nenhum shell ou arquivo de inicialização é alterado pela extensão.

Configurações do usuário: `ilhaActivities.enabled`, `ilhaActivities.terminal` e `ilhaActivities.bridgePath` (opcional, caminho completo de `scripts/ide_activity_bridge.py`). São opções de aplicação; um workspace não escolhe o programa da ponte. Em workspaces não confiáveis a extensão fica desativada. Execute localmente: ambientes web/VS Code Server isolados não são suportados como host da ponte.

Sem porcentagem inventada. Tarefas e comandos recebem sucesso/erro quando há código de saída. Depuração encerrada e tarefas sem código de saída são mostradas sem afirmar sucesso. Ao fechar o editor, a ponte finaliza atividades como estado desconhecido; se ela for morta, os eventos expiram. A extensão não pausa, cancela nem inicia suas tarefas por conta própria.

Desative nas extensões do editor ou com `ilhaActivities.enabled:false`. O controle **VS Code / VSCodium** em Configurações → Módulos da Ilha também oculta essas atividades. Para remover, desinstale `bielodragon.ilha-activities` pelo editor. Nada é alterado em `tasks.json`, `launch.json`, perfis gráficos ou configurações de outros shells.
