# Wi-Fi, Bluetooth e atualização da Ilha

## Wi-Fi

No Control Center, clique no card **Wi-Fi** para abrir a lista. O botão **Ligar/Desligar** fica dentro do painel. Use **Atualizar redes**, selecione uma rede, informe a senha quando necessária e clique em **Conectar**. A rolagem vai até as ações da rede selecionada.

Campo vazio em uma rede salva reutiliza o perfil existente, sem consultar/exibir a senha armazenada. Uma rede conectada oferece **Desconectar**. **Esquecer** exige confirmação e remove perfis compatíveis daquele SSID/dispositivo; pode desconectar. Ethernet não é desligada pelo botão de uma rede Wi-Fi.

Redes abertas, OWE, WPA pessoal e WPA3-SAE podem receber perfil novo. **Salvar nova conexão** escolhe entre persistência pelo NetworkManager e conexão temporária até desconectar. Essa opção não modifica um perfil salvo já existente. Informar outra senha em vez de reutilizar o perfil cria uma conexão nova do usuário, preservando os perfis anteriores.

WEP e redes empresariais 802.1X usam perfis previamente configurados no NetworkManager; o painel não edita certificados/EAP. SSIDs ocultos sem nome conhecido não são listados. As redes indicam a interface quando há vários adaptadores.

Senhas passam ao backend por stdin e ao NetworkManager por D-Bus, sem shell, argumentos de processo ou logs. O campo é limpo ao enviar/fechar. O backend não consulta GetSecrets e o JSON da Ilha não guarda senhas. A persistência escolhida é responsabilidade do NetworkManager.

## Bluetooth

Clique no card **Bluetooth**. **Buscar dispositivos** inicia descoberta da Ilha por até 30 segundos. Fechar/voltar encerra somente a sessão de descoberta pertencente à Ilha.

Selecione um dispositivo para **Parear e conectar**, **Conectar**, **Desconectar**, **Confiar/Não confiar**, **Bloquear/Desbloquear** ou **Esquecer** (com confirmação). O pareamento mostra código ou solicita PIN/passkey conforme o dispositivo. Para teclados, digite o código exibido no próprio teclado quando necessário. **Cancelar** cancela o pareamento iniciado pela Ilha.

O agente atende apenas os pareamentos dessa aplicação, sem substituir o agente padrão do BlueZ. Pedidos de outros dispositivos são recusados. Bateria aparece quando o BlueZ fornece org.bluez.Battery1; nem todo dispositivo oferece bateria ou perfis compatíveis.

Os painéis respeitam o modo avião gerenciado pela Ilha. Bloqueio físico/rfkill, serviços parados e permissões/Polkit podem impedir operações. A Ilha não habilita serviços nem altera outros shells para contornar isso.

## `ilha update`

```sh
ilha update --check   # Consulta a última release estável, sem instalar
ilha update           # Pede confirmação e instala com backup
```

Usa as releases públicas de **bielodragon/Dynamic-Shell**, sem exigir GitHub CLI/login. Baixa o tar.gz e checksum, verifica SHA-256, limita tamanhos e rejeita caminhos/links inválidos antes de executar o instalador da release. Não usa git reset nem instala pacotes de sistema. Revise novas dependências com `ilha-deps` quando necessário.

O escopo é preservado: pessoal continua pessoal; global usa sudo apenas para o instalador global. Execute como usuário. Preferências, temas e credenciais continuam fora do código. Os backups `.bak.ilha-*` ficam ao lado do código/comandos; preserve-os para restauração se instalação ou reload falhar. **Não há rollback automático.** Se a Ilha estava aberta, recarrega somente ela após instalar; se estava fechada, mantém fechada.

O recibo `.ilha-install.json` registra tag e escopo, sem credenciais. Instalações antigas sem recibo podem reinstalar a última versão uma vez para registrar a tag.

**Checkouts Git e diretórios dentro de repositórios são protegidos contra sobrescrita.** `--check` funciona neles, mas a atualização deve seguir o fluxo Git do desenvolvedor. Isso inclui este computador em `~/.config/quickshell`; a proteção evita substituir trabalho local por uma release anterior. Estes recursos novos só ficarão disponíveis por atualização pública depois de publicados em outra release; durante o teste, a release consultada era v1.1.0.

## Validação e limites

NetworkManager 1.58.1, BlueZ 5.87 e Quickshell 0.3.2 conferidos; nenhum pacote extra instalado. APIs verificadas na [documentação do NetworkManager](https://networkmanager.dev/docs/api/latest/) e nas interfaces [Agent](https://github.com/bluez/bluez/blob/master/doc/org.bluez.Agent.rst) e [Device](https://github.com/bluez/bluez/blob/master/doc/org.bluez.Device.rst) do BlueZ.

Testes cobrem segurança da rede, perfil do usuário, confirmação/PIN, descoberta própria, desconexão restrita ao AP selecionado, reutilização de perfil e proteção para esquecer. Painel QML privado com dispositivos sintéticos validou senha por stdin/campo limpo e confirmação de pareamento.

Teste nativo leu adaptadores e capturou os painéis sem buscar/conectar/desconectar/parear dispositivos pessoais. Capturas `/tmp/ilha-conectividade-wifi.png` e `/tmp/ilha-conectividade-bluetooth.png`, logs sem erros após correções. Conexão real, senha incorreta, pareamento físico, 802.1X e múltiplos adaptadores ainda precisam de validação manual.

Atualizador validado com consulta real à release, checksum/path traversal e implantação temporária usando o instalador real: backup, preferências preservadas e recibo. Não aplicada atualização real sobre o checkout em desenvolvimento nem instalação global elevada neste teste.
