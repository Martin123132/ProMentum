const bankKeys = ["ideas", "phrases", "people", "places", "obsessions", "questions", "formats", "rules"];

let appState = null;
let readiness = null;
let modes = [];
let favourites = [];
let currentResult = null;
let activeBankKey = "ideas";
let lastVariantSeed = null;
let transientMessage = "";
let lastExportPath = null;
let lastResultAction = null;
let lastCopyAction = null;
let collideMessageTimer = null;
let librarySearch = "";

const FLOW_STEPS = [
  { id: "start", route: "/start", label: "Start", lockedReason: null },
  { id: "bank", route: "/bank", label: "Build Bank", lockedReason: null },
  { id: "collide", route: "/collide", label: "Generate", lockedReason: "Add at least some ingredients first." },
  { id: "result", route: "/result", label: "Result", lockedReason: "Generate once to create something to review." },
  { id: "library", route: "/library", label: "Library", lockedReason: null },
  { id: "settings", route: "/settings", label: "Settings", lockedReason: null },
];

const pageMeta = {
  start: {
    title: "Start",
    step: "Get unstuck",
    stage: "1",
    cue: "Add a few ingredients until the traffic light turns amber, then green.",
    goal: "Goal: grow the spark bank so ProMentum can give you a first move.",
    tips: [
      "Quick Add one ingredient to get going.",
      "When the light is amber, you can generate your first move.",
      "If the light stays red, fill more categories in the Spark Bank.",
    ],
    actionText: "Open Spark Bank",
    actionLink: "/bank",
  },
  bank: {
    title: "Spark Bank",
    step: "Feed the engine",
    stage: "2",
    cue: "Add ingredients by category so results feel personal, not generic.",
    goal: "Goal: build a few entries in at least 3 categories.",
    tips: [
      "Keep each line short and specific to your own projects.",
      "Make sure people, places, and rules are not empty.",
      "When at least 3 categories have content, return to Generate.",
    ],
    actionText: "Go Generate",
    actionLink: "/collide",
  },
  collide: {
    title: "Generate",
    step: "Choose the push",
    stage: "3",
    cue: "Pick a mode and control weirdness to move from sane to chaotic.",
    goal: "Goal: generate one result, then save what you like.",
    tips: [
      "Pick a seed mode and keep weirdness around the middle to start.",
      "Use the same seed only when you want an intentional repeat.",
      "If output feels flat, raise weirdness a little and run again.",
    ],
    actionText: "Generate First Move",
    actionLink: "/result",
  },
  result: {
    title: "Result",
    step: "Use the spark",
    stage: "4",
    cue: "Turn the best hook into your next task, post, or format.",
    goal: "Goal: save or export the result that sparks the strongest action.",
    tips: [
      "Use 'Regenerate Variant' to move energy without losing context.",
      "Use Save Favourite before you clear or overwrite current output.",
      "Copy first, export second; both work without changing your saved copy.",
    ],
    actionText: "Open Library",
    actionLink: "/library",
  },
  library: {
    title: "Library",
    step: "Saved sparks",
    stage: "5",
    cue: "Keep only the hits and delete the rest manually.",
    goal: "Goal: review, copy, and pick a favourite to return to later.",
    tips: [
      "Load a favourite to compare alternatives in the same place.",
      "Clear the library when you want fewer choices.",
      "Only save results that still feel useful later.",
    ],
    actionText: "Make Another",
    actionLink: "/collide",
  },
  settings: {
    title: "Settings",
    step: "Local storage",
    stage: "6",
    cue: "Your data stays local to this machine.",
    goal: "Goal: know where files are stored and keep the workflow clean.",
    tips: [
      "Use `PROMENTUM_HOME` to point data to a different folder.",
      "Older portable data folders still load, but new setup should use ProMentum naming.",
      "Open Data and Exports folders after runs to check what was saved.",
      "The app can be restarted any time without reinstall.",
    ],
    actionText: "Run Storage Check",
    actionLink: "/start",
  },
};

const MODE_GUIDES = {
  "Random Spark": {
    label: "Surprise route",
    copy: "Let the engine choose the format when you want a blind first throw.",
    output: "Best for warm-ups, not final direction.",
  },
  "Sketch Hook": {
    label: "Comedy premise",
    copy: "Looks for one clean bit, one interruption, and a callback-shaped ending.",
    output: "Best when you want a scene you can actually write.",
  },
  "Video Idea": {
    label: "Fast visual",
    copy: "Pushes toward a thumbnail, opening image, and caption-sized premise.",
    output: "Best for short-form or pitchable clips.",
  },
  "Title Storm": {
    label: "Naming chaos",
    copy: "Turns the spark into titles, subtitles, and fake official projects.",
    output: "Best when you need a list of hooks fast.",
  },
  "Scene Seed": {
    label: "Room starter",
    copy: "Gives you a first line, a turn, and a room that misunderstands itself.",
    output: "Best for sitcom, sketch, or dialogue starts.",
  },
  "Concept Mashup": {
    label: "Buildable idea",
    copy: "Finds the useful pressure between ingredients and keeps one human motive underneath.",
    output: "Best for turning scraps into a usable concept.",
  },
  "Personal Myth": {
    label: "Tiny folklore",
    copy: "Treats a private feeling like a ritual, object, or household legend.",
    output: "Best when the idea needs emotional weirdness.",
  },
  "Serious To Absurd": {
    label: "Logic wobble",
    copy: "Starts sensible, then adds rules until the sensible version becomes the joke.",
    output: "Best for mock-serious pitches and fake explanations.",
  },
};

const BANK_CATEGORY_GUIDES = {
  ideas: {
    aim: "Raw sparks, half-premises, odd problems, or things you keep circling back to.",
    good: "Specific beats with a noun and a pressure point.",
    avoid: "Full paragraphs. The engine works better with punchy fragments.",
    examples: ["a fake tribunal for abandoned apps", "a kettle that thinks it is management"],
  },
  phrases: {
    aim: "Lines, sayings, titles, insults, warnings, or tiny bits of voice.",
    good: "Anything that sounds like someone could actually say it.",
    avoid: "Generic labels like funny idea or good video.",
    examples: ["this was never meant to be a spreadsheet", "the room has unionized"],
  },
  people: {
    aim: "Characters, real-world archetypes, public figures, family roles, or made-up specialists.",
    good: "A person plus a clear energy.",
    avoid: "Only first names unless the name itself is funny to you.",
    examples: ["Newton after one bad group chat", "a landlord who speaks in patch notes"],
  },
  places: {
    aim: "Rooms, towns, platforms, queues, offices, clubs, shops, and impossible corners.",
    good: "A place with social pressure built in.",
    avoid: "Empty locations that could be anywhere.",
    examples: ["therapy under the stairs", "the library aisle nobody admits exists"],
  },
  obsessions: {
    aim: "Private fixations, loops, fears, rituals, niche topics, and recurring arguments.",
    good: "The thing your brain keeps returning to for no sensible reason.",
    avoid: "Broad topics with no emotional hook.",
    examples: ["making every tool local-first", "whether a sandwich can be a legal document"],
  },
  questions: {
    aim: "What-if prompts, doubts, challenges, and arguments the scene can try to answer badly.",
    good: "Questions that force a choice or contradiction.",
    avoid: "Research questions that need facts instead of sparks.",
    examples: ["what if the tutorial became the villain?", "who benefits if the lift learns shame?"],
  },
  formats: {
    aim: "Containers for the output: sketch, title, memo, fake advert, scene, pitch, ritual, game.",
    good: "A shape you could actually make next.",
    avoid: "Vibes without a delivery format.",
    examples: ["five-minute sitcom cold open", "mock-serious safety training video"],
  },
  rules: {
    aim: "Constraints, laws, house rules, curses, procedures, and things everyone must obey.",
    good: "A rule that can break a normal situation.",
    avoid: "Rules so vague they cannot cause trouble.",
    examples: ["nobody can say the obvious thing first", "every solution must involve a clipboard"],
  },
};

const el = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) },
  });
  const data = await response.json();
  if (!data.ok) {
    throw new Error(data.error || "ProMentum request failed");
  }
  return data;
}

async function boot() {
  restoreResult();
  bindShell();
  await loadAll();
  renderRoute();
}

function bindShell() {
  document.body.addEventListener("click", (event) => {
    const link = event.target.closest("[data-link]");
    if (!link) return;
    event.preventDefault();
    navigate(link.getAttribute("href"));
  });
  window.addEventListener("popstate", renderRoute);
}

async function loadAll() {
  const data = await api("/api/state");
  appState = data.state;
  readiness = data.readiness;
  modes = data.modes || [];
  const doctor = await api("/api/doctor");
  updateDoctorStatus(doctor);
  const favData = await api("/api/favourites");
  favourites = favData.favourites || [];
  updateShellStatus();
  updateFlowRail("start");
}

