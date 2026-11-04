/* ==========================================================================
   EDUSPHERE — The Paper Archive
   Vanilla JS app. No framework, no network dependency.
   Data: window.__ARCHIVE__ (bundled from edusphere-backend/seed_data.sql)
   ========================================================================== */
(function () {
  "use strict";

  const DB = window.__ARCHIVE__ || { exams: [], papers: [], questions: [], meta: {}, counts: {} };
  const EXAMS = DB.exams || [];
  const EXAM = Object.fromEntries(EXAMS.map((e) => [e.id, e]));
  const FEATURED = ["isc-12", "cbse-12", "jee-main", "jee-advanced", "neet"];
  const VIEWS = ["home", "exams", "papers", "practice", "dashboard", "connect"];
  const STORE_KEY = "edusphere.archive.v1";

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (v) => String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nameOf = (id) => (EXAM[id] ? EXAM[id].name : id || "—");
  const shortOf = (id) => (EXAM[id] ? EXAM[id].short : id || "—");

  /* ---------- Persistent store (works even when localStorage is blocked) ---- */
  const memory = {};
  function readStore() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return memory[STORE_KEY] || {}; }
  }
  function writeStore(data) {
    memory[STORE_KEY] = data;
    try { localStorage.setItem(STORE_KEY, JSON.stringify(data)); } catch (e) { /* in-memory only */ }
  }
  const defaults = { saved: [], solved: [], recent: [], note: "", apiBase: "", custom: [], quizBest: 0 };
  let store = Object.assign({}, defaults, readStore());
  ["saved", "solved", "recent", "custom"].forEach((k) => { if (!Array.isArray(store[k])) store[k] = []; });
  const saveStore = () => writeStore(store);

  const state = {
    view: "home",
    filters: { exam: "", year: "", subject: "", type: "", q: "", sort: "newest", savedOnly: false, solvedOnly: false, pdfOnly: false },
    page: 1, perPage: 12,
    currentList: [],
    currentId: null,
    quiz: { exam: "", subject: "", index: 0, selected: null, score: 0, answered: 0 },
    apiBase: store.apiBase || "",
    apiConnected: false,
    admin: null,
    livePapers: [],
  };

  /* ---------- Data helpers -------------------------------------------------- */
  function allPapers() {
    return DB.papers.concat(store.custom, state.livePapers);
  }
  function mapLive(p) {
    return {
      id: "live-" + p.id,
      apiId: p.id,
      exam: p.exam,
      year: Number(p.year) || 0,
      subject: p.subject || "All Subjects",
      session: p.session || "",
      title: p.title || "Untitled paper",
      description: p.description || "",
      type: "Question Paper",
      format: p.hasFile ? "pdf" : "archive",
      sourceUrl: p.sourceUrl || "",
      sourceLabel: "Live API · /api/papers",
      fileName: p.fileName || "",
      origin: "live",
      downloads: Number(p.downloads) || 0,
      verified: true,
      featured: true,
      topics: [],
      note: "Loaded live from the connected FastAPI backend.",
    };
  }
  function sourceUrlOf(p) {
    if (p.origin === "live" && state.apiBase) return state.apiBase.replace(/\/$/, "") + "/api/papers/" + p.apiId + "/file";
    return p.sourceUrl || "";
  }
  function findPaper(id) { return allPapers().find((p) => p.id === id); }
  function examCount(id) { return allPapers().filter((p) => p.exam === id).length; }

  const EXAM_DETAILS = {
    "isc-12": { duration: "3 hours", marks: "100 / 70", pattern: "Section A (compulsory) + Section B (choice)", body: "CISCE" },
    "cbse-12": { duration: "3 hours", marks: "70 / 80 / 100", pattern: "Competency-based, MCQ, short & long answer", body: "CBSE" },
    "jee-main": { duration: "3 hours", marks: "300", pattern: "90 questions · Physics, Chemistry, Mathematics", body: "NTA" },
    "jee-advanced": { duration: "3 hours per paper", marks: "Paper-wise", pattern: "Two papers · MCQ, numerical, match-the-following", body: "IIT / JEE Adv" },
    "neet": { duration: "3 h 20 min", marks: "720", pattern: "200 questions · 180 to attempt · Physics, Chemistry, Biology", body: "NTA" },
    "cbse-10": { duration: "3 hours", marks: "80 / 100", pattern: "Board examination pattern", body: "CBSE" },
    "icse-10": { duration: "2–3 hours", marks: "80 / 100", pattern: "Board examination pattern", body: "CISCE" },
  };

  /* ---------- Toast --------------------------------------------------------- */
  let toastTimer;
  function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.add("is-on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("is-on"), 2600);
  }

  /* ---------- Router -------------------------------------------------------- */
  function go(view) {
    if (!VIEWS.includes(view)) view = "home";
    if (location.hash !== "#" + view) location.hash = "#" + view;
    else route();
  }
  function route() {
    const raw = (location.hash || "#home").slice(1).split("?")[0];
    const view = VIEWS.includes(raw) ? raw : "home";
    state.view = view;
    $$(".view").forEach((v) => { v.hidden = v.dataset.view !== view; });
    $$("[data-nav]").forEach((a) => a.classList.toggle("is-active", a.dataset.nav === view));
    $("#topbar").classList.remove("is-open");
    $("#menuToggle").setAttribute("aria-expanded", "false");
    window.scrollTo(0, 0);
    if (view === "papers") renderPapers();
    if (view === "practice") renderQuiz();
    if (view === "dashboard") renderDashboard();
    if (view === "connect") renderConnect();
  }

  /* ---------- Static boot --------------------------------------------------- */
  function bootStatic() {
    const total = allPapers().length;
    const years = allPapers().map((p) => p.year).filter(Boolean);
    const minY = Math.min.apply(null, years), maxY = Math.max.apply(null, years);
    $("#heroCount").textContent = total;
    $("#footerCount").textContent = total + " papers on file";
    const navCount = $("#navCount"); if (navCount) navCount.textContent = "(" + total + ")";

    $("#ticker").innerHTML = [
      [total, "Papers filed"],
      [FEATURED.length, "Exam shelves"],
      [minY + "–" + maxY, "Years covered"],
      [(DB.questions || []).length, "Practice questions"],
      [allPapers().filter((p) => p.format === "pdf").length, "Direct PDFs"],
    ].map(([n, label]) => `<div class="ticker__item"><strong>${esc(n)}</strong><span>${esc(label)}</span></div>`).join("");

    const featuredCards = EXAMS.filter((e) => FEATURED.includes(e.id)).map((e, i) => examCard(e, i)).join("");
    const extraCards = EXAMS.filter((e) => !FEATURED.includes(e.id)).map((e, i) => examCard(e, i + FEATURED.length)).join("");
    $("#homeExams").innerHTML = featuredCards;
    $("#examShelf").innerHTML = featuredCards;
    $("#extraShelf").innerHTML = extraCards || '<p class="muted">No extra shelves.</p>';

    // featured papers: newest official PDFs, one per exam
    const picks = [];
    FEATURED.forEach((id) => {
      const p = allPapers().filter((x) => x.exam === id && x.format === "pdf").sort((a, b) => b.year - a.year)[0]
        || allPapers().filter((x) => x.exam === id).sort((a, b) => b.year - a.year)[0];
      if (p) picks.push(p);
    });
    $("#featuredPapers").innerHTML = picks.map(paperCard).join("");

    fillSelects();
    renderChips();
    fillQuizSelects();
    renderConnect();
    $("#apiBase").value = state.apiBase;
  }

  function examCard(e, i) {
    const count = examCount(e.id);
    return `<article class="exam-card">
      <div class="exam-card__num">${String(i + 1).padStart(2, "0")} / ${esc(e.board)}</div>
      <span class="exam-card__tag">${esc(e.tag)}</span>
      <h3>${esc(e.name)}</h3>
      <p>${esc(e.blurb)}</p>
      <div class="exam-card__foot">
        <div class="exam-card__count"><b>${count}</b>papers filed</div>
        <button class="btn btn--sm" data-go="papers" data-exam="${esc(e.id)}">Open shelf →</button>
      </div>
    </article>`;
  }

  /* ---------- Filter controls ---------------------------------------------- */
  function fillSelects() {
    const papers = allPapers();
    const years = Array.from(new Set(papers.map((p) => p.year).filter(Boolean))).sort((a, b) => b - a);
    const subjects = Array.from(new Set(papers.map((p) => p.subject).filter(Boolean))).sort();
    const types = Array.from(new Set(papers.map((p) => p.type).filter(Boolean))).sort();
    const opts = (arr, allLabel, val) => `<option value="">${allLabel}</option>` + arr.map((x) => `<option value="${esc(x)}" ${String(x) === String(val) ? "selected" : ""}>${esc(x)}</option>`).join("");

    $("#filterExam").innerHTML = `<option value="">All examinations</option>` + EXAMS.map((e) => `<option value="${esc(e.id)}">${esc(e.name)} (${examCount(e.id)})</option>`).join("");
    $("#filterYear").innerHTML = opts(years, "All years", state.filters.year);
    $("#filterSubject").innerHTML = opts(subjects, "All subjects", state.filters.subject);
    $("#filterType").innerHTML = opts(types, "All documents", state.filters.type);
    $("#npExam").innerHTML = FEATURED.concat(EXAMS.filter(e => !FEATURED.includes(e.id)).map(e => e.id)).map((id) => `<option value="${esc(id)}">${esc(nameOf(id))}</option>`).join("");
    $("#filterExam").value = state.filters.exam;
    $("#filterYear").value = state.filters.year;
    $("#filterSubject").value = state.filters.subject;
    $("#filterType").value = state.filters.type;
    $("#filterSort").value = state.filters.sort;
    $("#searchInput").value = state.filters.q;
  }

  function renderChips() {
    const chips = [{ id: "", label: "All exams" }]
      .concat(FEATURED.map((id) => ({ id, label: shortOf(id) })))
      .concat([{ id: "__extra", label: "Class 10 & extras" }]);
    $("#examChips").innerHTML = chips.map((c) => {
      const on = c.id === "" ? !state.filters.exam : (c.id === "__extra" ? !FEATURED.includes(state.filters.exam) && !!state.filters.exam : state.filters.exam === c.id);
      return `<button class="chip ${on ? "is-on" : ""}" data-chip="${esc(c.id)}">${esc(c.label)} <span style="opacity:.6">${c.id === "" ? examCount("") || allPapers().length : c.id === "__extra" ? allPapers().filter(p => !FEATURED.includes(p.exam)).length : examCount(c.id)}</span></button>`;
    }).join("");
    ["savedOnly", "solvedOnly", "pdfOnly"].forEach((id) => {
      $("#" + id).classList.toggle("is-on", !!state.filters[id]);
    });
  }

  function filtered() {
    const f = state.filters;
    let list = allPapers().slice();
    if (f.exam === "__extra") list = list.filter((p) => !FEATURED.includes(p.exam));
    else if (f.exam) list = list.filter((p) => p.exam === f.exam);
    if (f.year) list = list.filter((p) => String(p.year) === String(f.year));
    if (f.subject) list = list.filter((p) => p.subject === f.subject);
    if (f.type) list = list.filter((p) => p.type === f.type);
    if (f.savedOnly) list = list.filter((p) => store.saved.includes(p.id));
    if (f.solvedOnly) list = list.filter((p) => store.solved.includes(p.id));
    if (f.pdfOnly) list = list.filter((p) => p.format === "pdf" || p.format === "zip");
    if (f.q) {
      const q = f.q.toLowerCase().trim();
      list = list.filter((p) => [p.title, p.subject, p.session, p.description, p.sourceLabel, p.fileName, p.year, nameOf(p.exam), p.type].join(" ").toLowerCase().includes(q));
    }
    const cmp = {
      newest: (a, b) => b.year - a.year || a.title.localeCompare(b.title),
      oldest: (a, b) => a.year - b.year || a.title.localeCompare(b.title),
      title: (a, b) => a.title.localeCompare(b.title),
      popular: (a, b) => (b.downloads || 0) - (a.downloads || 0) || b.year - a.year,
    }[f.sort];
    return list.sort(cmp);
  }

  /* ---------- Paper cards --------------------------------------------------- */
  function formatLabel(p) {
    return ({ pdf: "PDF", zip: "ZIP BUNDLE", archive: "ARCHIVE PAGE" })[p.format] || "LINK";
  }
  function stampClass(p) {
    if (p.origin === "repo") return "stamp--green";
    if (p.origin === "live") return "stamp--blue";
    return "";
  }
  function paperCard(p) {
    const saved = store.saved.includes(p.id);
    const solved = store.solved.includes(p.id);
    const url = sourceUrlOf(p);
    return `<article class="paper-card">
      <div class="paper-card__tape"></div>
      <div class="paper-card__top">
        <span class="stamp ${stampClass(p)}">${esc(shortOf(p.exam))}</span>
        <span class="paper-card__year">${esc(p.year || "—")}</span>
      </div>
      <h3>${esc(p.title)}</h3>
      <p class="paper-card__desc">${esc(p.description || "Official / verified question paper record.")}</p>
      <div class="paper-card__meta">
        <span class="pill">${esc(p.subject)}</span>
        <span class="pill">${esc(p.type)}</span>
        <span class="pill">${esc(formatLabel(p))}</span>
        ${solved ? '<span class="pill">✓ Solved</span>' : ""}
        ${p.origin === "repo" ? '<span class="pill">From seed_data.sql</span>' : ""}
        ${p.verified === false ? '<span class="pill">Link unchecked</span>' : ""}
      </div>
      <div class="paper-card__foot">
        <div class="paper-card__source">${esc(p.sourceLabel || "Source")} ${p.downloads ? "· " + esc(p.downloads) + " views" : ""}</div>
        <div class="paper-card__actions">
          <button class="btn btn--sm" data-open="${esc(p.id)}">View file</button>
          ${url ? `<a class="btn btn--outline btn--sm" href="${esc(url)}" target="_blank" rel="noopener noreferrer" data-source="${esc(p.id)}">Open ↗</a>` : ""}
          <button class="icon-btn ${saved ? "is-on" : ""}" data-save="${esc(p.id)}" aria-label="${saved ? "Remove from saved" : "Save paper"}" title="${saved ? "Remove from saved" : "Save paper"}">${saved ? "★" : "☆"}</button>
        </div>
      </div>
    </article>`;
  }

  function renderPapers() {
    const list = filtered();
    state.currentList = list;
    const pages = Math.max(1, Math.ceil(list.length / state.perPage));
    if (state.page > pages) state.page = pages;
    const start = (state.page - 1) * state.perPage;
    const slice = list.slice(start, start + state.perPage);

    $("#paperGrid").innerHTML = slice.length ? slice.map(paperCard).join("") :
      `<div class="empty"><h3>Nothing on this shelf</h3><p>Try clearing a filter, or reset everything with the button below.</p><button class="btn btn--sm" data-reset="1" style="margin-top:14px">↺ Reset filters</button></div>`;

    const f = state.filters;
    $("#resultsCount").textContent = `${list.length} paper${list.length === 1 ? "" : "s"} found · showing ${slice.length ? start + 1 : 0}–${start + slice.length}`;
    const bits = [f.exam === "__extra" ? "Class 10 & extras" : f.exam ? nameOf(f.exam) : "All exams", f.year || "all years", f.subject || "all subjects", f.type || "all documents", f.q ? `“${f.q}”` : "", f.savedOnly ? "saved" : "", f.solvedOnly ? "solved" : "", f.pdfOnly ? "direct files" : ""].filter(Boolean);
    $("#activeFilterText").textContent = bits.join(" · ");

    let pager = "";
    if (pages > 1) {
      pager += `<button class="btn btn--outline btn--sm" data-page="prev" ${state.page === 1 ? "disabled" : ""}>← Prev</button>`;
      const around = [];
      for (let i = 1; i <= pages; i++) if (i === 1 || i === pages || Math.abs(i - state.page) <= 1) around.push(i);
      let last = 0;
      around.forEach((i) => {
        if (i - last > 1) pager += `<span class="pager__info">…</span>`;
        pager += `<button class="chip ${i === state.page ? "is-on" : ""}" data-page="${i}">${i}</button>`;
        last = i;
      });
      pager += `<span class="pager__info">Page ${state.page} / ${pages}</span>`;
      pager += `<button class="btn btn--outline btn--sm" data-page="next" ${state.page === pages ? "disabled" : ""}>Next →</button>`;
    }
    $("#pager").innerHTML = pager;
    renderChips();
  }

  /* ---------- Drawer -------------------------------------------------------- */
  function relatedFor(p) {
    return allPapers().filter((x) => x.id !== p.id && x.exam === p.exam && x.subject === p.subject).sort((a, b) => b.year - a.year).slice(0, 4);
  }
  function pushRecent(id) {
    store.recent = [id].concat(store.recent.filter((x) => x !== id)).slice(0, 12);
    saveStore();
  }
  function openPaper(id) {
    const p = findPaper(id);
    if (!p) return;
    state.currentId = id;
    pushRecent(id);
    const saved = store.saved.includes(id);
    const solved = store.solved.includes(id);
    const url = sourceUrlOf(p);
    const d = EXAM_DETAILS[p.exam] || { duration: "—", marks: "—", pattern: "—", body: "—" };
    const idx = state.currentList.findIndex((x) => x.id === id);
    const prev = idx > 0 ? state.currentList[idx - 1] : null;
    const next = idx >= 0 && idx < state.currentList.length - 1 ? state.currentList[idx + 1] : null;
    const rel = relatedFor(p);
    const practiceCount = (DB.questions || []).filter((q) => q.exam === p.exam).length;

    $("#drawerPanel").innerHTML = `<div class="drawer__inner">
      <button class="drawer__close" data-drawer-close="1" aria-label="Close">✕</button>
      <p class="drawer__eyebrow">${esc(nameOf(p.exam))} · ${esc(p.year)} · File ${esc(p.id.toUpperCase())}</p>
      <h2 id="drawerTitle">${esc(p.title)}</h2>
      <p class="drawer__lead">${esc(p.description || "Question paper record from the EduSphere archive.")}</p>

      <dl class="meta-grid">
        <div><dt>Examination</dt><dd>${esc(nameOf(p.exam))}</dd></div>
        <div><dt>Year</dt><dd>${esc(p.year)}</dd></div>
        <div><dt>Subject</dt><dd>${esc(p.subject)}</dd></div>
        <div><dt>Session / paper</dt><dd>${esc(p.session || "—")}</dd></div>
        <div><dt>Document</dt><dd>${esc(p.type)} · ${esc(formatLabel(p))}</dd></div>
        <div><dt>Provenance</dt><dd>${esc(p.origin === "repo" ? "seed_data.sql" : p.origin === "live" ? "Live API" : "Official / verified")}</dd></div>
        <div><dt>Duration</dt><dd>${esc(d.duration)}</dd></div>
        <div><dt>Marks / pattern</dt><dd>${esc(d.marks)}</dd></div>
      </dl>
      <p class="small muted">${esc(d.pattern)} · Conducted by ${esc(d.body)}</p>

      <div class="paper-preview" aria-hidden="true">
        <div class="paper-preview__head"><b>${esc(nameOf(p.exam).toUpperCase())}</b><span>${esc(p.year)} · ${esc(p.subject)}</span></div>
        <div class="paper-preview__lines">${Array.from({ length: 9 }, () => "<span></span>").join("")}</div>
        <div class="paper-preview__foot">ILLUSTRATIVE PREVIEW — OPEN THE OFFICIAL FILE BELOW</div>
      </div>

      <div class="drawer__actions">
        ${url ? `<a class="btn" href="${esc(url)}" target="_blank" rel="noopener noreferrer" data-source="${esc(id)}">Open official file ↗</a>` : ""}
        ${url && (p.format === "pdf" || p.format === "zip") ? `<a class="btn btn--outline btn--sm" href="${esc(url)}" download="${esc(p.fileName || "question-paper")}" target="_blank" rel="noopener noreferrer" data-source="${esc(id)}">Download ↓</a>` : ""}
        <button class="btn btn--outline btn--sm" data-copy="${esc(id)}">Copy link</button>
        <button class="btn btn--outline btn--sm ${saved ? "btn--rust" : ""}" data-save="${esc(id)}">${saved ? "★ Saved" : "☆ Save"}</button>
        <button class="btn btn--outline btn--sm" data-solved="${esc(id)}">${solved ? "✓ Solved — undo" : "Mark solved"}</button>
      </div>
      <div class="url-box">${esc(url || "No external link on this record.")}</div>
      ${p.format === "archive" ? '<p class="small muted">This record opens an archive page — choose the year, subject or paper code there. For cross-origin files, use your browser’s “Save as” if the Download button opens a tab.</p>' : ""}
      ${p.note ? `<div class="drawer__note">${esc(p.note)}</div>` : ""}
      <p class="small muted">Source: ${esc(p.sourceLabel)}${p.fileName ? " · " + esc(p.fileName) : ""}</p>

      <h3 class="drawer__section-title">Topics to revise</h3>
      <div class="topic-list">${(p.topics || []).length ? p.topics.map((t) => `<span class="pill">${esc(t)}</span>`).join("") : '<span class="pill">See the official paper</span>'}</div>

      ${practiceCount ? `<h3 class="drawer__section-title">Practise this exam</h3>
        <p class="small muted" style="margin:0 0 12px">${practiceCount} question${practiceCount === 1 ? "" : "s"} in the reading room for ${esc(nameOf(p.exam))}.</p>
        <button class="btn btn--outline btn--sm" data-go="practice" data-quiz-exam="${esc(p.exam)}">Go to practice →</button>` : ""}

      <h3 class="drawer__section-title">More from this shelf</h3>
      <div class="related">${rel.length ? rel.map((r) => `<button data-open="${esc(r.id)}">${esc(r.year)} · ${esc(r.title)}</button>`).join("") : '<p class="small muted">No related papers yet.</p>'}</div>

      <div class="drawer__nav">
        <button class="btn btn--outline btn--sm" data-drawer-nav="prev" ${prev ? "" : "disabled"}>← Previous paper</button>
        <button class="btn btn--outline btn--sm" data-drawer-nav="next" ${next ? "" : "disabled"}>Next paper →</button>
      </div>
    </div>`;
    $("#drawerPanel").scrollTop = 0;
    $("#drawer").classList.add("is-open");
    $("#drawer").setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }
  function closeDrawer() {
    $("#drawer").classList.remove("is-open");
    $("#drawer").setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }
  function drawerNav(dir) {
    const idx = state.currentList.findIndex((x) => x.id === state.currentId);
    const target = state.currentList[idx + (dir === "next" ? 1 : -1)];
    if (target) openPaper(target.id);
  }

  /* ---------- Quiz ---------------------------------------------------------- */
  function fillQuizSelects() {
    const qs = DB.questions || [];
    const exams = Array.from(new Set(qs.map((q) => q.exam)));
    $("#quizExam").innerHTML = `<option value="">All examinations</option>` + exams.map((id) => `<option value="${esc(id)}">${esc(nameOf(id))}</option>`).join("");
    $("#quizExam").value = state.quiz.exam;
    refreshQuizSubjects();
  }
  function refreshQuizSubjects() {
    const qs = (DB.questions || []).filter((q) => !state.quiz.exam || q.exam === state.quiz.exam);
    const subs = Array.from(new Set(qs.map((q) => q.subject))).sort();
    $("#quizSubject").innerHTML = `<option value="">All subjects</option>` + subs.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join("");
    if (!subs.includes(state.quiz.subject)) state.quiz.subject = "";
    $("#quizSubject").value = state.quiz.subject;
  }
  function quizList() {
    return (DB.questions || []).filter((q) => (!state.quiz.exam || q.exam === state.quiz.exam) && (!state.quiz.subject || q.subject === state.quiz.subject));
  }
  function resetQuiz() {
    state.quiz.index = 0; state.quiz.selected = null; state.quiz.score = 0; state.quiz.answered = 0;
  }
  function renderQuiz() {
    refreshQuizSubjects();
    const list = quizList();
    const q = list[state.quiz.index];
    $("#quizScore").textContent = state.quiz.score + " / " + state.quiz.answered;
    $("#quizProgress").textContent = list.length ? `Question ${state.quiz.index + 1} of ${list.length}` : "No questions";
    if (!q) {
      $("#quizCard").innerHTML = `<div class="quiz-card__top"><span>Reading room</span></div>
        <h3 class="drawer__section-title" style="font-size:34px;margin:40px 0 12px">Nothing filed here</h3>
        <p class="muted">Choose another examination or subject.</p>
        <div class="quiz-card__foot"><button class="btn btn--sm" data-quiz-reset="1">↺ Restart</button></div>`;
      return;
    }
    const answered = state.quiz.selected !== null;
    const options = q.options.map((o, i) => {
      let cls = "";
      if (answered) {
        if (i === q.answer) cls = "is-correct";
        else if (i === state.quiz.selected) cls = "is-wrong";
        else cls = "is-muted";
      }
      return `<button class="option ${cls}" data-option="${i}" ${answered ? "disabled" : ""}><span class="option__key">${"ABCD"[i]}</span><span>${esc(o)}</span></button>`;
    }).join("");
    $("#quizCard").innerHTML = `<div class="quiz-card__top">
        <span>${esc(nameOf(q.exam))} · ${esc(q.subject)}</span>
        <span>${q.origin === "repo" ? "FROM seed_data.sql" : "ILLUSTRATIVE PRACTICE · NOT AN OFFICIAL PAPER"}</span>
      </div>
      <div class="quiz-card__q">${esc(q.question)}</div>
      <div class="options">${options}</div>
      ${answered ? `<div class="explanation"><b>${state.quiz.selected === q.answer ? "Correct." : "Not quite."}</b> ${esc(q.explanation)}<br><span class="small muted">Source: ${esc(q.source)}</span></div>` : ""}
      <div class="quiz-card__foot">
        ${answered ? `<button class="btn btn--sm" data-quiz-next="1">${state.quiz.index + 1 >= list.length ? "See results ↻" : "Next question →"}</button>` : '<span class="small muted">Pick an answer to reveal the explanation.</span>'}
        <button class="btn btn--outline btn--sm" data-quiz-reset="1">↺ Restart</button>
      </div>`;
  }
  function answerQuiz(i) {
    if (state.quiz.selected !== null) return;
    const list = quizList(); const q = list[state.quiz.index];
    if (!q) return;
    state.quiz.selected = i;
    state.quiz.answered++;
    if (i === q.answer) state.quiz.score++;
    if (state.quiz.score > (store.quizBest || 0)) { store.quizBest = state.quiz.score; saveStore(); }
    renderQuiz();
  }
  function nextQuiz() {
    const list = quizList();
    if (state.quiz.index + 1 >= list.length) {
      toast(`Set complete — ${state.quiz.score} of ${state.quiz.answered} correct`);
      resetQuiz();
    } else {
      state.quiz.index++;
      state.quiz.selected = null;
    }
    renderQuiz();
  }

  /* ---------- Dashboard ----------------------------------------------------- */
  function renderDashboard() {
    const saved = store.saved.length, solved = store.solved.length;
    $("#dashStats").innerHTML = [
      [allPapers().length, "Papers in archive"],
      [saved, "Saved papers"],
      [solved, "Marked solved"],
      [store.recent.length, "Recently opened"],
      [store.quizBest || 0, "Best practice score"],
    ].map(([n, l]) => `<div class="dash-stat"><strong>${esc(n)}</strong><span>${esc(l)}</span></div>`).join("");

    $("#dashProgress").innerHTML = FEATURED.map((id) => {
      const total = examCount(id);
      const done = allPapers().filter((p) => p.exam === id && store.solved.includes(p.id)).length;
      const pct = total ? Math.min(100, Math.round(done / total * 100)) : 0;
      return `<div class="progress-row"><div class="progress-row__head"><span>${esc(nameOf(id))}</span><span>${done} / ${total} · ${pct}%</span></div><div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div></div>`;
    }).join("");

    const ids = Array.from(new Set(store.saved.concat(store.solved)));
    $("#dashSaved").innerHTML = ids.length ? ids.map((id) => {
      const p = findPaper(id);
      if (!p) return "";
      return `<div class="list-row"><div><div class="list-row__title">${esc(p.title)}</div><div class="list-row__sub">${esc(nameOf(p.exam))} · ${esc(p.year)} ${store.solved.includes(id) ? "· ✓ solved" : ""}</div></div>
        <div style="display:flex;gap:6px"><button class="btn btn--outline btn--sm" data-open="${esc(id)}">Open</button><button class="icon-btn" data-save="${esc(id)}" aria-label="Remove">✕</button></div></div>`;
    }).join("") : '<p class="muted small">Nothing saved yet. Use the ☆ button on any paper card.</p>';

    $("#dashRecent").innerHTML = store.recent.length ? store.recent.map((id) => {
      const p = findPaper(id);
      return p ? `<div class="list-row"><div><div class="list-row__title">${esc(p.title)}</div><div class="list-row__sub">${esc(nameOf(p.exam))} · ${esc(p.year)}</div></div><button class="btn btn--outline btn--sm" data-open="${esc(id)}">Open</button></div>` : "";
    }).join("") : '<p class="muted small">Open a paper and it will be listed here.</p>';

    $("#noteInput").value = store.note || "";
  }

  /* ---------- Connect / API ------------------------------------------------- */
  function apiFetch(path, options) {
    const base = state.apiBase.replace(/\/$/, "");
    return fetch(base + path, Object.assign({ credentials: "include" }, options || {})).then(async (res) => {
      const type = res.headers.get("content-type") || "";
      const data = type.includes("application/json") ? await res.json() : null;
      if (!res.ok) throw new Error((data && (data.detail || data.error)) || "Request failed (" + res.status + ")");
      return data;
    });
  }
  function setApiStatus(text, ok) {
    const el = $("#apiStatus");
    el.classList.toggle("is-ok", !!ok);
    el.innerHTML = `<span class="status__dot"></span><span>${esc(text)}</span>`;
  }
  function renderConnect() {
    const m = DB.meta || {};
    $("#dbSummary").innerHTML = `<span class="k">database</span>  : ${esc(m.database || "seed_data.sql")}
<span class="k">source</span>    : ${esc(m.repo || "")}
<span class="k">commit</span>    : ${esc(m.repoCommit || "")}
<span class="k">generated</span> : ${esc(m.generated || "")}
<span class="k">papers</span>    : ${DB.papers.length} bundled + ${store.custom.length} local + ${state.livePapers.length} live
<span class="k">questions</span> : ${(DB.questions || []).length}
<span class="k">note</span>      : ${esc(m.note || "")}`;
    $("#dbTable").innerHTML = `<thead><tr><th>Exam</th><th>Bundled</th><th>Type</th></tr></thead><tbody>` +
      EXAMS.map((e) => `<tr><td>${esc(e.name)}</td><td>${DB.papers.filter((p) => p.exam === e.id).length}</td><td>${esc(e.tag)}</td></tr>`).join("") + `</tbody>`;
    $("#portablePreview").innerHTML = `<span class="k">saved</span>   : ${store.saved.length}
<span class="k">solved</span>  : ${store.solved.length}
<span class="k">recent</span>  : ${store.recent.length}
<span class="k">local papers</span> : ${store.custom.length}
<span class="k">note</span>    : ${esc((store.note || "").slice(0, 60) || "—")}`;
    if (state.apiConnected) setApiStatus(`Connected · ${state.livePapers.length} live papers${state.admin ? " · signed in as " + state.admin.email : ""}`, true);
    else setApiStatus("Offline — bundled database", false);
  }
  async function connectApi() {
    const base = $("#apiBase").value.trim();
    if (!base) { toast("Enter an API base URL first"); return; }
    state.apiBase = base; store.apiBase = base; saveStore();
    setApiStatus("Connecting…", false);
    try {
      const papers = await apiFetch("/api/papers?limit=500");
      if (!Array.isArray(papers)) throw new Error("Unexpected /api/papers response");
      state.livePapers = papers.map(mapLive);
      state.apiConnected = true;
      try {
        const s = await apiFetch("/api/session");
        state.admin = s && s.session ? s.session : null;
      } catch (e) { state.admin = null; }
      fillSelects(); renderChips(); renderConnect();
      toast(`Synced ${state.livePapers.length} live papers`);
      if (state.view === "papers") renderPapers();
    } catch (e) {
      state.apiConnected = false; state.livePapers = [];
      setApiStatus("Connection failed — using bundled data", false);
      $("#adminMsg").textContent = e.message;
      toast("Could not reach the backend");
    }
  }
  function disconnectApi() {
    state.apiConnected = false; state.livePapers = []; state.admin = null;
    fillSelects(); renderChips(); renderConnect();
    if (state.view === "papers") renderPapers();
    toast("Using bundled database");
  }

  /* ---------- Actions ------------------------------------------------------- */
  function toggleSave(id) {
    const i = store.saved.indexOf(id);
    if (i >= 0) { store.saved.splice(i, 1); toast("Removed from saved"); }
    else { store.saved.push(id); toast("Saved to your desk ★"); }
    saveStore();
    if (state.view === "papers") renderPapers();
    if (state.view === "dashboard") renderDashboard();
    if (state.view === "connect") renderConnect();
    if ($("#drawer").classList.contains("is-open") && state.currentId) openPaper(state.currentId);
  }
  function toggleSolved(id) {
    const i = store.solved.indexOf(id);
    if (i >= 0) { store.solved.splice(i, 1); toast("Marked as unsolved"); }
    else { store.solved.push(id); toast("Marked solved ✓"); }
    saveStore();
    if (state.view === "papers") renderPapers();
    if (state.view === "dashboard") renderDashboard();
    if ($("#drawer").classList.contains("is-open") && state.currentId) openPaper(state.currentId);
  }
  function setFilter(key, value) {
    state.filters[key] = value;
    state.page = 1;
    renderPapers();
  }
  function resetFilters() {
    state.filters = { exam: "", year: "", subject: "", type: "", q: "", sort: "newest", savedOnly: false, solvedOnly: false, pdfOnly: false };
    state.page = 1;
    fillSelects();
    renderPapers();
    toast("Filters reset");
  }
  function openRandom() {
    const list = filtered().length ? filtered() : allPapers();
    if (!list.length) return;
    const p = list[Math.floor(Math.random() * list.length)];
    state.currentList = list;
    openPaper(p.id);
  }
  function copyLink(id) {
    const p = findPaper(id);
    const url = p ? sourceUrlOf(p) : "";
    if (!url) { toast("No link on this record"); return; }
    const done = () => toast("Link copied to clipboard");
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done).catch(() => fallbackCopy(url, done));
    } else fallbackCopy(url, done);
  }
  function fallbackCopy(text, done) {
    const ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(); } catch (e) { toast("Copy the URL shown below"); }
    document.body.removeChild(ta);
  }
  function exportData() {
    const blob = new Blob([JSON.stringify(store, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "edusphere-my-data.json";
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); document.body.removeChild(a); }, 500);
    toast("Data exported");
  }
  function importData(file) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        store = Object.assign({}, defaults, data);
        ["saved", "solved", "recent", "custom"].forEach((k) => { if (!Array.isArray(store[k])) store[k] = []; });
        saveStore();
        state.apiBase = store.apiBase || "";
        $("#apiBase").value = state.apiBase;
        fillSelects(); renderChips(); renderConnect();
        toast("Data imported");
      } catch (e) { toast("That file is not valid JSON"); }
    };
    reader.readAsText(file);
  }

  /* ---------- Events -------------------------------------------------------- */
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-go],[data-exam],[data-chip],[data-open],[data-save],[data-solved],[data-source],[data-page],[data-option],[data-quiz-next],[data-quiz-reset],[data-copy],[data-drawer-nav],[data-drawer-close],[data-reset],[data-quiz-exam]");
    if (!el) return;

    if (el.hasAttribute("data-quiz-exam")) state.quiz.exam = el.getAttribute("data-quiz-exam");
    if (el.hasAttribute("data-exam")) state.filters.exam = el.getAttribute("data-exam");
    if (el.hasAttribute("data-go")) {
      const view = el.getAttribute("data-go");
      if (view === "papers") { state.page = 1; renderPapers(); }
      if (view === "practice") { resetQuiz(); fillQuizSelects(); renderQuiz(); }
      go(view);
      return;
    }
    if (el.hasAttribute("data-chip")) {
      const c = el.getAttribute("data-chip");
      setFilter("exam", c);
      $("#filterExam").value = EXAMS.some((x) => x.id === c) ? c : "";
      return;
    }
    if (el.hasAttribute("data-open")) { openPaper(el.getAttribute("data-open")); return; }
    if (el.hasAttribute("data-save")) { toggleSave(el.getAttribute("data-save")); return; }
    if (el.hasAttribute("data-solved")) { toggleSolved(el.getAttribute("data-solved")); return; }
    if (el.hasAttribute("data-copy")) { e.preventDefault(); copyLink(el.getAttribute("data-copy")); return; }
    if (el.hasAttribute("data-source")) { pushRecent(el.getAttribute("data-source")); return; }
    if (el.hasAttribute("data-reset")) { resetFilters(); return; }
    if (el.hasAttribute("data-page")) {
      const v = el.getAttribute("data-page");
      const pages = Math.max(1, Math.ceil(state.currentList.length / state.perPage));
      if (v === "prev") state.page = Math.max(1, state.page - 1);
      else if (v === "next") state.page = Math.min(pages, state.page + 1);
      else state.page = Number(v) || 1;
      renderPapers();
      window.scrollTo({ top: $("#view-papers").offsetTop, behavior: "smooth" });
      return;
    }
    if (el.hasAttribute("data-option")) { answerQuiz(Number(el.getAttribute("data-option"))); return; }
    if (el.hasAttribute("data-quiz-next")) { nextQuiz(); return; }
    if (el.hasAttribute("data-quiz-reset")) { resetQuiz(); renderQuiz(); return; }
    if (el.hasAttribute("data-drawer-nav")) { drawerNav(el.getAttribute("data-drawer-nav")); return; }
    if (el.hasAttribute("data-drawer-close")) { closeDrawer(); return; }
  });

  $("#drawerBackdrop").addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && $("#drawer").classList.contains("is-open")) closeDrawer();
    if ($("#drawer").classList.contains("is-open") && (e.key === "ArrowRight" || e.key === "ArrowLeft")) drawerNav(e.key === "ArrowRight" ? "next" : "prev");
  });

  $("#menuToggle").addEventListener("click", () => {
    const open = $("#topbar").classList.toggle("is-open");
    $("#menuToggle").setAttribute("aria-expanded", String(open));
  });

  let searchTimer;
  $("#searchInput").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => setFilter("q", e.target.value), 180);
  });
  [["#filterExam", "exam"], ["#filterYear", "year"], ["#filterSubject", "subject"], ["#filterType", "type"], ["#filterSort", "sort"]].forEach(([sel, key]) => {
    $(sel).addEventListener("change", (e) => { setFilter(key, e.target.value); renderChips(); });
  });
  $("#resetFilters").addEventListener("click", resetFilters);
  $("#surpriseBtn").addEventListener("click", openRandom);
  [["#savedOnly", "savedOnly"], ["#solvedOnly", "solvedOnly"], ["#pdfOnly", "pdfOnly"]].forEach(([sel, key]) => {
    $(sel).addEventListener("click", () => { state.filters[key] = !state.filters[key]; state.page = 1; renderPapers(); });
  });

  $("#quizExam").addEventListener("change", (e) => { state.quiz.exam = e.target.value; state.quiz.subject = ""; resetQuiz(); refreshQuizSubjects(); renderQuiz(); });
  $("#quizSubject").addEventListener("change", (e) => { state.quiz.subject = e.target.value; resetQuiz(); renderQuiz(); });
  $("#quizRestart").addEventListener("click", () => { resetQuiz(); renderQuiz(); });

  $("#dashClear").addEventListener("click", () => {
    if (!confirm("Clear saved papers, solved marks, recent files and notes from this browser?")) return;
    store = Object.assign({}, defaults, { apiBase: store.apiBase });
    saveStore(); renderDashboard(); toast("Your desk is clear");
  });
  $("#noteSave").addEventListener("click", () => {
    store.note = $("#noteInput").value;
    saveStore();
    $("#noteMsg").textContent = "Note saved on this device.";
    setTimeout(() => { $("#noteMsg").textContent = ""; }, 2500);
  });

  $("#apiConnect").addEventListener("click", connectApi);
  $("#apiDisconnect").addEventListener("click", disconnectApi);
  $("#adminLoginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("#adminMsg");
    if (!state.apiConnected) { msg.textContent = "Connect the backend first."; return; }
    msg.textContent = "Signing in…";
    try {
      const data = await apiFetch("/api/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: $("#adminEmail").value, password: $("#adminPassword").value }),
      });
      state.admin = data.session || null;
      msg.textContent = state.admin ? "Signed in as " + state.admin.email : "Signed in.";
      renderConnect(); toast("Admin signed in");
    } catch (err) { msg.textContent = err.message; }
  });
  $("#adminLogout").addEventListener("click", async () => {
    try { if (state.apiConnected) await apiFetch("/api/auth/logout", { method: "POST" }); } catch (e) { /* ignore */ }
    state.admin = null; $("#adminMsg").textContent = "Signed out."; renderConnect();
  });
  $("#addPaperForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("#addMsg");
    const payload = {
      exam: $("#npExam").value, year: $("#npYear").value, subject: $("#npSubject").value.trim(),
      session: $("#npSession").value.trim(), title: $("#npTitle").value.trim(),
      description: $("#npDesc").value.trim(), sourceUrl: $("#npUrl").value.trim(),
    };
    if (payload.title.length < 3 || !payload.subject) { msg.textContent = "A title (3+ chars) and subject are required."; return; }
    if (payload.sourceUrl && !/^https?:\/\//i.test(payload.sourceUrl)) { msg.textContent = "Source URL must start with http:// or https://"; return; }
    if (state.apiConnected && state.admin) {
      const fd = new FormData();
      Object.keys(payload).forEach((k) => fd.append(k, payload[k]));
      const file = $("#npFile").files[0];
      if (file) fd.append("file", file);
      msg.textContent = "Uploading…";
      try {
        await apiFetch("/api/admin/papers", { method: "POST", body: fd });
        msg.textContent = "Created on the backend. Syncing…";
        await connectApi();
        e.target.reset();
      } catch (err) { msg.textContent = err.message; }
      return;
    }
    const url = payload.sourceUrl;
    const p = {
      id: "local-" + Date.now(), exam: payload.exam, year: Number(payload.year), subject: payload.subject,
      session: payload.session, title: payload.title, description: payload.description,
      type: "Question Paper", format: /\.pdf$/i.test(url) ? "pdf" : /\.zip$/i.test(url) ? "zip" : "archive",
      sourceUrl: url, sourceLabel: "Added locally · this browser", fileName: url.split("/").pop() || "",
      origin: "local", downloads: 0, verified: false, featured: true, topics: [],
      note: "Added from the Database page. Stored in this browser only — export it to keep it.",
    };
    store.custom.push(p); saveStore();
    fillSelects(); renderChips(); renderConnect();
    msg.textContent = "Added to this browser's shelf.";
    toast("Paper added locally");
    e.target.reset();
  });
  $("#exportBtn").addEventListener("click", exportData);
  $("#importBtn").addEventListener("click", () => $("#importFile").click());
  $("#importFile").addEventListener("change", (e) => { if (e.target.files[0]) importData(e.target.files[0]); e.target.value = ""; });

  window.addEventListener("hashchange", route);

  /* ---------- Go ------------------------------------------------------------ */
  bootStatic();
  renderPapers();
  renderQuiz();
  route();
})();
