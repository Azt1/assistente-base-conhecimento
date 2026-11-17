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

    if (!response.ok) throw new Error("Não foi possível fazer a busca.");
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
  } catch {
    results.replaceChildren();
    const error = document.createElement("p");
    error.textContent = "A busca falhou. Confira se o servidor está ligado e tente de novo.";
    results.append(error);
  } finally {
    results.setAttribute("aria-busy", "false");
  }
});
