const state = {
  bootstrap: null,
  annotator: null,
  rows: [],
  currentIndex: 0,
};

const fieldOptions = {
  target_rendering_strategy: [
    { value: "", label: "Select..." },
    { value: "translate", label: "translate - use a normal Korean title/name" },
    { value: "transliterate", label: "transliterate - write the sound in Korean" },
    { value: "preserve", label: "preserve - keep the English/original form" },
    { value: "adapt", label: "adapt - use a more adjusted Korean form" },
  ],
  official_korean_title_preferred: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - there is a standard Korean title/name" },
    { value: "no", label: "no - no standard Korean title seems necessary" },
  ],
  preserve_english_preferred: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - English feels more natural here" },
    { value: "no", label: "no - Korean form is better here" },
  ],
  adaptation_needed: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - direct wording is not enough" },
    { value: "no", label: "no - direct wording is fine" },
  ],
  gpt4o_entity_correct: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - clearly right to a Korean reader" },
    { value: "partly", label: "partly - mostly right but awkward or incomplete" },
    { value: "no", label: "no - wrong or unacceptable" },
  ],
  gpt4o_rendering_strategy: [
    { value: "", label: "Select..." },
    { value: "translate", label: "translate - used a Korean title/name" },
    { value: "transliterate", label: "transliterate - used Korean sound spelling" },
    { value: "preserve", label: "preserve - kept English/original form" },
    { value: "adapt", label: "adapt - used a more adjusted Korean form" },
  ],
  gpt4o_quality_label: [
    { value: "", label: "Select..." },
    { value: "correct", label: "correct - fully acceptable" },
    { value: "acceptable_alias", label: "acceptable_alias - different but still acceptable" },
    { value: "incorrect_entity", label: "incorrect_entity - wrong entity" },
    { value: "wrong_rendering_strategy", label: "wrong_rendering_strategy - right entity, wrong way of writing it" },
    { value: "partial_entity_error", label: "partial_entity_error - partly wrong or incomplete" },
    { value: "hallucinated_entity", label: "hallucinated_entity - added unsupported entity info" },
    { value: "omitted_entity", label: "omitted_entity - left the entity out" },
  ],
  gpt4o_metric_likely_miss: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - automatic score might miss this problem" },
    { value: "no", label: "no - a simple score would probably catch it" },
    { value: "maybe", label: "maybe - not sure" },
  ],
  gpt4o_mini_entity_correct: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - clearly right to a Korean reader" },
    { value: "partly", label: "partly - mostly right but awkward or incomplete" },
    { value: "no", label: "no - wrong or unacceptable" },
  ],
  gpt4o_mini_rendering_strategy: [
    { value: "", label: "Select..." },
    { value: "translate", label: "translate - used a Korean title/name" },
    { value: "transliterate", label: "transliterate - used Korean sound spelling" },
    { value: "preserve", label: "preserve - kept English/original form" },
    { value: "adapt", label: "adapt - used a more adjusted Korean form" },
  ],
  gpt4o_mini_quality_label: [
    { value: "", label: "Select..." },
    { value: "correct", label: "correct - fully acceptable" },
    { value: "acceptable_alias", label: "acceptable_alias - different but still acceptable" },
    { value: "incorrect_entity", label: "incorrect_entity - wrong entity" },
    { value: "wrong_rendering_strategy", label: "wrong_rendering_strategy - right entity, wrong way of writing it" },
    { value: "partial_entity_error", label: "partial_entity_error - partly wrong or incomplete" },
    { value: "hallucinated_entity", label: "hallucinated_entity - added unsupported entity info" },
    { value: "omitted_entity", label: "omitted_entity - left the entity out" },
  ],
  gpt4o_mini_metric_likely_miss: [
    { value: "", label: "Select..." },
    { value: "yes", label: "yes - automatic score might miss this problem" },
    { value: "no", label: "no - a simple score would probably catch it" },
    { value: "maybe", label: "maybe - not sure" },
  ],
  preferred_model: [
    { value: "", label: "Select..." },
    { value: "gpt4o", label: "gpt4o - model A feels better" },
    { value: "gpt4o_mini", label: "gpt4o-mini - model B feels better" },
    { value: "tie", label: "tie - both feel equally good" },
    { value: "neither", label: "neither - both feel bad" },
  ],
};

