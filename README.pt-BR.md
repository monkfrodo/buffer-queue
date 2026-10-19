# buffer-queue

Mantém o seu Buffer sempre cheio sem você abrir o Buffer. Você escreve os posts num `queue.json` local e um script pequeno agenda canal por canal, até o limite do plano grátis (10 agendados por canal). Rodando duas vezes por dia, a fila se esvazia sozinha.

Sem IA, sem servidor, sem banco de dados. Só Python 3 e a CLI oficial do Buffer.

[Read in English](README.md)

## O que faz

- Lê o `queue.json`: cada item tem um horário e um texto por canal.
- Agenda cada item no Buffer até o canal bater no limite.
- Não duplica: se o mesmo texto já está no Buffer, só faz o vínculo.
- Se o horário do item já passou, remarca para o próximo horário livre da sua grade.
- Grava o id do post do Buffer de volta no `queue.json`, então rodar de novo é seguro.
- O `watchdog.py` avisa se o reabastecimento parou ou se a fila está acabando.

## Jeito mais rápido: deixe um agente de IA fazer

Abra o [PROMPT.md](PROMPT.md) (em inglês), cole o prompt no Claude Code, Codex ou similar, e ele conduz a instalação inteira sem nunca ver a sua chave de API.

## Instalação (manual)

1. **Instale a CLI do Buffer** (precisa de Node.js):

   ```sh
   npm install --prefix ~/.local/share/buffer-cli @bufferapp/cli
   ```

   No `config.json`, aponte `buffer_cli` para `~/.local/share/buffer-cli/node_modules/.bin/buffer` (caminho absoluto) ou deixe `buffer` no PATH.

2. **Crie uma chave de API** nas configurações da sua conta do Buffer. Trate como senha.

3. **Guarde a chave fora do projeto**, legível só por você:

   ```sh
   mkdir -p ~/.config/buffer-queue && chmod 700 ~/.config/buffer-queue
   read -rs KEY && printf %s "$KEY" > ~/.config/buffer-queue/api-key && unset KEY
   chmod 600 ~/.config/buffer-queue/api-key
   ```

   A chave nunca vai para `config.json`, `queue.json` nem para o repositório. Os dois arquivos estão no `.gitignore`.

4. **Descubra os seus ids.** Com a chave carregada:

   ```sh
   export BUFFER_API_KEY="$(cat ~/.config/buffer-queue/api-key)"
   buffer account --output json
   buffer channels --help
   ```

   O id da organização e dos canais não são segredo, mas são seus. Deixe só no `config.json`.

5. **Crie a configuração e a fila:**

   ```sh
   cp config.example.json config.json
   cp examples/queue.example.json queue.json
   ```

   Edite o `config.json`: id da organização, ids dos canais, fuso horário e grade de horários. Os nomes dos canais (`twitter`, `threads`, ...) precisam bater com o nome do serviço no Buffer, porque o script reconhece posts existentes por serviço.

## Formato da fila

```json
[
 {
  "id": "qualquer-id-unico",
  "due": "2026-01-02T09:30:00-03:00",
  "text": { "twitter": "Texto para o X", "threads": "Texto para o Threads" },
  "buffer": {}
 }
]
```

- `due`: ISO 8601 com fuso. O script pode mudar se o horário já passou.
- `text`: um texto por canal. Canal que não está aqui é ignorado naquele item.
- `buffer`: o script preenche com os ids do Buffer. Comece com `{}`.

## Rodar

```sh
export BUFFER_API_KEY="$(cat ~/.config/buffer-queue/api-key)"
python3 -I refill.py
```

Teste com um item só e confira no Buffer antes de encher a fila.

## Rodar sozinho

**macOS (launchd).** Copie `launchd/com.example.buffer-refill.plist` para `~/Library/LaunchAgents/`, troque `/ABSOLUTE/PATH/TO/` pelo caminho real e rode:

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.buffer-refill.plist
launchctl kickstart gui/$(id -u)/com.example.buffer-refill
```

**Linux (cron):**

```cron
0 8,20 * * * BUFFER_API_KEY="$(cat $HOME/.config/buffer-queue/api-key)" /usr/bin/python3 -I /caminho/buffer-queue/refill.py >> /caminho/buffer-queue/refill.log 2>&1
```

Opcional: rode `python3 watchdog.py` algumas vezes por dia para ser avisado quando o reabastecimento travar.

## Segurança se você fizer fork

- Nunca faça commit de `config.json`, `queue.json`, logs ou chaves. O `.gitignore` cobre, mas confira o `git status` antes de cada push.
- Nunca cole a chave em chat, issue ou pull request. Se vazar, revogue no Buffer e crie outra.
- Use uma chave só para esta ferramenta, para poder revogar sem quebrar mais nada.

## Licença

MIT
