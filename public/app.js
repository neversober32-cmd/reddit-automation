let leadsData = [];
let currentLead = null;
let currentAngle = "clinical_advisor";
let currentProvider = "demo";

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  await loadStats();
  await loadSettings();
  await loadLeads();
  await loadDrafts();
  await loadLogs();
  checkConnectionPill();
}

// TAB SWITCHING
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".tab-btn").forEach(el => {
    el.classList.remove("active", "bg-sky-500/10", "text-sky-400", "border-sky-500/20");
    el.classList.add("text-slate-400");
  });

  const targetTab = document.getElementById(`tab-${tabId}`);
  const targetBtn = document.getElementById(`tab-btn-${tabId}`);
  if (targetTab) targetTab.classList.remove("hidden");
  if (targetBtn) {
    targetBtn.classList.add("active", "bg-sky-500/10", "text-sky-400", "border-sky-500/20");
    targetBtn.classList.remove("text-slate-400");
  }

  if (tabId === 'queue') loadDrafts();
  if (tabId === 'logs') loadLogs();
}

// STATS
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById("stat-total-leads").innerText = data.total_leads || "0";
    document.getElementById("stat-pending-drafts").innerText = data.active_drafts || "0";
    document.getElementById("stat-published").innerText = data.published_comments || "0";
    currentProvider = data.provider || "demo";
  } catch (err) {
    console.error("Failed to load stats", err);
  }
}

// LEADS RADAR
async function loadLeads() {
  try {
    const res = await fetch('/api/leads');
    const data = await res.json();
    leadsData = data.leads || [];
    renderLeads(leadsData);
    if (leadsData.length > 0 && !currentLead) {
      selectLeadForStudio(leadsData[0].id);
    }
  } catch (err) {
    console.error("Failed to load leads", err);
  }
}