function pageFromPath() {
  const part = location.pathname.replace("/", "") || "start";
  return pageMeta[part] ? part : "start";
}

function navigate(path) {
  history.pushState({}, "", path);
  renderRoute();
}

function renderRoute() {
  if (!appState || !readiness) return;
  const page = pageFromPath();
  const meta = pageMeta[page];
  el("pageTitle").textContent = meta.title;
  el("pageStep").textContent = meta.step;
  document.querySelectorAll("[data-page]").forEach((link) => {
    link.classList.toggle("active", link.dataset.page === page);
    if (link.dataset.page === page) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });
  const root = el("pageRoot");
  root.classList.remove("page-enter");
  root.innerHTML = "";
  const renderers = {
    start: renderStart,
    bank: renderBank,
    collide: renderCollide,
    result: renderResult,
    library: renderLibrary,
    settings: renderSettings,
  };
  root.innerHTML = renderers[page](meta);
  root.classList.remove("page-enter");
  void root.offsetWidth;
  root.classList.add("page-enter");
  bindPage(page);
  updateFlowRail(page);
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  setTimeout(() => {
    setPrimaryPageFocus(page);
  }, 0);
}

function setPrimaryPageFocus(page) {
  const focusTargetGroups = {
    start: ["quickIdeaInput", "quickCollisionButton", "starterBankButton"],
    bank: ["bankQuickIdeaInput", "bankQuickAddButton", "saveBankButton"],
    collide: ["seedInput", "collideButton", "sameSeedButton"],
    result: ["copyResultButton", "saveFavouriteButton", "exportTxtButton", "openColliderButton"],
    library: ["librarySearchInput", "clearLibraryButton"],
    settings: ["openDataButton", "openExportsButtonSettings", "refreshDoctorButton"],
  };
  const targets = focusTargetGroups[page] || [];
  const target = firstAvailableTarget(targets);
  if (target) {
    target.focus({ preventScroll: true });
  }
}

function firstAvailableTarget(selectors) {
  if (!Array.isArray(selectors)) return null;
  for (const id of selectors) {
    const target = el(id);
    if (!target || target.disabled) continue;
    const style = getComputedStyle(target);
    if (style.display === "none" || style.visibility === "hidden" || target.getAttribute("aria-hidden") === "true") {
      continue;
    }
    if (target.offsetParent === null) continue;
    return target;
  }
  return null;
}

function updateShellStatus() {
  const status = el("sideStatus");
  status.innerHTML = `<span class="status-dot ${readiness.level}"></span><span>${readiness.label}: ${readiness.total} ingredients</span>`;
}

function updateFlowRail(currentPage) {
  const rail = el("flowRail");
  if (!rail) return;
  const currentIndex = FLOW_STEPS.findIndex((step) => step.id === currentPage);
  rail.innerHTML = FLOW_STEPS.map((step, index) => {
    const isLocked = step.id === "collide" ? readiness.level === "red" : step.id === "result" ? !currentResult : false;
    const isDone = index < currentIndex;
    const isCurrent = step.id === currentPage;
    const classes = isLocked ? "locked" : isDone ? "done" : isCurrent ? "active" : "";
    const hint = step.lockedReason && isLocked ? `<span class="flow-hint">${escapeHtml(step.lockedReason)}</span>` : "";
    const title = `<span class="flow-label">${escapeHtml(step.label)}</span>`;
    const linkAria = isCurrent ? ` aria-current="step"` : "";
    const action = isLocked
      ? `<span class="flow-link" role="link" aria-label="${escapeHtml(step.label)} - locked" aria-disabled="true" tabindex="-1">${title}${hint}</span>`
      : `<a href="${step.route}" data-link class="flow-link"${linkAria}>${title}${hint}</a>`;
    return `<li class="${classes}"><span class="flow-step-index">${index + 1}</span>${action}</li>`;
  }).join("");
}

function refreshProgressUI(page = pageFromPath()) {
  updateFlowRail(page);
  const progressTrack = document.querySelector(".coach .progress-track");
  if (progressTrack) {
    progressTrack.outerHTML = renderProgressTrack(page);
  }
}

function setBusy(button, busyText = "Working...") {
  if (!button) return null;
  if (button.classList.contains("busy")) return null;
  const alreadyDisabled = button.disabled;
  const previousText = button.textContent;
  button.disabled = true;
  button.classList.add("busy");
  if (busyText) button.textContent = busyText;
  return () => {
    button.disabled = alreadyDisabled;
    button.classList.remove("busy");
    button.textContent = previousText;
  };
}

function withBusyAction(buttonId, busyText, fn) {
  const button = el(buttonId);
  if (!button || button.disabled) return Promise.resolve();
  const release = setBusy(button, busyText);
  return fn()
    .catch((error) => {
      throw error;
    })
    .finally(() => {
      if (release) release();
    });
}

function renderStart() {
  const nextHref = readiness.level === "red" ? "/bank" : "/collide";
  const nextLabel = readiness.level === "red" ? "Open Spark Bank" : "Generate First Move";
  return `
    ${coachPanel("start")}
    <div class="page-grid">
      <section class="panel readiness-board">
        <div>
          <h2>Your bank is <span class="${readiness.level}-text">${escapeHtml(readiness.label.toLowerCase())}</span></h2>
          <p>${escapeHtml(readiness.next_action)}.</p>
        </div>
        ${renderStartLaunchStrip(nextHref, nextLabel)}
        ${trafficLights()}
        <div class="meter-grid">
          <div class="meter"><strong>${readiness.total}</strong><span>Total ingredients</span></div>
          <div class="meter"><strong>${readiness.populated_categories}</strong><span>Active categories</span></div>
          <div class="meter"><strong>${favourites.length}</strong><span>Saved sparks</span></div>
          <div class="meter"><strong>${readiness.level.toUpperCase()}</strong><span>Readiness</span></div>
        </div>
        <div class="action-row">
          <a class="button-link primary" href="${nextHref}" data-link>${nextLabel}</a>
          <a class="button-link" href="/bank" data-link>Edit Bank</a>
        </div>
      </section>
      <aside class="panel flat bank-sidebar">
        <div class="visual-card visual-card-lab" aria-hidden="true"></div>
        <h3>Next useful move</h3>
        <p>${escapeHtml(nextMove())}</p>
        <div class="quick-add">
          <label class="field">Quick add
            <select id="quickCategoryInput">
              ${bankKeys.map((key) => `<option value="${key}">${labelFor(key)}</option>`).join("")}
            </select>
          </label>
          <label class="field">Ingredient
            <input id="quickIdeaInput" type="text" placeholder="type one raw idea" autofocus />
          </label>
          <button id="quickAddButton" class="primary">Add Ingredient</button>
          <p class="message" role="status" aria-live="polite" id="quickAddMessage">${escapeHtml(transientMessage)}</p>
        </div>
        <div class="action-row">
          <button id="quickCollisionButton" class="cyan" ${readiness.level === "red" ? "disabled" : ""}>Quick First Move</button>
          <button id="blankBankButton">Blank Bank</button>
          <button id="starterBankButton">Starter Bank</button>
        </div>
        ${readiness.level === "red" ? "<p class=\"message\" role=\"status\" aria-live=\"polite\">Add ingredients first so the engine can make a useful first move.</p>" : ""}
      </aside>
    </div>
  `;
}

function renderStartLaunchStrip(nextHref, nextLabel) {
  const launchCopy = readiness.level === "red"
    ? "Feed the bank with a few rough scraps. The red light means ProMentum is waiting for material."
    : readiness.level === "amber"
      ? "You have enough for a first spark. Generate now, then save the parts that make you lean forward."
      : "Strong bank. Generate first moves, keep the best sparks, and use the library as your idea shelf.";
  const steps = [
    ["red", "Feed", "Add raw scraps"],
    ["amber", "Generate", nextLabel],
    ["green", "Keep", "Save the spark"],
  ];
  return `
    <div class="start-launch-strip">
      <div class="start-launch-copy">
        <h3>Build momentum without losing the plot</h3>
        <p>${escapeHtml(launchCopy)}</p>
        <div class="launch-chip-row" aria-label="Start page guidance">
          ${steps.map(([level, label, text]) => `
            <a class="launch-chip ${level} ${readiness.level === level ? "active" : ""}" href="${level === "red" ? "/bank" : nextHref}" data-link>
              <span class="status-dot ${level}"></span>
              <strong>${escapeHtml(label)}</strong>
              <span>${escapeHtml(text)}</span>
            </a>
          `).join("")}
        </div>
      </div>
      <div class="start-console-art" aria-hidden="true"></div>
    </div>
  `;
}

function trafficLights() {
  const levels = [
    ["red", "Needs fuel", "Add more raw material."],
    ["amber", "Enough to try", "The machine can spark."],
    ["green", "Ready", "Strong bank. Generate now."],
  ];
  return `<div class="traffic">${levels
    .map(([level, label, text]) => `
      <div class="traffic-step ${readiness.level === level ? "active" : ""}">
        <span class="status-dot ${level}"></span>
        <strong>${label}</strong>
        <span>${text}</span>
      </div>
    `)
    .join("")}</div>`;
}