const editableFields = [
  "target_rendering_strategy",
  "official_korean_title_preferred",
  "preserve_english_preferred",
  "adaptation_needed",
  "gpt4o_entity_correct",
  "gpt4o_rendering_strategy",
  "gpt4o_quality_label",
  "gpt4o_metric_likely_miss",
  "gpt4o_notes",
  "gpt4o_mini_entity_correct",
  "gpt4o_mini_rendering_strategy",
  "gpt4o_mini_quality_label",
  "gpt4o_mini_metric_likely_miss",
  "gpt4o_mini_notes",
  "preferred_model",
  "overall_comments",
];

function $(selector) {
  return document.querySelector(selector);
}

function populateSelects() {
  Object.entries(fieldOptions).forEach(([field, options]) => {
    const element = document.getElementById(field);
    if (!element) return;
    element.innerHTML = "";
    options.forEach((option) => {
      const el = document.createElement("option");
      el.value = option.value;
      el.textContent = option.label;
      element.appendChild(el);
    });
  });
}

function createChip(text) {
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.textContent = text;
  return chip;
}

function parseJsonList(rawValue) {
  if (!rawValue) return [];
  try {
    const parsed = JSON.parse(rawValue);
    return Array.isArray(parsed) ? parsed : [String(parsed)];
  } catch {
    return [rawValue];
  }
}

function rowLabel(row) {
  return `${row.assignment_index}. ${row.id}`;
}

function queueSummary() {
  const complete = state.rows.filter((row) => row.annotation_completed === "yes").length;
  return `${complete} complete / ${state.rows.length} assigned`;
}

function updateProgress() {
  const complete = state.rows.filter((row) => row.annotation_completed === "yes").length;
  const total = state.rows.length;
  const percent = total ? Math.round((complete / total) * 100) : 0;
  $("#progress-label").textContent = `${complete} / ${total} complete`;
  $("#progress-percent").textContent = `${percent}%`;
  $("#progress-fill").style.width = `${percent}%`;
  $("#queue-summary").textContent = queueSummary();
}

function renderQueue() {
  const container = $("#queue-list");
  container.innerHTML = "";
  state.rows.forEach((row, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "queue-item";
    if (index === state.currentIndex) button.classList.add("active");
    if (row.annotation_completed === "yes") button.classList.add("complete");
    button.innerHTML = `
      <strong>${rowLabel(row)}</strong>
      <div class="meta-row">
        <span>${row.primary_entity_type}</span>
        <span>${row.annotation_completed === "yes" ? "Done" : "Pending"}</span>
      </div>
    `;
    button.addEventListener("click", () => {
      state.currentIndex = index;
      renderCurrentRow();
      renderQueue();
    });
    container.appendChild(button);
  });
}

function setValue(field, value) {
  const element = document.getElementById(field);
  if (!element) return;
  element.value = value || "";
}

function renderCurrentRow() {
  const row = state.rows[state.currentIndex];
  if (!row) return;

  $("#example-id").textContent = rowLabel(row);
  $("#example-meta").textContent = `${row.primary_entity_type} | Wikidata ${row.wikidata_id}`;
  $("#source-text").textContent = row.source;
  $("#reference-translation").textContent = row.reference_translation;
  $("#reference-mention").textContent = row.reference_mention;
  $("#gpt4o_prediction").textContent = row.gpt4o_prediction;
  $("#gpt4o_mini_prediction").textContent = row.gpt4o_mini_prediction;

  const referenceTranslations = $("#reference-translations");
  referenceTranslations.innerHTML = "";
  parseJsonList(row.reference_translations).forEach((item) => {
    referenceTranslations.appendChild(createChip(item));
  });

  const entityTypes = $("#entity-types");
  entityTypes.innerHTML = "";
  parseJsonList(row.entity_types).forEach((item) => {
    entityTypes.appendChild(createChip(item));
  });

  editableFields.forEach((field) => setValue(field, row[field]));

  $("#prev-button").disabled = state.currentIndex === 0;
  $("#next-button").disabled = state.currentIndex === state.rows.length - 1;
  $("#save-message").textContent = row.annotation_completed === "yes"
    ? "Saved. You can still revise this example."
    : "Fill the fields and save when ready.";
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(payload.error || "Request failed");
  }
  return response.json();
}