function renderLeads(leads) {
  const container = document.getElementById("leads-container");
  if (!container) return;

  if (leads.length === 0) {
    container.innerHTML = `
      <div class="col-span-2 text-center py-12 glass-panel rounded-xl text-slate-400">
        <i class="fa-solid fa-radar text-4xl mb-3 text-slate-600"></i>
        <p class="text-sm">No discussions found matching criteria. Click "Scan Subreddits Now".</p>
      </div>
    `;
    return;
  }

  container.innerHTML = leads.map(l => {
    let intentBadgeClass = "bg-sky-500/10 text-sky-400 border-sky-500/20";
    if (l.intent.includes("Commercial")) intentBadgeClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (l.intent.includes("Brand")) intentBadgeClass = "bg-purple-500/10 text-purple-400 border-purple-500/20";
    if (l.intent.includes("Comparison")) intentBadgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";

    const isReplied = l.status === 'replied';

    return `
      <div class="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4">
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span class="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">r/${l.subreddit}</span>
              <span class="text-xs font-mono text-slate-500">u/${l.author}</span>
            </div>
            <div class="flex items-center space-x-1.5">
              <span class="text-[11px] px-2 py-0.5 rounded-full border ${intentBadgeClass} font-medium">${l.intent}</span>
              <span class="text-[11px] px-2 py-0.5 rounded bg-slate-800/80 text-slate-400 font-medium">${l.location}</span>
            </div>
          </div>

          <h3 class="font-bold text-slate-100 text-sm hover:text-sky-300 transition line-clamp-2">
            <a href="${l.url}" target="_blank" rel="noopener">${l.title} <i class="fa-solid fa-arrow-up-right-from-square text-[10px] ml-1 text-slate-500"></i></a>
          </h3>

          <p class="text-xs text-slate-400 line-clamp-3 leading-relaxed">${l.body || "No additional post body."}</p>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-slate-800/80">
          <span class="text-[11px] text-slate-500 font-mono">${l.id}</span>
          <div class="flex items-center space-x-2">
            ${isReplied ? `
              <span class="text-xs text-teal-400 font-semibold px-2.5 py-1 bg-teal-500/10 rounded border border-teal-500/20">
                <i class="fa-solid fa-check mr-1"></i> Replied
              </span>
            ` : ''}
            <button onclick="selectLeadForStudio('${l.id}')" class="px-3 py-1.5 bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white text-xs font-semibold rounded-lg shadow transition flex items-center space-x-1.5">
              <i class="fa-solid fa-wand-magic-sparkles"></i>
              <span>Craft Medical Reply</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function filterLeadsUI() {
  const city = document.getElementById("filter-city").value;
  const query = document.getElementById("scan-custom-query").value.toLowerCase();

  const filtered = leadsData.filter(l => {
    const matchCity = city === "all" || l.location.toLowerCase().includes(city.toLowerCase());
    const matchQuery = !query || l.title.toLowerCase().includes(query) || l.body.toLowerCase().includes(query) || l.subreddit.toLowerCase().includes(query);
    return matchCity && matchQuery;
  });

  renderLeads(filtered);
}

document.getElementById("scan-custom-query")?.addEventListener("input", filterLeadsUI);

async function triggerScan() {
  const query = document.getElementById("scan-custom-query").value;
  showToast("Scanning target subreddits for high-intent hair & aesthetic discussions...");
  try {
    const res = await fetch('/api/leads/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query || null })
    });
    const data = await res.json();
    leadsData = data.leads || [];
    filterLeadsUI();
    loadStats();
    showToast(`Scan complete! Found ${leadsData.length} target discussions.`);
  } catch (err) {
    showToast("Scan failed: " + err.message, true);
  }
}

// STUDIO
function selectLeadForStudio(leadId) {
  const lead = leadsData.find(l => l.id === leadId);
  if (!lead) return;
  currentLead = lead;

  document.getElementById("studio-lead-fullname").innerText = lead.id;
  document.getElementById("studio-lead-sub").innerText = `r/${lead.subreddit}`;
  document.getElementById("studio-lead-author").innerText = `u/${lead.author}`;
  document.getElementById("studio-lead-title").innerText = lead.title;
  document.getElementById("studio-lead-body").innerText = lead.body || "No body content.";

  switchTab('studio');
  regenerateAIResponse();
}

function setStudioAngle(angle) {
  currentAngle = angle;
  document.querySelectorAll(".angle-btn").forEach(btn => {
    btn.classList.remove("active", "bg-sky-500/10", "border-sky-500", "text-sky-300");
    btn.classList.add("bg-slate-900", "border-slate-800", "text-slate-300");
  });

  const activeBtn = document.getElementById(`angle-btn-${angle}`);
  if (activeBtn) {
    activeBtn.classList.add("active", "bg-sky-500/10", "border-sky-500", "text-sky-300");
    activeBtn.classList.remove("bg-slate-900", "border-slate-800", "text-slate-300");
  }

  regenerateAIResponse();
}

async function regenerateAIResponse() {
  if (!currentLead) return;
  const editor = document.getElementById("studio-draft-editor");
  editor.value = "Generating clinical, MD-verified response for Assure Clinic...";

  try {
    const res = await fetch('/api/generate_reply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lead: currentLead, angle: currentAngle })
    });
    const data = await res.json();
    if (data.success) {
      editor.value = data.response_text;
    } else {
      editor.value = "Failed to generate response.";
    }
  } catch (err) {
    editor.value = "Error contacting AI engine: " + err.message;
  }
}

function copyDraftToClipboard() {
  const text = document.getElementById("studio-draft-editor").value;
  navigator.clipboard.writeText(text);
  showToast("Draft copied to clipboard!");
}

async function saveToQueue() {
  if (!currentLead) return;
  const draftText = document.getElementById("studio-draft-editor").value;
  try {
    const res = await fetch('/api/drafts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_id: currentLead.id,
        response_type: currentAngle,
        draft_text: draftText
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Draft successfully saved to Publishing Queue!");
      loadStats();
      loadDrafts();
    }
  } catch (err) {
    showToast("Error saving draft: " + err.message, true);
  }
}

async function publishDirectly() {
  if (!currentLead) return;
  const draftText = document.getElementById("studio-draft-editor").value;
  showToast("Submitting comment via Reddit Engine...");
  
  try {
    const saveRes = await fetch('/api/drafts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead_id: currentLead.id,
        response_type: currentAngle,
        draft_text: draftText
      })
    });
    const saveData = await saveRes.json();
    if (!saveData.success) throw new Error(saveData.message);

    const pubRes = await fetch(`/api/drafts/${saveData.draft_id}/publish`, { method: 'POST' });
    const pubData = await pubRes.json();
    
    if (pubData.success) {
      showToast(`Success! ${pubData.message}`);
      loadStats();
      loadLeads();
      loadDrafts();
      switchTab('queue');
    } else {
      showToast(`Publishing failed: ${pubData.message}`, true);
    }
  } catch (err) {
    showToast("Submission error: " + err.message, true);
  }
}

// QUEUE & PUBLISHED
async function loadDrafts() {
  try {
    const res = await fetch('/api/drafts');
    const data = await res.json();
    renderQueue(data.drafts || []);
  } catch (err) {
    console.error("Failed to load drafts", err);
  }
}

function renderQueue(drafts) {
  const tbody = document.getElementById("queue-table-body");
  if (!tbody) return;

  if (drafts.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center py-8 text-slate-500">
          No items in queue. Select a lead in Radar to draft responses.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = drafts.map(d => {
    const isPublished = d.status === 'published';
    return `
      <tr class="hover:bg-slate-900/40 transition">
        <td class="p-3">
          <div class="font-semibold text-slate-200 line-clamp-1">${d.post_title}</div>
          <div class="text-[11px] text-slate-400">r/${d.subreddit} • ${d.post_fullname}</div>
        </td>
        <td class="p-3">
          <span class="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-sky-300 font-medium">${d.response_type}</span>
        </td>
        <td class="p-3">
          <div class="line-clamp-2 text-slate-400 font-mono text-[11px] max-w-xs">${d.draft_text}</div>
        </td>
        <td class="p-3">
          ${isPublished ? `
            <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/20 text-[11px] font-semibold">
              <i class="fa-solid fa-check text-[10px]"></i>
              <span>Published (${d.published_comment_id})</span>
            </span>
          ` : `
            <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[11px] font-semibold">
              <i class="fa-solid fa-clock text-[10px]"></i>
              <span>Draft (Ready)</span>
            </span>
          `}
        </td>
        <td class="p-3 text-right space-x-1">
          ${!isPublished ? `
            <button onclick="publishDraftFromQueue(${d.id})" class="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-[11px] font-semibold transition">
              <i class="fa-solid fa-paper-plane mr-1"></i> Post
            </button>
          ` : ''}
          <button onclick="deleteDraftFromQueue(${d.id})" class="p-1 text-slate-500 hover:text-rose-400 transition">
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

async function publishDraftFromQueue(draftId) {
  showToast("Publishing draft to Reddit...");
  try {
    const res = await fetch(`/api/drafts/${draftId}/publish`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      loadDrafts();
      loadStats();
      loadLeads();
    } else {
      showToast(`Failed: ${data.message}`, true);
    }
  } catch (err) {
    showToast("Publish error: " + err.message, true);
  }
}

async function deleteDraftFromQueue(draftId) {
  try {
    await fetch(`/api/drafts/${draftId}/delete`, { method: 'DELETE' });
    loadDrafts();
    loadStats();
    showToast("Draft removed.");
  } catch (err) {
    showToast("Error deleting draft", true);
  }
}

// PRESETS & POST BUILDER
function loadPostPreset(preset) {
  const titleEl = document.getElementById("post-title");
  const bodyEl = document.getElementById("post-body");

  if (preset === 'graft_math') {
    titleEl.value = "[Guide] Graft Survival Math: Why Out-of-Body Time & Implantation Protocol Matter More Than Harvest Count";
    bodyEl.value = `When researching hair restoration, patients often focus purely on the quote: *"I got 3,000 grafts for ₹X."*

However, in clinical hair restoration, what dictates your final density is not the **Harvest Count**, but the **Graft Survival Rate**.

### 3 Factors That Cause Graft Failure:
1. **Desiccation (Drying Out):** Follicular units are living tissue. If left exposed without temperature-regulated bio-preservative holding solution, cellular degradation begins within 60 minutes.
2. **Transection:** High-speed, blunt motorized punches can sever follicular bulbs beneath the scalp surface.
3. **Handling Trauma:** Forceps squeezing the delicate root bulb crushes stem cells.

### Clinical Protocols for 95%+ Survival:
- **Ultra-Fine Micro Extraction (UFME):** Sub-0.8mm micro-punches that protect the adjacent donor bed.
- **Direct Simultaneous Hair Implantation (DSHI):** Slits and placement performed concurrently to minimize out-of-body holding time.
- **MD-Dermatologist Driven Execution:** Slit angles, density gradients (single hairs at hairline, doubles/triples at mid-scalp) placed by qualified doctors.

At **Assure Clinic** (clinics across Mumbai, Delhi, Bangalore, Hyderabad, Lucknow, Pune, and Dubai), our surgical teams are led by MD Dermatologists committed to donor preservation.

*Disclaimer: Informational only. Consult a board-certified dermatologist for a clinical assessment.*`;
  } else if (preset === 'hairline_rules') {
    titleEl.value = "[Guide] The Aesthetics of a Natural Hairline: Macro-Irregularities & Age-Appropriate Design";
    bodyEl.value = `A natural hairline should never look like a ruler was held against your forehead.

Here are the 4 aesthetic rules our MD Dermatologists at **Assure Clinic** use during pre-operative surgical planning:

1. **Rule of Thirds:** The distance from chin to subnasale, subnasale to glabella, and glabella to trichion (hairline) must maintain proportional facial thirds.
2. **Micro & Macro Irregularities:** Real human hair does not grow in straight rows. The transitional anterior zone requires soft single-hair follicular units placed in subtle zig-zag clusters.
3. **Temporal Angles & Lateral Humps:** Recreating temple points prevents an artificial "pluggy" or helmet appearance.
4. **Angulation & Direction:** Hair must emerge at 15–20 degrees at the front and increase to 30–45 degrees moving back into the mid-scalp.

Drop your questions below on hairline planning, Norwood staging, or donor capacity!

*Disclaimer: Informational guide by Assure Clinic.*`;
  }
}

async function submitEducationalPost() {
  const sub = document.getElementById("post-target-sub").value;
  const title = document.getElementById("post-title").value;
  const body = document.getElementById("post-body").value;

  if (!title || !body) {
    showToast("Please provide both title and body text", true);
    return;
  }

  showToast(`Submitting educational post to r/${sub}...`);
  try {
    const res = await fetch('/api/posts/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subreddit: sub, title, body })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      loadLogs();
    } else {
      showToast(`Error: ${data.message}`, true);
    }
  } catch (err) {
    showToast("Submission failed: " + err.message, true);
  }
}

// PROVIDER & SETTINGS
function selectProvider(provider) {
  currentProvider = provider;
  
  ['composio', 'praw', 'demo'].forEach(p => {
    const card = document.getElementById(`provider-card-${p}`);
    if (card) {
      if (p === provider) {
        card.className = "cursor-pointer p-3.5 rounded-lg border-2 border-sky-500 bg-sky-500/10 shadow transition";
      } else {
        card.className = "cursor-pointer p-3.5 rounded-lg border border-slate-800 bg-slate-900 hover:border-slate-700 transition";
      }
    }
  });

  const composioBox = document.getElementById("composio-config-box");
  const prawBox = document.getElementById("praw-config-box");

  if (provider === 'composio') {
    composioBox.classList.remove("hidden");
  } else if (provider === 'praw') {
    prawBox.classList.remove("hidden");
  }
}

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    const cfg = data.config || {};

    document.getElementById("cfg-composio-key").value = cfg.composio_api_key || "";
    document.getElementById("cfg-composio-entity").value = cfg.composio_entity_id || "default";
    document.getElementById("cfg-client-id").value = cfg.reddit_client_id || "";
    document.getElementById("cfg-client-secret").value = cfg.reddit_client_secret || "";
    document.getElementById("cfg-username").value = cfg.reddit_username || "";

    selectProvider(cfg.provider || cfg.mode || "demo");
  } catch (err) {
    console.error("Failed to load settings", err);
  }
}

async function saveSettings() {
  const payload = {
    provider: currentProvider,
    mode: currentProvider,
    composio_api_key: document.getElementById("cfg-composio-key").value,
    composio_entity_id: document.getElementById("cfg-composio-entity").value,
    reddit_client_id: document.getElementById("cfg-client-id").value,
    reddit_client_secret: document.getElementById("cfg-client-secret").value,
    reddit_username: document.getElementById("cfg-username").value
  };

  const passwordVal = document.getElementById("cfg-password").value;
  if (passwordVal && !passwordVal.includes("••••")) {
    payload.reddit_password = passwordVal;
  }

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast("Configuration saved!");
      checkConnectionPill();
    }
  } catch (err) {
    showToast("Error saving settings: " + err.message, true);
  }
}