function coachPanel(pageKey) {
  const meta = pageMeta[pageKey];
  const isCompact = true;
  const quickAction = pageKey === "start" && readiness.level === "red"
    ? { label: "Add a first idea", link: "/bank" }
    : pageKey === "collide" && readiness.level === "red"
      ? { label: "Add ingredients", link: "/bank" }
      : null;
  const tips = (meta.tips || []).map((tip) => `<li>${escapeHtml(tip)}</li>`).join("");
  const tipBlock = `<details class="coach-details"><summary>Quick tips</summary><ol class="guide-list">${tips}</ol></details>`;
  const coachAction = pageKey === "collide"
    ? `<button class="button-link" id="coachGenerateButton" ${readiness.level === "red" ? "disabled" : ""}>${escapeHtml(meta.actionText)}</button>`
    : pageKey === "settings"
      ? `<button class="button-link" id="coachStorageCheckButton">${escapeHtml(meta.actionText)}</button>`
    : `<a class="button-link" href="${meta.actionLink}" data-link>${escapeHtml(meta.actionText)}</a>`;
  return `
    <section class="coach panel coach-compact coach-${escapeHtml(pageKey)}">
      <p class="coach-step">Step ${escapeHtml(meta.stage)}</p>
      <h2>${escapeHtml(meta.title)} flow</h2>
      <p>${escapeHtml(meta.cue)}</p>
      <p class="coach-goal">${escapeHtml(meta.goal)}</p>
      ${renderProgressTrack(pageKey)}
      ${tipBlock}
      <div class="coach-row">
        ${quickAction ? `<a class="button-link primary" href="${quickAction.link}" data-link>${escapeHtml(quickAction.label)}</a>` : ""}
        ${coachAction}
      </div>
    </section>
  `;
}

function renderProgressTrack(_pageKey) {
  const hasStorageCheck = hasCheckedStorage();
  const steps = [
    { key: "start", label: "Start", done: true },
    { key: "bank", label: "Build Bank", done: (readiness.total || 0) > 0 },
    { key: "collide", label: "Generate first move", done: Boolean(currentResult) },
    { key: "library", label: "Save a spark", done: (favourites || []).length > 0 },
    { key: "settings", label: "Check storage", done: hasStorageCheck },
  ];
  const firstIncomplete = steps.findIndex((entry) => !entry.done);
  const activeIndex = firstIncomplete === -1 ? -1 : firstIncomplete;
  if (steps[activeIndex]) {
    steps[activeIndex].isCurrent = true;
  }
  const markers = steps
    .map((entry, index) => `
      <span class="progress-chip ${entry.done ? "done" : ""} ${entry.isCurrent ? "current" : ""}" aria-label="${escapeHtml(entry.label)} step${entry.done ? " complete" : entry.isCurrent ? " current" : ""}">
        ${escapeHtml(String(index + 1))}. ${escapeHtml(entry.label)}
      </span>
    `).join("");
  return `<div class="progress-track" role="list" aria-label="Session progress">${markers}</div>`;
}

function hasCheckedStorage() {
  try {
    return Boolean(localStorage.getItem("ideaColliderCheckedDoctor"));
  } catch {
    return false;
  }
}

function nextMove() {
  if (readiness.level === "red") return "Add a few ideas, phrases, people, and places. The lights will change as the bank gets usable.";
  if (readiness.level === "amber") return "Generate a first move, then add anything that feels missing. The app gets better when the bank sounds like you.";
  return "Go to the Generate page and choose the kind of spark you want.";
}

function statusCardRows() {
  const counts = bankKeys.map((key) => ({ key, count: (appState[key] || []).length }));
  const rich = [...counts].sort((a, b) => b.count - a.count)[0];
  const weak = [...counts].sort((a, b) => a.count - b.count)[0];
  return `
    <div class="meter-grid compact">
      ${counts
        .map(
          (entry) => `
            <div class="meter">
              <strong>${entry.count}</strong>
              <span>${labelFor(entry.key)}</span>
            </div>
          `,
        )
        .join("")}
    </div>
    <p class="micro-hint">
      ${escapeHtml(`Strongest: ${labelFor(rich?.key || "ideas")} (${rich?.count || 0}); Lowest: ${labelFor(weak?.key || "ideas")} (${weak?.count || 0})`)}
    </p>
  `;
}

