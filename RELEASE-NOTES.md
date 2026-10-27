# Distribuição da expansão — 27/10/2026

Inclui o shell das fases 1–11 e as seis etapas da expansão: compatibilidade gráfica opcional, bateria/desempenho/métricas, wallpaper animado nativo, catálogos e atividades de apps/jogos, terminal/editores e instalação de dependências.

Novidades de distribuição: `install-deps.sh`/`ilha-deps`, perfis minimal/desktop/full, seleção de módulos, identificação de provedores/repositórios, confirmação antes da instalação e AUR separado como usuário. Os dois instaladores de código fazem backup e preservam preferências. O pacote é gerado do commit com SHA-256; [instruções para GitHub](GITHUB.md).

## Uso rápido

- **Super+Espaço** abre a pesquisa; `>` oferece ações, wallpapers, temas, Steam, LocalSend e Minecraft Java.
- Wallpapers em `~/Pictures/Wallpapers`, incluindo GIF/vídeo, com pausas configuráveis.
- Desempenho, métricas e FPS são controles separados; FPS real exige jogos iniciados com MangoHud pelo wrapper.
- `ilha-run -- comando` mostra atividade de terminal; `ilha-editor --install codium|code` instala a extensão local de tarefas/depuração/terminal.

## Validação e limites

Testado em Arch/Omarchy, Quickshell 0.3.1/0.3.2 e Hyprland 0.56.2/Lua. Migração `.conf`/versões antigas precisa de revisão das regras; os dois escopos de instalação foram testados em staging, não em uma nova instalação Arch ou como instalação global real. O instalador de dependências foi testado com prévias reais e execução simulada das transações, sem instalar pacotes só para testar.

Os testes automatizados e nativos por recurso estão nos guias em `ilha/integrations/`. VSCodium foi testado com tarefas, código de erro, terminal integrado e depuração sintética; VS Code Microsoft não estava instalado. Sem leitura de comandos/logs privados pelos adapters do editor/terminal. Pacman/yay não mostram porcentagem inventada.

Ainda dependem de teste manual: download Steam real, transferência LocalSend entre dispositivos, Minecraft real, celular KDE Connect pareado, OBS autenticado conforme os guias e uso prolongado dos ajustes gráficos em Plasma/Hyprland. LocalSend GUI não expõe progresso ao adapter; use o CLI integrado. Atender chamadas do celular depende do que o KDE Connect oferece.

Não há benchmark garantindo 60 fps, teste físico de múltiplos monitores, bateria de notebook ou GPU híbrida NVIDIA. O hardware de teste era Intel Sandy Bridge/Radeon Whistler sem bateria. Nenhum driver, seleção de GPU, serviço do sistema ou ajuste gráfico global é aplicado pelos instaladores. A correção gráfica opcional não é executada automaticamente.

Caelestia e Omarchy continuam instalados. Wallpaper, bloqueio, servidor de notificações e barras concorrentes precisam da escolha/configuração de sessão descrita nos guias; o instalador não encerra outros shells automaticamente. A sincronização externa de temas começa desligada.
