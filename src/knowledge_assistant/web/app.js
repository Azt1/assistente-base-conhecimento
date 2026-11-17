const form = document.querySelector("#search-form");
const questionInput = document.querySelector("#question");
const results = document.querySelector("#results");
const consentRow = document.querySelector("#consent-row");
const consent = document.querySelector("#consent");
const submitButton = form.querySelector("button[type=submit]");
const statusMessage = document.querySelector("#model-status");
const modes = document.querySelectorAll('input[name="mode"]');

function selectedMode() {
  return document.querySelector('input[name="mode"]:checked').value;
}

modes.forEach((mode) => mode.addEventListener("change", () => {
  const wantsChat = selectedMode() === "chat";
  consentRow.hidden = !wantsChat;
  submitButton.textContent = wantsChat ? "Perguntar à IA" : "Pesquisar";
  statusMessage.textContent = wantsChat ? "Verificando se a IA está configurada..." : "";
}));

fetch("/api/status")
  .then((response) => response.json())
  .then((status) => {
    statusMessage.textContent = status.ia_configurada
      ? "A integração com IA está configurada no servidor."
      : "A IA ainda não está configurada; a busca local continua disponível.";
  })
  .catch(() => {
    statusMessage.textContent = "Não foi possível consultar o status da integração com IA.";
  });

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const pergunta = questionInput.value.trim();
  if (pergunta.length < 3) return;
  const useChat = selectedMode() === "chat";
  if (useChat && !consent.checked) {
    statusMessage.textContent = "Marque a autorização antes de enviar a pergunta ao provedor.";
    consent.focus();
    return;
  }

  results.replaceChildren();
  results.setAttribute("aria-busy", "true");
  submitButton.disabled = true;
  submitButton.textContent = "Consultando...";
  const loading = document.createElement("p");
  loading.textContent = "Buscando nos documentos...";
  results.append(loading);

  try {
    const response = await fetch(useChat ? "/api/chat" : "/api/busca", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(useChat
        ? { pergunta, autoriza_envio: true }
        : { pergunta }),
    });
    const data = await response.json();
    results.replaceChildren();

    if (!response.ok) {
      const messages = {
        400: "Autorize o envio da pergunta para usar o modo IA.",
        422: "Revise sua pergunta e tente novamente.",
        429: "Já há consultas à IA em andamento. Tente de novo em instantes.",
        502: "A IA não respondeu agora. Tente novamente mais tarde.",
        503: "A integração com IA ainda não foi configurada no servidor.",
      };
      throw new Error(messages[response.status] || "Não foi possível concluir a consulta.");
    }
    if (data.fontes.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = data.resposta || "Não encontrei esse assunto nos documentos disponíveis.";
      results.append(empty);
      return;
    }

    if (data.resposta) {
      const answer = document.createElement("p");
      answer.className = "assistant-answer";
      answer.textContent = data.resposta;
      results.append(answer);
    }
    const heading = document.createElement("h2");
    heading.textContent = data.resposta ? "Fontes consultadas" : "Encontrei estas informações";
    results.append(heading);
    for (const source of data.fontes) {
      const card = document.createElement("article");
      card.className = "source-card";
      const title = document.createElement("h3");
      const text = document.createElement("p");
      const citation = document.createElement("small");
      title.textContent = source.titulo;
      text.textContent = source.texto;
      citation.textContent = `Documento: ${source.id}`;
      card.append(title, text, citation);
      results.append(card);
    }
  } catch (cause) {
    results.replaceChildren();
    const error = document.createElement("p");
    error.textContent = cause instanceof TypeError
      ? "Não consegui acessar o servidor. Confira se ele está ligado e tente de novo."
      : cause.message;
    results.append(error);
  } finally {
    results.setAttribute("aria-busy", "false");
    submitButton.disabled = false;
    submitButton.textContent = selectedMode() === "chat" ? "Perguntar à IA" : "Pesquisar";
  }
});