function bankTextStats(value) {
  const lines = String(value || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const unique = new Set(lines.map((line) => line.toLowerCase()));
  const longLines = lines.filter((line) => line.length > 96).length;
  return {
    count: lines.length,
    unique: unique.size,
    duplicates: lines.length - unique.size,
    longLines,
  };
}

function bankPulseClass(stats) {
  if (!stats.count) return "red";
  if (stats.count < 3 || stats.duplicates || stats.longLines) return "amber";
  return "green";
}

function bankPulseLabel(stats) {
  if (!stats.count) return "Needs first line";
  if (stats.duplicates) return `${stats.duplicates} duplicate${stats.duplicates === 1 ? "" : "s"}`;
  if (stats.longLines) return `${stats.longLines} long line${stats.longLines === 1 ? "" : "s"}`;
  if (stats.count < 3) return "Add a little more";
  return "Category ready";
}

function bankPulseHint(stats) {
  if (!stats.count) return "Add one short line to wake up this category.";
  if (stats.duplicates) return "Clean Duplicates will tidy repeated lines.";
  if (stats.longLines) return "Shorter lines spark more cleanly.";
  if (stats.count < 3) return "Three or more lines gives the engine better choice.";
  return "Good shape. Save Bank when you are done.";
}

function renderBankPulse(stats) {
  return `
    <div class="bank-editor-pulse ${bankPulseClass(stats)}" id="bankEditorPulse" aria-live="polite">
      <strong>${escapeHtml(String(stats.count))}</strong>
      <span>${escapeHtml(bankPulseLabel(stats))}</span>
    </div>
  `;
}

function renderBankCategoryGuide(key) {
  const guide = BANK_CATEGORY_GUIDES[key] || BANK_CATEGORY_GUIDES.ideas;
  return `
    <div class="bank-category-guide" id="bankCategoryGuide">
      <div class="bank-guide-item">
        <span>Aim</span>
        <strong>${escapeHtml(guide.aim)}</strong>
      </div>
      <div class="bank-guide-item">
        <span>Good line</span>
        <strong>${escapeHtml(guide.good)}</strong>
      </div>
      <div class="bank-guide-item">
        <span>Watch out</span>
        <strong>${escapeHtml(guide.avoid)}</strong>
      </div>
      <div class="bank-example-list" aria-label="Example line shapes">
        ${(guide.examples || []).map((example) => `<span class="bank-example-chip">${escapeHtml(example)}</span>`).join("")}
      </div>
    </div>
  `;
}

function renderBank() {
  const activeText = (appState[activeBankKey] || []).join("\n");
  const activeStats = bankTextStats(activeText);
  return `
    ${coachPanel("bank")}
    <div class="page-grid">
      <section class="panel">
        <div class="quick-add bank-quick-add">
          <label class="field">Add to category
            <select id="bankQuickCategoryInput">
              ${bankKeys.map((key) => `<option value="${key}" ${key === activeBankKey ? "selected" : ""}>${labelFor(key)}</option>`).join("")}
            </select>
          </label>
           <label class="field">New ingredient
             <input id="bankQuickIdeaInput" type="text" placeholder="one phrase, object, question, or half-joke" autofocus />
           </label>
          <button id="bankQuickAddButton" class="primary">Add</button>
        </div>
        <div class="bank-layout">
          <div class="bank-tabs" role="tablist" aria-label="Idea bank categories">
            ${bankKeys
              .map(
                (key) =>
                  `<button data-bank-tab="${key}" role="tab" aria-selected="${key === activeBankKey}" aria-controls="bank-editor-panel" class="${key === activeBankKey ? "active" : ""}">
                    ${labelFor(key)} <span>${(appState[key] || []).length}</span>
                  </button>`,
              )
              .join("")}
          </div>
          <div class="editor-panel">
            <div class="editor-heading-row">
              <div>
                <h2 id="bank-editor-panel">${labelFor(activeBankKey)}</h2>
                <p>One ingredient per line. Keep the wording yours.</p>
              </div>
              ${renderBankPulse(activeStats)}
            </div>
            ${renderBankCategoryGuide(activeBankKey)}
            <p class="micro-hint bank-live-hint" id="bankLiveHint">${escapeHtml(bankPulseHint(activeStats))}</p>
            <textarea id="bankText">${escapeHtml(activeText)}</textarea>
            <div class="button-row compact">
              <button id="saveBankButton" class="primary">Save Bank</button>
              <button id="dedupeBankButton">Clean Duplicates</button>
              <button id="resetBankButton" class="danger">Reset Starter Bank</button>
              <button id="blankBankFromBankButton" class="danger">Blank Bank</button>
              <a class="button-link" href="/collide" data-link>Go To Generate</a>
            </div>
            <p class="message" role="status" aria-live="polite" id="bankMessage">${escapeHtml(transientMessage)}</p>
          </div>
        </div>
      </section>
      <aside class="panel flat bank-health-panel">
        <div class="visual-card visual-card-bank" aria-hidden="true"></div>
        <h3>Current bank health</h3>
        <p class="micro-hint">Use this panel as a quick check before generating.</p>
        ${statusCardRows()}
      </aside>
    </div>
  `;
}

function renderCollide() {
  const readyToCollide = readiness.level !== "red";
  const hasResultHistory = Boolean(currentResult);
  const modeOptions = modes.map((mode) => `<option>${escapeHtml(mode)}</option>`).join("");
  const collideMessage = collideStatusText(readyToCollide, hasResultHistory);
  const initialMode = modes[0] || "Random Spark";
  return `
    ${coachPanel("collide")}
    <div class="page-grid">
      <section class="panel">
        <h2>Choose the push</h2>
        <p>The same seed gives the same spark. Raise weirdness when the bank feels too sensible.</p>
        <div class="form-grid result-section">
          <label class="field">Mode<select id="modeInput">${modeOptions}</select></label>
          <label class="field">Ingredients<input id="ingredientInput" type="number" min="3" max="7" value="5" /></label>
          <label class="field field-range">Weirdness <span class="range-meta"><output id="weirdnessValue" for="weirdnessInput">55</output></span><input id="weirdnessInput" type="range" min="0" max="100" value="55" /></label>
          <label class="field">Seed<input id="seedInput" type="text" inputmode="numeric" placeholder="auto (blank = random)" autofocus /></label>
        </div>
        <div class="button-row">
          <button id="collideButton" class="primary" ${readyToCollide ? "" : "disabled"}>Generate First Move</button>
          <button id="sameSeedButton" ${readyToCollide && hasResultHistory ? "" : "disabled"}>Regenerate Same Seed</button>
        </div>
        <p class="message" role="status" aria-live="polite" id="collideMessage">${escapeHtml(collideMessage)}</p>
      </section>
      <aside class="panel flat collision-guide">
        <div id="collisionPreview" aria-live="polite">
          ${renderCollisionPreview({ mode: initialMode, weirdness: 55, ingredientCount: 5, seed: "" })}
        </div>
        <div class="mini-readiness">
          <h3>Bank readiness</h3>
          <p>${escapeHtml(readiness.next_action)}.</p>
          ${trafficLights()}
        </div>
      </aside>
    </div>
  `;
}

function renderCollisionPreview({ mode, weirdness, ingredientCount, seed }) {
  const guide = MODE_GUIDES[mode] || MODE_GUIDES["Concept Mashup"];
  const band = weirdnessBand(weirdness);
  const seedInfo = seedPreview(seed);
  const castSize = ingredientPace(ingredientCount);
  return `
    <div class="collision-preview-card">
      <p class="result-kicker">Run preview</p>
      <h3>${escapeHtml(guide.label)}</h3>
      <p>${escapeHtml(guide.copy)}</p>
      <div class="preview-stack">
        <div class="preview-row">
          <span class="preview-dot ${escapeHtml(band.className)}"></span>
          <div><strong>${escapeHtml(band.label)}</strong><span>${escapeHtml(band.copy)}</span></div>
        </div>
        <div class="preview-row">
          <span class="preview-dot ingredients"></span>
          <div><strong>${escapeHtml(castSize.label)}</strong><span>${escapeHtml(castSize.copy)}</span></div>
        </div>
        <div class="preview-row">
          <span class="preview-dot ${escapeHtml(seedInfo.className)}"></span>
          <div><strong>${escapeHtml(seedInfo.label)}</strong><span>${escapeHtml(seedInfo.copy)}</span></div>
        </div>
      </div>
      <p class="preview-outcome">${escapeHtml(guide.output)}</p>
    </div>
  `;
}

function weirdnessBand(value) {
  const weirdness = normalizeNumber(value, 0, 100, 55);
  if (weirdness < 34) {
    return {
      className: "grounded",
      label: `Grounded ${weirdness}`,
      copy: "Cleaner premise, fewer sideways jumps.",
    };
  }
  if (weirdness < 72) {
    return {
      className: "tilted",
      label: `Tilted ${weirdness}`,
      copy: "Enough drift to surprise you while staying usable.",
    };
  }
  return {
    className: "wild",
    label: `Wild ${weirdness}`,
    copy: "Bigger leaps, stronger odd logic, less respect for normal.",
  };
}

function ingredientPace(value) {
  const count = normalizeNumber(value, 3, 7, 5);
  if (count <= 3) {
    return { label: `${count} ingredients`, copy: "Tight, focused, easier to turn into one scene." };
  }
  if (count <= 5) {
    return { label: `${count} ingredients`, copy: "Balanced mix: enough pressure without losing the thread." };
  }
  return { label: `${count} ingredients`, copy: "Crowded and lively; expect more accidental connections." };
}

function seedPreview(value) {
  const rawSeed = String(value || "").trim();
  if (!rawSeed) {
    return { className: "auto", label: "Auto seed", copy: "A fresh seed will be picked when you generate." };
  }
  if (!normalizeSeed(rawSeed)) {
    return { className: "invalid", label: "Seed needs a number", copy: "Use whole numbers only, or leave it blank." };
  }
  return { className: "locked", label: `Seed ${normalizeSeed(rawSeed)}`, copy: "Locked runs can be repeated and compared." };
}

function renderResult() {
  const hasSavedCount = favourites.length;
  if (!currentResult) {
    return `
      ${coachPanel("result")}
      <section class="empty-state empty-state-visual">
        <div class="empty-art empty-art-collider" aria-hidden="true"></div>
        <div>
          <h2>No first move yet</h2>
          <p>Generate one on the Generate page. The result will land here.</p>
          <div class="action-row"><a class="button-link primary" id="openColliderButton" href="/collide" data-link>Open Generate</a></div>
        </div>
      </section>
    `;
  }
  return `
    ${coachPanel("result")}
    <section class="panel result-panel">
      <div class="result-hero">
        <div class="result-heading">
          <p class="result-kicker">Fresh first move</p>
          <h2 class="result-title">${escapeHtml(currentResult.title)}</h2>
          <div class="result-meta-pills">
            <span>${escapeHtml(currentResult.mode || "Spark")}</span>
            <span>Seed ${escapeHtml(currentResult.seed)}</span>
            <span>Weirdness ${escapeHtml(currentResult.weirdness)}</span>
            <span>${escapeHtml(currentResult.ingredient_count || 0)} ingredients</span>
          </div>
        </div>
        <aside class="result-hook-card" aria-label="Best hook">
          <span class="result-hook-label">Best hook</span>
          <p>${escapeHtml(currentResult.best_hook)}</p>
        </aside>
      </div>
      ${renderResultUseMap(currentResult)}
      <div class="result-actions">
        <section class="action-group action-group-primary">
          <h3>Keep this result</h3>
          <p class="micro-hint">Save the keeper first, then copy or export what you want to use.</p>
          <div class="button-row">
            <button id="saveFavouriteButton" class="primary">Save Favourite</button>
            <button id="copyResultButton">Copy Output</button>
            <button id="copyHookButton">Copy Hook</button>
            <button id="exportTxtButton">Export TXT</button>
            <button id="exportHtmlButton">Export HTML</button>
            <button id="openExportsButton" ${lastExportPath ? "" : "disabled"}>Open Exports Folder</button>
          </div>
        </section>
        <section class="action-group">
          <h3>Shape the output</h3>
          <p class="micro-hint">Use one pass to get fresh energy without losing what made this work.</p>
          <div class="button-row">
            <button id="variantButton" class="cyan">Regenerate Variant</button>
            <button id="sameIngredientsButton">Keep Same Ingredients</button>
            <button id="lockBestButton">Lock Best Ingredient</button>
            <button id="copyRecipeButton">Copy Seed Recipe</button>
          </div>
        </section>
      </div>
      ${renderResultHandoffPanel()}
      <p class="message" role="status" aria-live="polite" id="resultMessage">${lastExportPath ? `Latest export: ${escapeHtml(_fileNameFromPath(lastExportPath))}` : ""}</p>
      <textarea id="copyFallback" class="copy-fallback" readonly hidden></textarea>
      <div class="result-section">
        <h3>Ingredients Used</h3>
        <div class="ingredient-list">${(currentResult.ingredients || []).map((item) => `
          <span class="ingredient-chip">${escapeHtml(labelFor(item.category))}: ${escapeHtml(item.text)}</span>
        `).join("")}</div>
      </div>
      <div class="result-section">
        <h3>Hooks</h3>
        <ul>${currentResult.hooks.map((hook) => `<li>${escapeHtml(hook)}</li>`).join("")}</ul>
      </div>
      <div class="result-section">
        <h3>What This Could Become</h3>
        <p>${escapeHtml(currentResult.expanded_concept)}</p>
      </div>
      <div class="result-section">
        <h3>Next Moves</h3>
        <ul>${(currentResult.next_steps || []).map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ul>
      </div>
      <div class="result-section">
        <h3>Scene Or Format Seed</h3>
        <p>${escapeHtml(currentResult.sketch_seed)}</p>
      </div>
      <div class="result-section">
        <h3>Why This Happened</h3>
          <details class="result-details">
          <summary>Show trace details</summary>
          <div class="trace-list">${currentResult.trace_lines.map((line) => `<div>${escapeHtml(line)}</div>`).join("")}</div>
        </details>
      </div>
      <div class="result-section">
        <h3>Saved Sparks</h3>
        <p>${hasSavedCount ? `${hasSavedCount} saved result${hasSavedCount === 1 ? "" : "s"} available in Library.` : "No saved sparks yet."}</p>
      </div>
    </section>
  `;
}

function renderResultUseMap(result) {
  const nextMove = (result.next_steps || [])[0] || "Pick the part that made you grin and write one rough version.";
  const bestIngredient = result.best_ingredient?.text || (result.ingredients || [])[0]?.text || "the strongest ingredient";
  return `
    <div class="result-use-map" aria-label="Use this spark">
      <article class="result-use-card result-use-card-primary">
        <span class="result-use-number">1</span>
        <div>
          <h3>Start with the hook</h3>
          <p>${escapeHtml(result.best_hook || "Choose the line that feels alive.")}</p>
        </div>
      </article>
      <article class="result-use-card">
        <span class="result-use-number">2</span>
        <div>
          <h3>Shape the format</h3>
          <p>${escapeHtml(resultModeNudge(result.mode, bestIngredient))}</p>
        </div>
      </article>
      <article class="result-use-card">
        <span class="result-use-number">3</span>
        <div>
          <h3>Do the tiny move</h3>
          <p>${escapeHtml(nextMove)}</p>
        </div>
      </article>
    </div>
  `;
}

function renderResultHandoffPanel() {
  const saved = isCurrentResultSaved();
  const copied = Boolean(lastCopyAction);
  const exported = Boolean(lastExportPath);
  const exportName = exported ? _fileNameFromPath(lastExportPath) : "No file exported yet";
  const exportFormat = exportName.toLowerCase().endsWith(".html") ? "HTML" : "TXT";
  const copyLabel = lastCopyAction?.kind === "copy-hook"
    ? "Hook copied"
    : lastCopyAction?.kind === "copy-recipe"
      ? "Recipe copied"
      : copied
        ? "Output copied"
        : "Copy when ready";
  return `
    <div class="result-handoff-panel" id="resultHandoffPanel" aria-live="polite">
      ${renderHandoffCard({
        tone: saved ? "green" : "amber",
        title: saved ? "Saved in Library" : "Save first",
        copy: saved ? `${favourites.length} saved spark${favourites.length === 1 ? "" : "s"} in your library.` : "Keep the keeper before you make another variant.",
        status: saved ? "Done" : "Next",
      })}
      ${renderHandoffCard({
        tone: copied ? "green" : "cyan",
        title: copyLabel,
        copy: copied ? "Clipboard has the bit you just chose." : "Copy the full output, hook, or recipe when you need it.",
        status: copied ? "Ready" : "Optional",
      })}
      ${renderHandoffCard({
        tone: exported ? "green" : "cyan",
        title: exported ? `Exported ${exportFormat}` : "Export a file",
        copy: exported ? exportName : "TXT is plain and fast. HTML is nicer for sharing.",
        status: exported ? "File ready" : "Optional",
        detail: exported ? `<details class="result-export-path"><summary>Full path</summary><code>${escapeHtml(lastExportPath)}</code></details>` : "",
      })}
    </div>
  `;
}

function renderHandoffCard({ tone, title, copy, status, detail = "" }) {
  return `
    <article class="handoff-card ${tone}">
      <span class="status-dot ${tone}"></span>
      <div>
        <div class="handoff-card-heading">
          <h3>${escapeHtml(title)}</h3>
          <span>${escapeHtml(status)}</span>
        </div>
        <p>${escapeHtml(copy)}</p>
        ${detail}
      </div>
    </article>
  `;
}

function isCurrentResultSaved() {
  if (!currentResult) return false;
  const current = resultIdentity(currentResult);
  return favourites.some((item) => resultIdentity(item.result || item) === current);
}

function resultIdentity(result) {
  return [result?.title, result?.seed, result?.best_hook].map((part) => String(part ?? "")).join("::");
}

function markResultAction(kind, message) {
  lastResultAction = { kind, message, at: Date.now() };
  if (kind.startsWith("copy")) {
    lastCopyAction = lastResultAction;
  }
  const panel = el("resultHandoffPanel");
  if (panel) panel.outerHTML = renderResultHandoffPanel();
  setResultMessage(message);
}

function setResultMessage(message) {
  const target = el("resultMessage");
  if (target) target.textContent = message;
}

function resultModeNudge(mode, bestIngredient) {
  const fallback = `Use ${bestIngredient} as the pressure point and make the smallest test version.`;
  const nudges = {
    "Sketch Hook": `Give ${bestIngredient} the first interruption, then write the first ten lines.`,
    "Video Idea": `Turn ${bestIngredient} into the opening image and make the thumbnail obvious.`,
    "Title Storm": `Keep the three titles that sound least sensible and test them out loud.`,
    "Scene Seed": `Put ${bestIngredient} in the room first and let everyone react badly.`,
    "Concept Mashup": `Make ${bestIngredient} the rule that forces the concept to exist.`,
    "Personal Myth": `Treat ${bestIngredient} like a private ritual and give it one visible object.`,
    "Serious To Absurd": `Explain ${bestIngredient} with total confidence until the logic starts wobbling.`,
    "Random Spark": fallback,
  };
  return nudges[mode] || fallback;
}

function renderLibrary() {
  const visible = filteredLibraryFavourites();
  return `
    ${coachPanel("library")}
    <section class="panel">
      <div class="section-heading-row">
        <div>
          <h2>Library</h2>
          <p>Saved favourites stay on this machine. Search by title, hook, mode, seed, or ingredient.</p>
        </div>
      </div>
      <div class="library-toolbar">
        <label class="field library-search">Search saved sparks
          <input id="librarySearchInput" type="search" placeholder="try myth, kettle, video, 12345..." value="${escapeHtml(librarySearch)}" autocomplete="off" />
        </label>
        <button id="clearLibrarySearchButton" ${librarySearch ? "" : "disabled"}>Clear Search</button>
        <button id="clearLibraryButton" class="danger" ${favourites.length ? "" : "disabled"}>Clear Library</button>
      </div>
      <div id="libraryStats">${renderLibraryStats(visible)}</div>
      <div class="result-section" id="libraryResults">${renderLibraryResults(visible)}</div>
      <p class="message" role="status" aria-live="polite" id="libraryMessage">${libraryStatusText(visible)}</p>
    </section>
  `;
}

function filteredLibraryFavourites() {
  const query = librarySearch.trim().toLowerCase();
  if (!query) return favourites;
  return favourites.filter((fav) => librarySearchText(fav).includes(query));
}

function librarySearchText(fav) {
  const result = fav.result || {};
  const ingredients = (result.ingredients || [])
    .map((item) => `${item.category || ""} ${item.text || ""}`)
    .join(" ");
  return [
    fav.title,
    fav.best_hook,
    fav.mode,
    fav.seed,
    fav.created_at,
    result.mode,
    result.seed,
    result.recipe,
    ingredients,
  ].join(" ").toLowerCase();
}

function renderLibraryStats(visible) {
  const modes = new Set(favourites.map((fav) => fav.mode || fav.result?.mode).filter(Boolean));
  const latest = favourites[0];
  return `
    <div class="library-stats meter-grid compact">
      <div class="meter"><strong>${favourites.length}</strong><span>Total saved</span></div>
      <div class="meter"><strong>${visible.length}</strong><span>Showing now</span></div>
      <div class="meter"><strong>${modes.size || 0}</strong><span>Modes saved</span></div>
      <div class="meter"><strong>${latest ? escapeHtml(String(latest.seed ?? latest.result?.seed ?? "auto")) : "-"}</strong><span>Latest seed</span></div>
    </div>
  `;
}

function renderLibraryResults(items) {
  if (!favourites.length) {
    return `<div class="empty-state empty-state-visual"><div class="empty-art empty-art-library" aria-hidden="true"></div><div><h2>No saved sparks yet</h2><p>Save a result when it feels worth keeping.</p><div class="action-row"><a class="button-link primary" href="/collide" data-link>Make First Spark</a></div></div></div>`;
  }
  if (!items.length) {
    return `<div class="empty-state empty-state-visual"><div class="empty-art empty-art-library" aria-hidden="true"></div><div><h2>No saved sparks match</h2><p>Clear the search or try a word from the title, mode, hook, seed, or ingredients.</p></div></div>`;
  }
  return `<div class="library-list">${items.map(renderLibraryItem).join("")}</div>`;
}

function renderLibraryItem(fav) {
  const result = fav.result || {};
  const mode = fav.mode || result.mode || "Saved";
  const seed = fav.seed ?? result.seed ?? "auto";
  const weirdness = result.weirdness ?? "";
  const ingredientCount = result.ingredient_count || (result.ingredients || []).length || "";
  return `
    <article class="library-item">
      <div class="library-item-main">
        <div>
          <p class="result-kicker">${escapeHtml(shortDate(fav.created_at))}</p>
          <strong>${escapeHtml(fav.title)}</strong>
          <div class="result-meta-pills library-meta">
            <span>${escapeHtml(mode)}</span>
            <span>Seed ${escapeHtml(seed)}</span>
            ${weirdness !== "" ? `<span>Weirdness ${escapeHtml(weirdness)}</span>` : ""}
            ${ingredientCount ? `<span>${escapeHtml(ingredientCount)} ingredients</span>` : ""}
          </div>
        </div>
        <p>${escapeHtml(fav.best_hook || "")}</p>
      </div>
      <div class="button-row">
        <button data-load-favourite="${escapeHtml(fav.id)}" class="primary">Load Result</button>
        <button data-copy-favourite-hook="${escapeHtml(fav.id)}">Copy Hook</button>
        <button class="danger" data-delete-favourite="${escapeHtml(fav.id)}">Delete</button>
      </div>
    </article>
  `;
}

function libraryStatusText(visible) {
  if (!favourites.length) return "Save a result to build your local spark library.";
  if (librarySearch.trim()) return `${visible.length} of ${favourites.length} saved sparks match "${librarySearch.trim()}".`;
  return "Tip: search saved sparks before deleting anything. Future you is forgetful.";
}

function shortDate(value) {
  if (!value) return "Saved locally";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Saved locally";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function updateLibraryView() {
  const visible = filteredLibraryFavourites();
  const stats = el("libraryStats");
  const results = el("libraryResults");
  const message = el("libraryMessage");
  const clearSearch = el("clearLibrarySearchButton");
  if (stats) stats.innerHTML = renderLibraryStats(visible);
  if (results) results.innerHTML = renderLibraryResults(visible);
  if (message) message.textContent = libraryStatusText(visible);
  if (clearSearch) clearSearch.disabled = !librarySearch;
  bindLibraryCards();
}

function renderSettings() {
  return `
    ${coachPanel("settings")}
    <section class="panel">
      <div class="section-heading-row">
        <div>
          <h2>Local settings</h2>
          <p>By default, this app prefers data in <code>D:\\ProMentumData</code> on Windows and falls back to the app folder. Set <code>PROMENTUM_HOME</code> to move it.</p>
        </div>
      </div>
      <div id="settingsHealthGrid">${renderSettingsHealthGrid()}</div>
      <div class="settings-path-panel result-section">
        <div>
          <h3>Local file map</h3>
          <p class="micro-hint">These are the exact folders and files the app is using on this machine.</p>
        </div>
        <div class="settings-path-list" id="settingsPathList">
          ${renderSettingsPathList()}
        </div>
      </div>
      <div class="button-row">
        <button id="openDataButton">Open Data Folder</button>
        <button id="openExportsButtonSettings">Open Exports Folder</button>
        <button id="refreshDoctorButton">Refresh Status</button>
        <button id="settingsResetButton" class="danger">Reset Starter Bank</button>
      </div>
      <p class="message" role="status" aria-live="polite" id="settingsMessage"></p>
    </section>
  `;
}

function renderSettingsHealthGrid(payload = null) {
  const doctor = payload?.doctor || {};
  const readinessInfo = doctor.readiness || {};
  const dataDir = doctor.data_dir || "Checking...";
  const dataTone = pathTone(dataDir);
  return `
    <div class="settings-health-grid">
      <article class="settings-health-card ${escapeHtml(dataTone)}">
        <span>Storage home</span>
        <strong>${escapeHtml(pathHomeLabel(dataDir))}</strong>
        <p>${escapeHtml(storageHomeHint(dataDir))}</p>
      </article>
      <article class="settings-health-card ${readinessInfo.level === "green" ? "green" : readinessInfo.level === "red" ? "red" : "amber"}">
        <span>Bank health</span>
        <strong>${escapeHtml(readinessInfo.label || "Checking")}</strong>
        <p>${escapeHtml(readinessInfo.next_action || "Refreshing local bank status.")}</p>
      </article>
      <article class="settings-health-card">
        <span>Saved sparks</span>
        <strong>${escapeHtml(String(doctor.favourite_count ?? "-"))}</strong>
        <p>Saved locally in your favourites file.</p>
      </article>
      <article class="settings-health-card green">
        <span>Runtime</span>
        <strong>${escapeHtml(payload?.version ? `v${payload.version}` : "Local only")}</strong>
        <p>${escapeHtml(payload?.python ? `Python ${payload.python}; browser uses 127.0.0.1.` : "No accounts, API keys, or cloud calls.")}</p>
      </article>
    </div>
  `;
}

function renderSettingsPathList(payload = null) {
  const doctor = payload?.doctor || {};
  const rows = [
    ["Data folder", doctor.data_dir],
    ["Idea bank", doctor.state_path],
    ["Favourites", doctor.favourites_path],
    ["Exports", doctor.exports_dir],
    ["Portable fallback", doctor.portable_default],
  ];
  return rows.map(([label, value]) => `
    <div class="settings-path-row">
      <span>${escapeHtml(label)}</span>
      <code>${escapeHtml(value || "Checking...")}</code>
    </div>
  `).join("");
}

function updateSettingsDoctor(payload) {
  const health = el("settingsHealthGrid");
  const pathList = el("settingsPathList");
  const dataPath = el("dataPath");
  if (health) health.innerHTML = renderSettingsHealthGrid(payload);
  if (pathList) pathList.innerHTML = renderSettingsPathList(payload);
  if (dataPath) dataPath.textContent = payload?.doctor?.data_dir || "";
}

function pathTone(path) {
  const value = String(path || "");
  if (/^d:[\\/]/i.test(value)) return "green";
  if (/^[a-z]:[\\/]/i.test(value)) return "amber";
  return value && value !== "Checking..." ? "green" : "amber";
}

function pathHomeLabel(path) {
  const value = String(path || "");
  const drive = value.match(/^([a-z]):[\\/]/i)?.[1]?.toUpperCase();
  if (drive) return `${drive}: drive`;
  if (value === "Checking...") return value;
  return "Portable/local";
}

function storageHomeHint(path) {
  const value = String(path || "");
  if (/^d:[\\/]/i.test(value)) return "Good: runtime data is on D drive.";
  if (/^[a-z]:[\\/]/i.test(value)) return "Set PROMENTUM_HOME to D:\\ProMentumData if you want this on D drive.";
  if (value === "Checking...") return "Refreshing storage location.";
  return "Using a portable folder beside the app.";
}

function bindPage(page) {
  if (page === "start") {
    el("quickCollisionButton")?.addEventListener("click", () => {
      if (readiness.level === "red") {
        transientMessage = "Add more ingredients before the first move.";
        const quickMessage = el("quickAddMessage");
        if (quickMessage) {
          quickMessage.textContent = transientMessage;
        }
        return;
      }
      runGenerate({});
    });
    el("quickAddButton")?.addEventListener("click", () => quickAddFrom("quickCategoryInput", "quickIdeaInput", "quickAddMessage"));
    el("quickIdeaInput")?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") quickAddFrom("quickCategoryInput", "quickIdeaInput", "quickAddMessage");
    });
    el("blankBankButton")?.addEventListener("click", () => resetBank("blank"));
    el("starterBankButton")?.addEventListener("click", () => resetBank(true));
  }
  if (page === "bank") bindBank();
  if (page === "collide") bindCollide();
  if (page === "result") bindResult();
  if (page === "library") bindLibrary();
  if (page === "settings") bindSettings();
}

