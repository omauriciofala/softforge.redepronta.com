/**
 * SoftForge Bootstrap Starter Theme - Client Script
 * Demonstra a integração de um frontend Bootstrap com a API do SoftForge.
 */

const API_BASE_URL = window.location.origin.includes(":8000")
  ? ""
  : "http://localhost:8000";

document.addEventListener("DOMContentLoaded", () => {
  initHealthCheck();
  loadSystemThemes();
  setupTokenPlayground();
});

/**
 * Checa a saúde da API SoftForge e atualiza o badge no topo da página.
 */
async function initHealthCheck() {
  const badge = document.getElementById("api-status-badge");
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) {
      const data = await res.json();
      badge.textContent = `API: Online (v${data.version})`;
      badge.className = "badge bg-success";
    } else {
      badge.textContent = "API: Indisponível";
      badge.className = "badge bg-danger";
    }
  } catch (err) {
    badge.textContent = "API: Offline / Fallback";
    badge.className = "badge bg-warning text-dark";
  }
}

/**
 * Carrega a lista de temas instalados no SoftForge via GET /api/v1/system/themes.
 */
async function loadSystemThemes() {
  const tableBody = document.getElementById("themes-table-body");
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/system/themes`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const themes = await res.json();
    renderThemesTable(themes);
  } catch (err) {
    // Fallback estático caso a API local ainda não esteja em execução
    renderThemesTable([
      {
        name: "SoftForge Default React",
        slug: "default-react",
        engine: "react",
        version: "0.1.0",
        description: "Tema padrão React 18 + Tailwind",
      },
      {
        name: "SoftForge Bootstrap Starter",
        slug: "bootstrap-starter",
        engine: "html-bootstrap",
        version: "1.0.0",
        description: "Tema clássico Bootstrap 5",
      },
    ]);
  }
}

/**
 * Renderiza os temas na tabela.
 */
function renderThemesTable(themes) {
  const tableBody = document.getElementById("themes-table-body");
  if (!themes || themes.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Nenhum tema encontrado.</td></tr>`;
    return;
  }

  tableBody.innerHTML = themes
    .map(
      (t) => `
    <tr>
      <td><strong>${escapeHtml(t.name)}</strong></td>
      <td><code>${escapeHtml(t.slug)}</code></td>
      <td><span class="badge bg-info text-dark">${escapeHtml(t.engine)}</span></td>
      <td><small class="text-muted">v${escapeHtml(t.version)}</small></td>
      <td>
        <button class="btn btn-xs btn-outline-secondary btn-sm" onclick="previewTheme('${escapeHtml(t.slug)}')">
          Ver Tokens
        </button>
      </td>
    </tr>
  `
    )
    .join("");
}

/**
 * Aplica tokens dinamicamente no :root
 */
function setupTokenPlayground() {
  const btnApply = document.getElementById("btn-apply-tokens");
  const inputColor = document.getElementById("input-primary-color");
  const inputRadius = document.getElementById("input-radius");

  const valColorPrimary = document.getElementById("val-color-primary");
  const valRadius = document.getElementById("val-radius");

  btnApply.addEventListener("click", () => {
    const newColor = inputColor.value;
    const newRadius = inputRadius.value;

    document.documentElement.style.setProperty("--sf-color-primary", newColor);
    document.documentElement.style.setProperty("--sf-radius", newRadius);
    document.documentElement.style.setProperty("--bs-primary", newColor);
    document.documentElement.style.setProperty("--bs-border-radius", newRadius);

    valColorPrimary.textContent = newColor;
    valRadius.textContent = newRadius;
  });

  const btnRefresh = document.getElementById("btn-refresh-themes");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      loadSystemThemes();
    });
  }
}

function previewTheme(slug) {
  alert(`Tema selecionado: ${slug}\nOs tokens e manifestos podem ser consultados via /api/v1/system/themes/${slug}`);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
