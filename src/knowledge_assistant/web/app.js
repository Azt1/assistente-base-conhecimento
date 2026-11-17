const form = document.querySelector("#search-form");
const questionInput = document.querySelector("#question");
const results = document.querySelector("#results");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const pergunta = questionInput.value.trim();
  if (pergunta.length < 3) return;

  results.replaceChildren();
  results.setAttribute("aria-busy", "true");
  const loading = document.createElement("p");
  loading.textContent = "Buscando nos documentos...";
  results.append(loading);

  try {
    const response = await fetch("/api/busca", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta }),
    });
    const data = await response.json();
    results.replaceChildren();

    if (!response.ok) throw new Error("Não foi possível fazer a busca.");
    if (data.fontes.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = "Não encontrei esse assunto nos documentos disponíveis.";
      results.append(empty);
      return;
    }

    const heading = document.createElement("h2");
    heading.textContent = "Encontrei estas informações";
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