function bindBank() {
  document.querySelectorAll("[data-bank-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      saveVisibleEditor(false);
      activeBankKey = button.dataset.bankTab;
      renderRoute();
    });
  });
  el("saveBankButton").addEventListener("click", () =>
    withBusyAction("saveBankButton", "Saving...", async () => {
      saveVisibleEditor(false);
      const data = await api("/api/state", { method: "POST", body: JSON.stringify({ state: appState }) });
      appState = data.state;
      readiness = data.readiness;
      updateShellStatus();
      el("bankMessage").textContent = "Bank saved.";
      renderRoute();
    }),
  );
  el("bankQuickAddButton").addEventListener("click", () => quickAddFrom("bankQuickCategoryInput", "bankQuickIdeaInput", "bankMessage"));
  el("bankQuickIdeaInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") quickAddFrom("bankQuickCategoryInput", "bankQuickIdeaInput", "bankMessage");
  });
  el("bankText")?.addEventListener("input", updateBankEditorPulse);
  el("dedupeBankButton").addEventListener("click", () =>
    withBusyAction("dedupeBankButton", "Cleaning...", async () => {
      saveVisibleEditor(false);
      let removed = 0;
      for (const key of bankKeys) {
        const seen = new Set();
        const cleaned = [];
        for (const item of appState[key] || []) {
          const normalized = item.trim().toLowerCase();
          if (seen.has(normalized)) {
            removed += 1;
            continue;
          }
          seen.add(normalized);
          cleaned.push(item);
        }
        appState[key] = cleaned;
      }
      const data = await api("/api/state", { method: "POST", body: JSON.stringify({ state: appState }) });
      appState = data.state;
      readiness = data.readiness;
      updateShellStatus();
      renderRoute();
      setTimeout(() => {
        const message = el("bankMessage");
        if (message) message.textContent = removed ? `Removed ${removed} duplicate lines.` : "No duplicates found.";
      }, 0);
    }),
  );
  el("resetBankButton").addEventListener("click", async () => {
    await resetBank(true);
  });
  el("blankBankFromBankButton").addEventListener("click", () => resetBank("blank"));
  updateBankEditorPulse();
}

