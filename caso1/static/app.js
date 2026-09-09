const form = document.querySelector("#download-form");
const button = document.querySelector("#submit-button");
const panel = document.querySelector("#progress-panel");
const errorBox = document.querySelector("#error-message");
const bar = document.querySelector("#progress-bar");
const value = document.querySelector("#progress-value");
const label = document.querySelector("#status-label");
const detail = document.querySelector("#status-detail");
const fileLink = document.querySelector("#file-link");

const statusLabels = {
  queued: "En cola",
  starting: "Analizando el enlace",
  downloading: "Descargando contenido",
  processing: "Preparando el archivo",
  ready: "Tu archivo está listo",
};

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
  panel.hidden = true;
  button.disabled = false;
}

async function poll(jobId) {
  try {
    const response = await fetch(`/api/downloads/${jobId}`);
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "No fue posible consultar la descarga.");
    if (job.status === "error") throw new Error(job.error || "La plataforma rechazó la descarga.");

    const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
    label.textContent = statusLabels[job.status] || "Procesando";
    detail.textContent = [job.speed, job.eta && `Faltan ${job.eta}`].filter(Boolean).join(" · ") || "Esto puede tomar unos segundos";
    value.textContent = `${Math.round(progress)}%`;
    bar.style.width = `${Math.max(progress, job.status === "queued" ? 4 : 8)}%`;

    if (job.status === "ready") {
      detail.textContent = job.title || job.filename;
      fileLink.href = job.download_url;
      fileLink.hidden = false;
      button.disabled = false;
      return;
    }
    window.setTimeout(() => poll(jobId), 1000);
  } catch (error) {
    showError(error.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  fileLink.hidden = true;
  panel.hidden = false;
  button.disabled = true;
  label.textContent = "Creando descarga";
  detail.textContent = "Validando el enlace";
  value.textContent = "0%";
  bar.style.width = "4%";

  try {
    const response = await fetch("/api/downloads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: document.querySelector("#video-url").value,
        quality: document.querySelector("#quality").value,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "No se pudo iniciar la descarga.");
    poll(result.id);
  } catch (error) {
    showError(error.message);
  }
});
