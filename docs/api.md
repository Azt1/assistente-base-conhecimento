# Usar a API local

Com o servidor iniciado na porta 8001, abra `http://127.0.0.1:8001/docs`. Os formatos de entrada e saída de cada rota aparecem nessa página.

## Buscar documentos sem IA

Use `POST /api/busca` com um corpo JSON:

```json
{
  "pergunta": "Qual o prazo de entrega?",
  "limite": 1
}
```

`limite` é opcional e aceita números inteiros de 1 a 3. Sem ele, a busca retorna no máximo três documentos. Não há resultado preenchido artificialmente: se apenas um documento corresponder à pergunta, a resposta contém somente esse documento. Se não houver correspondência, `fontes` é uma lista vazia.

A busca devolve `id`, `titulo` e `texto` de cada documento. Ela compara palavras, não interpreta o sentido da pergunta nem faz chamadas a modelos de IA.

No PowerShell:

```powershell
$corpo = @{ pergunta = "prazo entrega"; limite = 1 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/api/busca" `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($corpo))
```

## Consultar com IA

`POST /api/chat` recebe `pergunta` e `autoriza_envio`. Sem autorização, retorna `400`. Sem configuração do provedor, retorna `503`. Esta integração ainda precisa ser validada com uma chamada real ao modelo.

O corpo de uma resposta bem-sucedida contém `resposta`, `fontes` e `encontrou`. A aplicação só aceita IDs de fontes enviados ao modelo naquela consulta e remove referências repetidas. Se o modelo citar uma fonte diferente, não citar nenhuma ou indicar falta de informação, o texto é substituído pela orientação de procurar o atendimento humano.

Essa verificação confere referências, não garante que cada frase esteja correta. Ainda precisamos avaliar a qualidade das respostas e os casos em que a busca encontra um documento relacionado, mas insuficiente para responder.

## Erros

- `422`: pergunta ausente, curta demais, maior que 500 caracteres ou limite de busca inválido.
- `400`: envio ao provedor não autorizado.
- `503`: configuração da IA incompleta.
- `502`: falha na consulta ao provedor, com mensagem pública sem detalhes internos.
- `429`: já existem duas consultas ao modelo em andamento neste processo.

A aplicação não grava as perguntas em banco. Quando a consulta com IA é configurada e autorizada, a pergunta e os documentos selecionados são enviados ao provedor externo. Use apenas os dados fictícios desta base e mantenha o servidor restrito ao computador local.