function updateBankEditorPulse() {
  const text = el("bankText");
  const pulse = el("bankEditorPulse");
  const hint = el("bankLiveHint");
  if (!text || !pulse) return;
  const stats = bankTextStats(text.value);
  pulse.className = `bank-editor-pulse ${bankPulseClass(stats)}`;
  pulse.innerHTML = `<strong>${escapeHtml(String(stats.count))}</strong><span>${escapeHtml(bankPulseLabel(stats))}</span>`;
  if (hint) hint.textContent = bankPulseHint(stats);
  const tabCount = document.querySelector(`[data-bank-tab="${activeBankKey}"] span`);
  if (tabCount) tabCount.textContent = String(stats.count);
}

function bindCollide() {
  const readyToCollide = readiness.level !== "red";
  const weird = el("weirdnessInput");
  const weirdValue = el("weirdnessValue");
  weirdValue.textContent = weird.value;
  weird.addEventListener("input", () => {
    weirdValue.textContent = weird.value;
    const message = collideStatusText(readyToCollide, Boolean(currentResult));
    const collideMessage = el("collideMessage");
    if (collideMessage) {
      collideMessage.textContent = message;
    }
    updateCollisionPreview();
  });
  ["modeInput", "ingredientInput", "seedInput"].forEach((id) => {
    el(id)?.addEventListener("input", updateCollisionPreview);
    el(id)?.addEventListener("change", updateCollisionPreview);
  });
  el("collideButton").addEventListener("click", () =>
    withBusyAction("collideButton", "Generating...", () => runGenerateFromInputs(false)),
  );
  el("coachGenerateButton")?.addEventListener("click", () =>
    withBusyAction("coachGenerateButton", "Generating...", () => runGenerateFromInputs(false)),
  );
  el("sameSeedButton").addEventListener("click", () =>
    withBusyAction("sameSeedButton", "Re-running...", () => runGenerateFromInputs(true)),
  );
  el("seedInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      if (!el("collideButton").disabled) {
        el("collideButton").click();
      }
    }
  });
  updateCollisionPreview();
}

