# Colocar no GitHub

O pacote tem uma pasta `ilha-shell/` com o código, a licença, os guias e três entradas de instalação:

- `install.sh`: código e comandos somente no usuário;
- `install-system.sh`: código e comandos para o sistema, configurações separadas por usuário;
- `install-deps.sh`: prévia/instalação confirmada de dependências, por perfil/módulos.

Extraia o `.tar.gz` e envie o **conteúdo** de `ilha-shell/` para a raiz de um repositório seu. Assim o README e os fontes ficam navegáveis. Você também pode anexar somente o `.tar.gz` a uma Release, junto com o `.sha256`; isso não coloca os fontes navegáveis na página principal automaticamente.

Para conferir um download, coloque os dois arquivos na mesma pasta:

```sh
sha256sum -c ilha-shell-COMMIT.tar.gz.sha256
tar -xzf ilha-shell-COMMIT.tar.gz
cd ilha-shell
./install-deps.sh --profile full
```

Troque COMMIT pelo identificador presente no nome do arquivo recebido. Revise a prévia antes de usar `--apply`. Os dois modos de instalação de código estão no [README](README.md).

O pacote desta entrega não contém contas, tokens, senhas do OBS, mídia pessoal, configuração da sessão, `.git` ou o checkpoint `RETOMADA.md`. Temas prontos são incluídos; temas pessoais ficam fora do repositório em `~/.config/ilha/themes`. O empacotador usa somente arquivos versionados, portanto revise os arquivos que você adicionar ao Git antes de futuras publicações. A instalação preserva Caelestia/Omarchy; a ativação da Ilha e ajustes de barras são decisões separadas do usuário.

## Gerar outra versão

No checkout Git, depois de revisar, testar e commitar:

```sh
python3 ilha/scripts/build_release.py
```

O script exige árvore limpa, usa `git archive HEAD` com as exclusões de `.gitattributes` e escreve `dist/ilha-shell-COMMIT.tar.gz` e o checksum. O conteúdo vem do commit, sem copiar arquivos extras da máquina. Gerar novamente o mesmo commit produz os mesmos bytes gzip. `dist/` é ignorado pelo Git.

O VSIX da extensão pode ser gerado separadamente com `python3 ilha/scripts/editor_extension.py --output /tmp/ilha-activities.vsix` para anexar à mesma Release. A extensão é local; não foi publicada no Marketplace/Open VSX.

A criação do repositório remoto, escolha da visibilidade e publicação da Release ficam com você. Estes scripts não configuram credenciais, criam remotos nem fazem push.