async function testConnection() {
  showToast("Testing connection status...");
  try {
    const res = await fetch('/api/settings/test', { method: 'POST' });
    const data = await res.json();
    
    const oauthBox = document.getElementById("composio-oauth-cta");
    const oauthLink = document.getElementById("composio-oauth-link");

    if (data.status === "auth_required" && data.auth_url) {
      oauthBox.classList.remove("hidden");
      oauthLink.href = data.auth_url;
      showToast("Composio API key valid! Click 'Connect Reddit OAuth' to authenticate.");
    } else if (data.status.startsWith("connected")) {
      oauthBox.classList.add("hidden");
      showToast(data.message);
    } else {
      showToast(data.message, true);
    }
    checkConnectionPill();
  } catch (err) {
    showToast("Connection test error: " + err.message, true);
  }
}

async function checkConnectionPill() {
  const pill = document.getElementById("connection-status-pill");
  const text = document.getElementById("connection-status-text");

  try {
    const res = await fetch('/api/settings/test', { method: 'POST' });
    const data = await res.json();
    if (data.status === "connected_live") {
      pill.className = "flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300";
      text.innerText = `${data.provider.toUpperCase()}: ${data.username}`;
    } else if (data.status === "auth_required") {
      pill.className = "flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300";
      text.innerText = "Composio: OAuth Required";
    } else if (data.status === "connected_demo") {
      pill.className = "flex items-center space-x-2 px-3 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/30 text-xs text-sky-300";
      text.innerText = "Demo Testbed Active";
    } else {
      pill.className = "flex items-center space-x-2 px-3 py-1.5 rounded-full bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300";
      text.innerText = "Auth Disconnected";
    }
  } catch (err) {
    text.innerText = "Offline";
  }
}