function updateCollisionPreview() {
  const preview = el("collisionPreview");
  if (!preview) return;
  preview.innerHTML = renderCollisionPreview({
    mode: el("modeInput")?.value || modes[0] || "Random Spark",
    weirdness: el("weirdnessInput")?.value || 55,
    ingredientCount: el("ingredientInput")?.value || 5,
    seed: el("seedInput")?.value || "",
  });
}

function bindResult() {
  if (!currentResult) return;
  el("variantButton").addEventListener("click", () =>
    withBusyAction("variantButton", "Brewing variant...", () => runGenerate(resultVariantOptions({ keepIngredients: false }))),
  );
  el("sameIngredientsButton").addEventListener("click", () =>
    withBusyAction("sameIngredientsButton", "Brewing variant...", () => runGenerate(resultVariantOptions({ keepIngredients: true }))),
  );
  el("lockBestButton").addEventListener("click", () =>
    withBusyAction("lockBestButton", "Locking ingredient...", () => runGenerate(resultVariantOptions({ lockBest: true }))),
  );
  el("copyResultButton").addEventListener("click", () =>
    withBusyAction("copyResultButton", "Copying...", () => copyText(currentResult.text, "Copied output.", "copy-output")),
  );
  el("copyHookButton").addEventListener("click", () =>
    withBusyAction(
      "copyHookButton",
      "Copying...",
      () => copyText(currentResult.best_hook + "\n\n" + currentResult.recipe, "Copied best hook.", "copy-hook"),
    ),
  );
  el("copyRecipeButton").addEventListener("click", () =>
    withBusyAction("copyRecipeButton", "Copying...", () => copyText(currentResult.recipe, "Copied seed recipe.", "copy-recipe")),
  );
  el("saveFavouriteButton").addEventListener("click", () => withBusyAction("saveFavouriteButton", "Saving...", saveFavourite));
  el("exportTxtButton").addEventListener("click", () => withBusyAction("exportTxtButton", "Exporting...", () => exportResult("txt")));
  el("exportHtmlButton").addEventListener("click", () => withBusyAction("exportHtmlButton", "Exporting...", () => exportResult("html")));
  el("openExportsButton")?.addEventListener("click", openExportsFolder);
}

async function quickAddFrom(categoryId, inputId, messageId) {
  const categoryInput = el(categoryId);
  const input = el(inputId);
  const message = el(messageId);
  const text = input.value.trim();
  if (!text) {
    if (message) message.textContent = "Type one ingredient first.";
    return;
  }
  const category = categoryInput.value;
  appState[category] = [...(appState[category] || []), text];
  const data = await api("/api/state", { method: "POST", body: JSON.stringify({ state: appState }) });
  appState = data.state;
  readiness = data.readiness;
  activeBankKey = category;
  input.value = "";
  updateShellStatus();
  transientMessage = `Added to ${labelFor(category)}.`;
  if (message) message.textContent = transientMessage;
  renderRoute();
}

async function resetBank(mode) {
  const data = await api("/api/state", { method: "POST", body: JSON.stringify({ reset: mode }) });
  appState = data.state;
  readiness = data.readiness;
  activeBankKey = "ideas";
  currentResult = null;
  lastExportPath = null;
  lastResultAction = null;
  lastCopyAction = null;
  persistResult();
  transientMessage = mode === "blank" ? "Blank bank ready. Add a few raw ingredients." : "Starter bank restored.";
  updateShellStatus();
  renderRoute();
}

function bindLibrary() {
  const searchInput = el("librarySearchInput");
  searchInput?.addEventListener("input", () => {
    librarySearch = searchInput.value;
    updateLibraryView();
  });
  el("clearLibrarySearchButton")?.addEventListener("click", () => {
    librarySearch = "";
    if (searchInput) {
      searchInput.value = "";
      searchInput.focus();
    }
    updateLibraryView();
  });
  bindLibraryCards();
  el("clearLibraryButton")?.addEventListener("click", async () => {
    if (!favourites.length || !confirm("Clear all saved sparks?")) return;
    const data = await api("/api/favourites", { method: "DELETE", body: JSON.stringify({ clear: true }) });
    favourites = data.favourites || [];
    librarySearch = "";
    renderRoute();
    const message = el("libraryMessage");
    if (message) message.textContent = "Library cleared.";
  });
}

function bindLibraryCards() {
  document.querySelectorAll("[data-load-favourite]").forEach((button) => {
    button.addEventListener("click", () => {
      const fav = favourites.find((item) => item.id === button.dataset.loadFavourite);
      if (!fav) return;
      currentResult = fav.result;
      persistResult();
      navigate("/result");
    });
  });
  document.querySelectorAll("[data-copy-favourite-hook]").forEach((button) => {
    button.addEventListener("click", async () => {
      const fav = favourites.find((item) => item.id === button.dataset.copyFavouriteHook);
      if (!fav) return;
      await copyLibraryText(`${fav.best_hook || ""}\n\n${fav.result?.recipe || ""}`.trim(), "Copied hook from library.");
    });
  });
  document.querySelectorAll("[data-delete-favourite]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.deleteFavourite;
      if (!id || !confirm("Delete this saved spark?")) return;
      const data = await api("/api/favourites", { method: "DELETE", body: JSON.stringify({ id }) });
      favourites = data.favourites || [];
      updateLibraryView();
      const message = el("libraryMessage");
      if (message) message.textContent = `Deleted spark from library. ${favourites.length ? libraryStatusText(filteredLibraryFavourites()) : "Library is empty."}`;
    });
  });
}