function collectAnnotations() {
  const annotations = {};
  editableFields.forEach((field) => {
    const element = document.getElementById(field);
    if (element) annotations[field] = element.value;
  });
  return annotations;
}

async function saveCurrentRow(advance = false) {
  const row = state.rows[state.currentIndex];
  if (!row || !state.annotator) return;

  $("#save-message").textContent = "Saving...";
  try {
    const payload = await fetchJson(`/api/annotator/${state.annotator.slug}/save`, {
      method: "POST",
      body: JSON.stringify({
        id: row.id,
        annotations: collectAnnotations(),
      }),
    });

    state.rows = payload.session.rows;
    const savedIndex = state.rows.findIndex((item) => item.id === row.id);
    state.currentIndex = savedIndex >= 0 ? savedIndex : state.currentIndex;
    updateProgress();

    if (advance) {
      const nextIncomplete = state.rows.findIndex(
        (item, index) => index > state.currentIndex && item.annotation_completed !== "yes",
      );
      if (nextIncomplete >= 0) {
        state.currentIndex = nextIncomplete;
      } else if (state.currentIndex < state.rows.length - 1) {
        state.currentIndex += 1;
      }
    }

    renderQueue();
    renderCurrentRow();
    $("#save-message").textContent = "Saved locally in your clone.";
  } catch (error) {
    $("#save-message").textContent = error.message;
  }
}

async function loadSession(slug) {
  const payload = await fetchJson(`/api/annotator/${slug}/session`);
  state.annotator = payload.annotator;
  state.rows = payload.rows;
  const firstIncomplete = state.rows.findIndex((row) => row.annotation_completed !== "yes");
  state.currentIndex = firstIncomplete >= 0 ? firstIncomplete : 0;

  $("#annotator-picker").classList.add("hidden");
  $("#workspace").classList.remove("hidden");
  $("#annotator-avatar").src = payload.annotator.avatar;
  $("#annotator-avatar").alt = `${payload.annotator.name} avatar`;
  $("#annotator-name").textContent = payload.annotator.name;
  $("#save-path").textContent = `Saved in ${payload.export_path}`;

  updateProgress();
  renderQueue();
  renderCurrentRow();

  const header = document.querySelector(".workspace-header");
  if (header) {
    header.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function renderPickerCards() {
  const grid = $("#picker-grid");
  grid.innerHTML = "";
  state.bootstrap.annotators.forEach((annotator) => {
    const card = document.createElement("article");
    card.className = "annotator-card";
    card.innerHTML = `
      <img src="${annotator.avatar}" alt="${annotator.name} avatar" />
      <div>
        <h2>${annotator.name}</h2>
        <p>${annotator.assigned_count} assigned examples</p>
        <button class="primary-button" type="button">Start as ${annotator.name}</button>
      </div>
    `;
    card.querySelector("button").style.background = annotator.accent;
    card.querySelector("button").addEventListener("click", () => loadSession(annotator.slug));
    grid.appendChild(card);
  });
}

async function bootstrap() {
  populateSelects();
  state.bootstrap = await fetchJson("/api/bootstrap");
  renderPickerCards();

  $("#prev-button").addEventListener("click", () => {
    if (state.currentIndex > 0) {
      state.currentIndex -= 1;
      renderCurrentRow();
      renderQueue();
    }
  });
  $("#next-button").addEventListener("click", () => {
    if (state.currentIndex < state.rows.length - 1) {
      state.currentIndex += 1;
      renderCurrentRow();
      renderQueue();
    }
  });
  $("#save-button").addEventListener("click", () => saveCurrentRow(false));
  $("#save-next-button").addEventListener("click", () => saveCurrentRow(true));
}

bootstrap().catch((error) => {
  $("#annotator-picker").innerHTML = `<p>${error.message}</p>`;
});
