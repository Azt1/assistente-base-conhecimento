# Assistente da base de conhecimento

Projeto de estudo em Python para consultar documentos de uma empresa fictícia e, depois, usar esses trechos para responder perguntas com IA e indicar as fontes.

## Etapa atual

A API inicia e permite buscar os documentos locais por palavras em comum com a pergunta. A base tem três exemplos da Loja Aurora: entregas, trocas e atendimento.

Já existe código de integração com Gemini, mas ele ainda não foi validado com uma chamada real ao modelo. Não há tela de conversa, publicação na internet nem resultados medidos com usuários. Busca local não é resposta gerada por IA.

## Executar

Use Python 3.11 ou superior. No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn knowledge_assistant.api:app --host 127.0.0.1 --port 8001
```

Abra `http://127.0.0.1:8001/docs` para testar as rotas.

- `GET /api/status`: informa a quantidade de documentos e se a configuração de IA está preenchida. Isso não verifica se a chave é válida.
- `POST /api/busca`: recebe `{"pergunta": "Qual o prazo de entrega?"}` e retorna documentos relacionados, sem enviar dados a um serviço externo.
- `POST /api/chat`: reservado para a integração com Gemini. Sem configuração, retorna `503`. O envio exige `autoriza_envio: true`, além da pergunta.

Não configure uma chave para testar a busca local. Não envie dados pessoais ou documentos reais nesta demonstração.

## Organização

- `search.py`: carrega a base e compara as palavras da pergunta com as dos documentos.
- `api.py`: recebe as requisições HTTP e valida as perguntas.
- `gemini.py`: contém o cliente do provedor, ainda pendente de teste real.
- `base/`: documentos fictícios versionados com o código.

## Próximas etapas

1. Conferir a busca e as validações com testes automatizados.
2. Configurar o provedor e testar uma resposta real, sem dados pessoais.
3. Criar uma tela simples de conversa e exibição das fontes.
4. Avaliar respostas, registrar limitações e só então preparar uma demonstração publicada.

As perguntas e os documentos usados na consulta com IA são enviados ao Google quando essa função é configurada e autorizada. Pode haver cobrança conforme a conta e o modelo. A aplicação ainda não tem autenticação nem controle de custo por usuário; não exponha o servidor à internet nesta fase.