async function copyLibraryText(text, successMessage) {
  const message = el("libraryMessage");
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      throw new Error("Clipboard unavailable");
    }
    if (message) message.textContent = successMessage;
  } catch {
    if (message) message.textContent = "Clipboard blocked. Load the result and copy it there.";
  }
}

async function bindSettings() {
  await refreshDoctor();
  el("coachStorageCheckButton")?.addEventListener("click", () =>
    withBusyAction("coachStorageCheckButton", "Checking...", refreshDoctor),
  );
  el("refreshDoctorButton").addEventListener("click", () =>
    withBusyAction("refreshDoctorButton", "Checking...", refreshDoctor),
  );
  el("openDataButton").addEventListener("click", () =>
    withBusyAction("openDataButton", "Opening...", async () => {
      const data = await api("/api/open-data", { method: "POST", body: "{}" });
      el("settingsMessage").textContent = data.data_folder.opened ? `Opened ${data.data_folder.path}` : data.data_folder.error;
    }),
  );
  el("openExportsButtonSettings").addEventListener("click", () => withBusyAction("openExportsButtonSettings", "Opening...", openExportsFolder));
  el("settingsResetButton").addEventListener("click", () =>
    withBusyAction("settingsResetButton", "Resetting...", async () => {
      const data = await api("/api/state", { method: "POST", body: JSON.stringify({ reset: true }) });
      appState = data.state;
      readiness = data.readiness;
      updateShellStatus();
      el("settingsMessage").textContent = "Starter bank restored.";
      renderRoute();
    }),
  );
}

function saveVisibleEditor() {
  const text = el("bankText");
  if (!text) return;
  appState[activeBankKey] = text.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function normalizeNumber(value, min, max, fallback) {
  const parsed = Number.parseInt(String(value), 10);
  if (Number.isNaN(parsed)) return fallback;
  if (parsed < min) return min;
  if (parsed > max) return max;
  return parsed;
}

function normalizeSeed(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  return /^-?\d+$/.test(text) ? String(Number(text)) : "";
}

function collideStatusText(readyToCollide = readiness.level !== "red", hasResultHistory = Boolean(currentResult)) {
  if (!readyToCollide) {
    return "Add more ingredients before generating.";
  }
  return hasResultHistory ? "Ready to generate. Keep current seed for repeatability." : "Ready to generate. Create one result first to reuse its seed.";
}

function collideInputs(useExistingSeed = false) {
  const ingredientInput = el("ingredientInput");
  const ingredientCount = normalizeNumber(ingredientInput.value, 3, 7, 5);
  const message = el("collideMessage");
  const seedInput = el("seedInput");
  const rawSeed = seedInput.value.trim();
  const seed = useExistingSeed && currentResult ? currentResult.seed : normalizeSeed(rawSeed);
  const rawIngredient = String(ingredientInput.value || "").trim();
  const warnings = [];
  if (rawSeed && !seed) {
    warnings.push("Seed must be a whole number, or leave blank to auto-generate.");
  }
  if (rawIngredient && ingredientCount !== Number.parseInt(rawIngredient, 10)) {
    warnings.push(`Ingredients clamped to ${ingredientCount} (allowed range: 3-7).`);
  }
  if (warnings.length && message) {
    message.textContent = warnings.join(" ");
    if (collideMessageTimer) {
      clearTimeout(collideMessageTimer);
    }
    collideMessageTimer = setTimeout(() => {
      const collideMessage = collideStatusText(true, Boolean(currentResult));
      if (message) message.textContent = collideMessage;
      collideMessageTimer = null;
    }, 1900);
  }
  return {
    mode: el("modeInput").value,
    weirdness: normalizeNumber(el("weirdnessInput").value, 0, 100, 55),
    ingredient_count: ingredientCount,
    seed,
  };
}

function runGenerateFromInputs(useExistingSeed = false) {
  const options = collideInputs(useExistingSeed);
  if (options.seed === "") {
    const message = el("seedInput").value.trim();
    if (message && !/^[-]?\d+$/.test(message)) {
      return Promise.resolve();
    }
  }
  return runGenerate(options);
}

function resultVariantOptions({ keepIngredients = false, lockBest = false } = {}) {
  const baseSeed = Number(currentResult.seed || 0);
  lastVariantSeed = lastVariantSeed == null ? baseSeed + 1009 : lastVariantSeed + 1009;
  const options = {
    mode: currentResult.mode,
    weirdness: currentResult.weirdness,
    ingredient_count: currentResult.ingredient_count,
    seed: lastVariantSeed,
  };
  if (keepIngredients) {
    options.locked_ingredients = (currentResult.ingredients || []).map((item) => ({ category: item.category, text: item.text }));
  }
  if (lockBest && currentResult.best_ingredient) {
    options.locked_text = currentResult.best_ingredient.text;
  }
  return options;
}

async function runGenerate(options) {
  const data = await api("/api/generate", { method: "POST", body: JSON.stringify(options) });
  currentResult = data.result;
  lastVariantSeed = Number(currentResult.seed || 0);
  lastExportPath = null;
  lastResultAction = null;
  lastCopyAction = null;
  persistResult();
  readiness = data.readiness;
  updateShellStatus();
  navigate("/result");
}

async function saveFavourite() {
  const data = await api("/api/favourites", { method: "POST", body: JSON.stringify({ result: currentResult }) });
  favourites = data.favourites || [];
  markResultAction("save", "Saved to library.");
  refreshProgressUI("result");
}

async function exportResult(format) {
  const data = await api("/api/export", { method: "POST", body: JSON.stringify({ result: currentResult, format }) });
  lastExportPath = data.export.path;
  const openExportsButton = el("openExportsButton");
  if (openExportsButton) openExportsButton.disabled = false;
  markResultAction("export", `Exported ${data.export.format.toUpperCase()} as ${_fileNameFromPath(data.export.path)}.`);
}

async function refreshDoctor() {
  const data = await api("/api/doctor");
  updateSettingsDoctor(data);
  el("settingsMessage").textContent = `Ready: ${data.doctor.readiness.label}. Favourites: ${data.doctor.favourite_count}.`;
  updateDoctorStatus(data);
  markProgressStepVisited();
  refreshProgressUI("settings");
}

function markProgressStepVisited() {
  try {
    localStorage.setItem("ideaColliderCheckedDoctor", "1");
  } catch {
    // localStorage not available in constrained environments; keep moving.
  }
}

function updateDoctorStatus(doctor) {
  const level = doctor?.doctor?.readiness?.level || "amber";
  const normalized = level === "green" ? "ready" : level;
  const label = doctor?.doctor?.readiness?.label || "Ready";
  const status = el("doctorStatus");
  if (!status) return;
  status.className = `status-pill ${normalized}`;
  status.textContent = `ProMentum v${doctor.version || "?"} - ${label}`;
}

async function openExportsFolder() {
  const data = await api("/api/open-exports", { method: "POST", body: "{}" });
  if (data.exports_folder.opened) {
    if (el("settingsMessage")) {
      el("settingsMessage").textContent = `Opened ${data.exports_folder.path}`;
    }
    setResultMessage("Opened exports folder.");
  } else {
    const message = `${data.exports_folder.error || "Could not open exports folder."} (${data.exports_folder.path})`;
    setResultMessage(message);
    if (el("settingsMessage")) {
      el("settingsMessage").textContent = message;
    }
  }
}

async function copyText(text, successMessage, actionKind = "copy-output") {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      fallbackCopy(text, actionKind);
    }
    markResultAction(actionKind, successMessage);
  } catch {
    fallbackCopy(text, actionKind);
  }
}

function fallbackCopy(text, actionKind = "copy-output") {
  const fallback = el("copyFallback");
  fallback.hidden = false;
  fallback.value = text;
  fallback.focus();
  fallback.select();
  try {
    document.execCommand("copy");
    fallback.hidden = true;
    markResultAction(actionKind, "Copied.");
  } catch {
    markResultAction(actionKind, "Clipboard blocked. Text is selected below.");
  }
}

function persistResult() {
  sessionStorage.setItem("ideaColliderLastResult", JSON.stringify(currentResult));
}

function restoreResult() {
  try {
    currentResult = JSON.parse(sessionStorage.getItem("ideaColliderLastResult") || "null");
  } catch {
    currentResult = null;
  }
}

function _fileNameFromPath(path) {
  const parts = String(path || "").split(/[\\/]/);
  return parts[parts.length - 1] || "";
}

function labelFor(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

boot().catch((error) => {
  el("pageRoot").innerHTML = `<section class="empty-state"><h2>ProMentum could not start</h2><p>${escapeHtml(error.message)}</p></section>`;
});