// LOGS
async function loadLogs() {
  try {
    const res = await fetch('/api/logs');
    const data = await res.json();
    const container = document.getElementById("logs-container");
    if (!container) return;

    if (!data.logs || data.logs.length === 0) {
      container.innerHTML = '<div class="text-slate-500 p-4">No recent activity logged.</div>';
      return;
    }

    container.innerHTML = data.logs.map(l => {
      const isErr = l.status === 'error';
      return `
        <div class="p-2.5 rounded bg-slate-900/80 border border-slate-800/80 flex items-start justify-between space-x-3">
          <div class="space-y-0.5">
            <span class="font-bold ${isErr ? 'text-rose-400' : 'text-sky-400'}">[${l.action}]</span>
            <span class="text-slate-300">${l.details}</span>
          </div>
          <span class="text-[10px] text-slate-500 whitespace-nowrap">${l.timestamp}</span>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load logs", err);
  }
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  const msgEl = document.getElementById("toast-message");
  const icon = document.getElementById("toast-icon");

  if (!toast || !msgEl) return;

  msgEl.innerText = message;
  if (isError) {
    icon.className = "fa-solid fa-circle-exclamation text-rose-400 text-lg";
    toast.className = "fixed bottom-6 right-6 z-50 bg-slate-900 border border-rose-500/40 px-4 py-3 rounded-xl shadow-2xl flex items-center space-x-3 text-sm transform translate-y-0 opacity-100 transition-all duration-300";
  } else {
    icon.className = "fa-solid fa-circle-check text-teal-400 text-lg";
    toast.className = "fixed bottom-6 right-6 z-50 bg-slate-900 border border-teal-500/40 px-4 py-3 rounded-xl shadow-2xl flex items-center space-x-3 text-sm transform translate-y-0 opacity-100 transition-all duration-300";
  }

  setTimeout(() => {
    toast.className = "fixed bottom-6 right-6 z-50 transform translate-y-20 opacity-0 transition-all duration-300 bg-slate-900 border border-slate-700 px-4 py-3 rounded-xl shadow-2xl flex items-center space-x-3 text-sm";
  }, 4000);
}
