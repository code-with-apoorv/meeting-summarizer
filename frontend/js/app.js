/**
 * Meeting Summarizer - Main Frontend Application Logic
 */

// Dynamic API Base: Automatically connects to live Render backend if hosted on Vercel/external domain
const API_BASE = window.location.hostname.includes('vercel.app') 
  ? 'https://meeting-summarizer-0we1.onrender.com' 
  : '';
let currentMeeting = null;
let selectedAudioFile = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initUploadDropzone();
  initRecorderUI();
  initDirectTextInput();
  initTranscriptSearch();
  initHistoryTab();
  checkBackendHealth();

  // Setup waveform canvas in recorder
  const canvas = document.getElementById('waveform-canvas');
  if (canvas) {
    window.meetingRecorder.initVisualizer(canvas);
  }
});

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const bgColors = {
    info: 'bg-blue-600',
    success: 'bg-emerald-600',
    error: 'bg-rose-600',
    warning: 'bg-amber-600'
  };

  toast.className = `${bgColors[type] || 'bg-blue-600'} text-white px-4 py-3 rounded-lg shadow-xl text-sm flex items-center space-x-2 transition-all transform duration-300 opacity-0 translate-y-2`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove('opacity-0', 'translate-y-2');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ----------------------------------------------------
// Navigation & Tabs
// ----------------------------------------------------
function initNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const target = tab.getAttribute('data-tab');

      // Update active classes
      tabs.forEach(t => {
        t.classList.remove('border-blue-500', 'text-blue-400');
        t.classList.add('border-transparent', 'text-gray-400');
      });
      tab.classList.add('border-blue-500', 'text-blue-400');
      tab.classList.remove('border-transparent', 'text-gray-400');

      // Hide all panels
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));

      // Show target panel
      const targetPanel = document.getElementById(`panel-${target}`);
      if (targetPanel) {
        targetPanel.classList.remove('hidden');
      }

      if (target === 'history') {
        loadMeetingHistory();
      }
    });
  });
}

// ----------------------------------------------------
// File Upload & Dropzone
// ----------------------------------------------------
function initUploadDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('audio-file-input');
  const filePreview = document.getElementById('file-preview');
  const fileNameDisplay = document.getElementById('file-name');
  const fileSizeDisplay = document.getElementById('file-size');
  const removeFileBtn = document.getElementById('btn-remove-file');
  const audioPlayer = document.getElementById('audio-preview-player');
  const processBtn = document.getElementById('btn-process-audio');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dropzone-active');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dropzone-active');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      clearSelectedFile();
    });
  }

  function handleFileSelected(file) {
    selectedAudioFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

    // Preview audio in player
    const objectUrl = URL.createObjectURL(file);
    audioPlayer.src = objectUrl;
    audioPlayer.classList.remove('hidden');

    dropzone.classList.add('hidden');
    filePreview.classList.remove('hidden');
    processBtn.disabled = false;
    processBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }

  function clearSelectedFile() {
    selectedAudioFile = null;
    fileInput.value = '';
    audioPlayer.src = '';
    audioPlayer.classList.add('hidden');
    filePreview.classList.add('hidden');
    dropzone.classList.remove('hidden');
    processBtn.disabled = true;
    processBtn.classList.add('opacity-50', 'cursor-not-allowed');
  }

  // Process button click handler
  processBtn.addEventListener('click', async () => {
    if (!selectedAudioFile) {
      showToast('Please select or record an audio file first.', 'warning');
      return;
    }
    await processAudioMeeting(selectedAudioFile);
  });
}

// ----------------------------------------------------
// Live Microphone Recording
// ----------------------------------------------------
function initRecorderUI() {
  const btnStart = document.getElementById('btn-start-record');
  const btnStop = document.getElementById('btn-stop-record');
  const timerDisplay = document.getElementById('record-timer');
  const recordStatus = document.getElementById('record-status');
  const recordIndicator = document.getElementById('record-indicator');

  if (!btnStart || !btnStop) return;

  btnStart.addEventListener('click', async () => {
    try {
      await window.meetingRecorder.startRecording((timeStr) => {
        timerDisplay.textContent = timeStr;
      });

      btnStart.classList.add('hidden');
      btnStop.classList.remove('hidden');
      recordStatus.textContent = 'Recording live meeting audio...';
      recordIndicator.classList.remove('hidden');
      recordIndicator.classList.add('recording-active');
    } catch (err) {
      showToast('Could not access microphone: ' + err.message, 'error');
    }
  });

  btnStop.addEventListener('click', async () => {
    const recordResult = await window.meetingRecorder.stopRecording();
    btnStop.classList.add('hidden');
    btnStart.classList.remove('hidden');
    recordIndicator.classList.add('hidden');
    recordIndicator.classList.remove('recording-active');
    recordStatus.textContent = 'Recording complete! Ready to summarize.';

    if (recordResult && recordResult.file) {
      selectedAudioFile = recordResult.file;
      const filePreview = document.getElementById('file-preview');
      const dropzone = document.getElementById('dropzone');
      const fileNameDisplay = document.getElementById('file-name');
      const fileSizeDisplay = document.getElementById('file-size');
      const audioPlayer = document.getElementById('audio-preview-player');
      const processBtn = document.getElementById('btn-process-audio');

      fileNameDisplay.textContent = `Live Recording (${recordResult.duration}s)`;
      fileSizeDisplay.textContent = `${(recordResult.file.size / 1024).toFixed(1)} KB`;
      audioPlayer.src = URL.createObjectURL(recordResult.blob);
      audioPlayer.classList.remove('hidden');

      dropzone.classList.add('hidden');
      filePreview.classList.remove('hidden');
      processBtn.disabled = false;
      processBtn.classList.remove('opacity-50', 'cursor-not-allowed');

      showToast('Microphone recording saved. Click "Transcribe & Summarize" to proceed.', 'success');
    }
  });
}

// ----------------------------------------------------
// Process Audio Request
// ----------------------------------------------------
async function processAudioMeeting(file) {
  const progressContainer = document.getElementById('processing-status');
  const progressStepText = document.getElementById('progress-step-text');
  const resultsContainer = document.getElementById('results-section');
  const customPromptInput = document.getElementById('custom-prompt');
  const asrSelect = document.getElementById('asr-provider-select');
  const llmSelect = document.getElementById('llm-provider-select');
  const processBtn = document.getElementById('btn-process-audio');

  try {
    processBtn.disabled = true;
    processBtn.classList.add('opacity-50', 'cursor-not-allowed');
    progressContainer.classList.remove('hidden');
    resultsContainer.classList.add('hidden');

    // Step 1: Uploading
    updateProgressStep(1, 'Uploading audio file to processing server...');

    const formData = new FormData();
    formData.append('file', file);
    if (customPromptInput && customPromptInput.value.trim()) {
      formData.append('custom_prompt', customPromptInput.value.trim());
    }
    if (asrSelect) {
      formData.append('asr_provider', asrSelect.value);
    }
    if (llmSelect) {
      formData.append('llm_provider', llmSelect.value);
    }

    // Step 2: Transcribing & Extracting
    setTimeout(() => {
      updateProgressStep(2, 'Transcribing speech to text via ASR Engine...');
    }, 1200);

    setTimeout(() => {
      updateProgressStep(3, 'Extracting key decisions & action items with LLM...');
    }, 2800);

    const response = await fetch(`${API_BASE}/api/meetings/upload-and-summarize`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to process meeting');
    }

    const meetingData = await response.json();
    currentMeeting = meetingData;

    updateProgressStep(4, 'Meeting summary complete!');
    setTimeout(() => {
      progressContainer.classList.add('hidden');
      renderMeetingResults(meetingData);
      showToast('Meeting processed successfully!', 'success');
    }, 600);

  } catch (error) {
    console.error('Processing error:', error);
    progressContainer.classList.add('hidden');
    showToast(`Error: ${error.message}`, 'error');
  } finally {
    processBtn.disabled = false;
    processBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

function updateProgressStep(stepNum, text) {
  const stepText = document.getElementById('progress-step-text');
  if (stepText) stepText.textContent = text;

  for (let i = 1; i <= 3; i++) {
    const stepEl = document.getElementById(`step-indicator-${i}`);
    if (stepEl) {
      if (i < stepNum) {
        stepEl.className = 'w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs';
        stepEl.innerHTML = '✓';
      } else if (i === stepNum) {
        stepEl.className = 'w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs ring-4 ring-blue-900 animate-pulse';
      } else {
        stepEl.className = 'w-8 h-8 rounded-full bg-gray-700 text-gray-400 flex items-center justify-center font-bold text-xs';
      }
    }
  }
}

// ----------------------------------------------------
// Direct Text Summarizer
// ----------------------------------------------------
function initDirectTextInput() {
  const directTextArea = document.getElementById('direct-transcript-text');
  const btnSummarizeDirect = document.getElementById('btn-summarize-direct');
  const btnLoadSample = document.getElementById('btn-load-sample-transcript');

  if (btnLoadSample && directTextArea) {
    btnLoadSample.addEventListener('click', () => {
      directTextArea.value = `[00:00 - Alice (Product Lead)]: Good morning everyone, thanks for joining the Q3 Product & Roadmap alignment meeting. Today we need to decide on three key things: the new user onboarding flow, our mobile app release date, and cloud database migration.

[00:45 - Bob (Engineering Lead)]: Thanks Alice. On the database migration, we analyzed Postgres vs DynamoDB. Postgres with pgvector will save us 40% in infrastructure costs and simplifies our vector search for the AI features. I recommend we finalize Postgres.

[01:30 - Carol (Design Lead)]: From the UX side, the redesigned onboarding flow has reduced drop-off by 25% in user testing. We just need engineering to hook up the new analytics events before we push to production.

[02:15 - David (DevOps / QA)]: We have finished the load testing for the mobile app backend. It handles 5,000 concurrent requests smoothly. However, the iOS build certificate expires next Friday, so we need that renewed immediately.

[03:00 - Alice (Product Lead)]: Great progress. Let's make the decisions:
1. We officially approve Postgres as our primary database and vector store.
2. Mobile app v2.0 release date is locked for September 15th.
3. The new onboarding UI will be enabled for 50% of new signups starting next Monday.

[03:45 - Alice (Product Lead)]: Here are the action items:
- Bob: Finalize the Postgres schema migration script and share the benchmark report by this Friday.
- Carol: Deliver the finalized Figma design tokens and mobile onboarding assets to the engineering repo by Wednesday.
- David: Renew the Apple developer certificates and set up the automated staging CI/CD pipeline by Thursday.
- Alice: Update the executive stakeholder roadmap and schedule the external release announcement for September 15th.

[04:30 - Bob (Engineering Lead)]: Understood. We will kick off the migration scripts right after this call.

[04:45 - Alice (Product Lead)]: Thank you everyone, let's wrap up and get to work!`;
      showToast('Sample transcript loaded.', 'info');
    });
  }

  if (btnSummarizeDirect && directTextArea) {
    btnSummarizeDirect.addEventListener('click', async () => {
      const text = directTextArea.value.trim();
      if (!text) {
        showToast('Please enter transcript text or click "Load Sample Meeting".', 'warning');
        return;
      }

      const promptInput = document.getElementById('direct-custom-prompt');
      const customPrompt = promptInput ? promptInput.value.trim() : '';

      try {
        btnSummarizeDirect.disabled = true;
        btnSummarizeDirect.textContent = 'Summarizing...';

        const response = await fetch(`${API_BASE}/api/meetings/text-summarize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text,
            custom_prompt: customPrompt,
            provider: 'auto'
          })
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Failed to summarize transcript');
        }

        const data = await response.json();
        currentMeeting = data;

        // Switch to upload tab and show results
        document.querySelector('[data-tab="upload"]').click();
        renderMeetingResults(data);
        showToast('Summary generated successfully!', 'success');

      } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
      } finally {
        btnSummarizeDirect.disabled = false;
        btnSummarizeDirect.textContent = 'Generate Summary';
      }
    });
  }
}

// ----------------------------------------------------
// Render Meeting Results
// ----------------------------------------------------
function renderMeetingResults(data) {
  const resultsContainer = document.getElementById('results-section');
  resultsContainer.classList.remove('hidden');
  resultsContainer.scrollIntoView({ behavior: 'smooth' });

  // Header Elements
  document.getElementById('meeting-title').textContent = data.title || 'Meeting Summary';
  document.getElementById('meeting-date').textContent = data.created_at || 'Just now';
  document.getElementById('meeting-asr-badge').textContent = `ASR: ${data.asr_provider || 'Whisper'}`;
  document.getElementById('meeting-llm-badge').textContent = `LLM: ${data.llm_provider || 'Gemini'}`;
  document.getElementById('meeting-sentiment-badge').textContent = data.sentiment || 'Constructive';

  // Tags
  const tagsContainer = document.getElementById('meeting-tags');
  tagsContainer.innerHTML = '';
  if (data.tags && Array.isArray(data.tags)) {
    data.tags.forEach(tag => {
      const span = document.createElement('span');
      span.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-800 text-blue-300 border border-blue-900/40';
      span.textContent = `#${tag}`;
      tagsContainer.appendChild(span);
    });
  }

  // Executive Summary
  document.getElementById('meeting-exec-summary').textContent = data.executive_summary || 'No summary available.';

  // Key Decisions
  const decisionsContainer = document.getElementById('meeting-decisions-list');
  decisionsContainer.innerHTML = '';
  if (data.key_decisions && data.key_decisions.length > 0) {
    data.key_decisions.forEach(d => {
      const li = document.createElement('li');
      li.className = 'flex items-start space-x-3 text-sm text-gray-300';
      li.innerHTML = `
        <span class="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-xs mt-0.5">✓</span>
        <span>${escapeHtml(d)}</span>
      `;
      decisionsContainer.appendChild(li);
    });
  } else {
    decisionsContainer.innerHTML = '<li class="text-sm text-gray-500 italic">No formal decisions recorded.</li>';
  }

  // Discussion Points
  const pointsContainer = document.getElementById('meeting-points-list');
  pointsContainer.innerHTML = '';
  if (data.discussion_points && data.discussion_points.length > 0) {
    data.discussion_points.forEach(p => {
      const li = document.createElement('li');
      li.className = 'flex items-start space-x-3 text-sm text-gray-300';
      li.innerHTML = `
        <span class="flex-shrink-0 w-2 h-2 rounded-full bg-blue-500 mt-2"></span>
        <span>${escapeHtml(p)}</span>
      `;
      pointsContainer.appendChild(li);
    });
  } else {
    pointsContainer.innerHTML = '<li class="text-sm text-gray-500 italic">No major discussion points extracted.</li>';
  }

  // Action Items Checklist
  renderActionItems(data.action_items || []);

  // Verbatim Transcript
  const transcriptEl = document.getElementById('meeting-transcript-text');
  transcriptEl.textContent = data.transcript || 'No transcript available.';

  // Init Export Handlers for current meeting
  setupExportButtons(data.id);
}

// Render Action items table with interactive toggle
function renderActionItems(actionItems) {
  const container = document.getElementById('action-items-container');
  const countBadge = document.getElementById('action-items-count');
  countBadge.textContent = `${actionItems.length} Tasks`;
  container.innerHTML = '';

  if (!actionItems || actionItems.length === 0) {
    container.innerHTML = '<div class="p-4 text-sm text-gray-500 italic text-center">No action items assigned.</div>';
    return;
  }

  actionItems.forEach(item => {
    const isCompleted = item.status === 'completed';
    const card = document.createElement('div');
    card.className = `p-3 rounded-lg border transition-all flex items-start space-x-3 ${
      isCompleted 
        ? 'bg-gray-900/40 border-gray-800 opacity-60' 
        : 'bg-gray-800/60 border-gray-700/60 hover:border-gray-600'
    }`;

    let priorityClass = 'badge-priority-medium';
    const pLower = (item.priority || 'medium').toLowerCase();
    if (pLower === 'high') priorityClass = 'badge-priority-high';
    else if (pLower === 'low') priorityClass = 'badge-priority-low';

    card.innerHTML = `
      <input type="checkbox" ${isCompleted ? 'checked' : ''} 
        class="mt-1 w-4 h-4 rounded text-blue-600 focus:ring-blue-500 bg-gray-700 border-gray-600 cursor-pointer task-checkbox"
        data-task-id="${item.id}">
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium ${isCompleted ? 'line-through text-gray-400' : 'text-gray-200'}">${escapeHtml(item.task)}</p>
        <div class="mt-2 flex flex-wrap items-center gap-2 text-xs">
          <span class="px-2 py-0.5 rounded font-semibold ${priorityClass}">${escapeHtml(item.priority || 'Medium')}</span>
          <span class="px-2 py-0.5 rounded bg-gray-700 text-gray-300 flex items-center space-x-1">
            <span>👤 ${escapeHtml(item.assignee || 'Unassigned')}</span>
          </span>
          <span class="px-2 py-0.5 rounded bg-gray-700/70 text-gray-400">
            📅 ${escapeHtml(item.due_date || 'TBD')}
          </span>
        </div>
      </div>
    `;

    const checkbox = card.querySelector('.task-checkbox');
    checkbox.addEventListener('change', async (e) => {
      const newStatus = e.target.checked ? 'completed' : 'pending';
      await toggleTaskStatus(item.id, newStatus);
    });

    container.appendChild(card);
  });
}

async function toggleTaskStatus(itemId, newStatus) {
  if (!currentMeeting) return;
  try {
    const res = await fetch(`${API_BASE}/api/meetings/${currentMeeting.id}/action-items/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      // Update local state
      const item = currentMeeting.action_items.find(a => a.id === itemId);
      if (item) item.status = newStatus;
      renderActionItems(currentMeeting.action_items);
      showToast(`Task marked as ${newStatus}`, 'info');
    }
  } catch (err) {
    showToast('Failed to update task status', 'error');
  }
}

// ----------------------------------------------------
// Export Handlers
// ----------------------------------------------------
function setupExportButtons(meetingId) {
  const btnCopy = document.getElementById('btn-copy-summary');
  const btnExportMd = document.getElementById('btn-export-md');
  const btnExportPdf = document.getElementById('btn-export-pdf');
  const btnExportJson = document.getElementById('btn-export-json');
  const btnExportTxt = document.getElementById('btn-export-txt');

  if (btnCopy) {
    btnCopy.onclick = () => {
      if (!currentMeeting) return;
      const textToCopy = `MEETING SUMMARY: ${currentMeeting.title}
Date: ${currentMeeting.created_at}

EXECUTIVE SUMMARY:
${currentMeeting.executive_summary}

KEY DECISIONS:
${currentMeeting.key_decisions.map(d => `• ${d}`).join('\n')}

ACTION ITEMS:
${currentMeeting.action_items.map(a => `[${a.status === 'completed' ? 'X' : ' '}] ${a.task} (@${a.assignee}, Due: ${a.due_date})`).join('\n')}`;
      
      navigator.clipboard.writeText(textToCopy);
      showToast('Summary copied to clipboard!', 'success');
    };
  }

  if (btnExportMd) {
    btnExportMd.onclick = () => window.open(`${API_BASE}/api/meetings/${meetingId}/export/md`, '_blank');
  }
  if (btnExportPdf) {
    btnExportPdf.onclick = () => window.open(`${API_BASE}/api/meetings/${meetingId}/export/pdf`, '_blank');
  }
  if (btnExportJson) {
    btnExportJson.onclick = () => window.open(`${API_BASE}/api/meetings/${meetingId}/export/json`, '_blank');
  }
  if (btnExportTxt) {
    btnExportTxt.onclick = () => window.open(`${API_BASE}/api/meetings/${meetingId}/export/txt`, '_blank');
  }
}

// ----------------------------------------------------
// Transcript In-text Search & Highlighting
// ----------------------------------------------------
function initTranscriptSearch() {
  const searchInput = document.getElementById('transcript-search');
  const transcriptEl = document.getElementById('meeting-transcript-text');
  const copyTranscriptBtn = document.getElementById('btn-copy-transcript');

  if (copyTranscriptBtn) {
    copyTranscriptBtn.addEventListener('click', () => {
      if (currentMeeting && currentMeeting.transcript) {
        navigator.clipboard.writeText(currentMeeting.transcript);
        showToast('Transcript copied to clipboard!', 'success');
      }
    });
  }

  if (searchInput && transcriptEl) {
    searchInput.addEventListener('input', () => {
      if (!currentMeeting || !currentMeeting.transcript) return;
      const query = searchInput.value.trim();

      if (!query) {
        transcriptEl.textContent = currentMeeting.transcript;
        return;
      }

      const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
      const highlighted = escapeHtml(currentMeeting.transcript).replace(
        regex,
        '<span class="highlight-text">$1</span>'
      );
      transcriptEl.innerHTML = highlighted;
    });
  }
}

// ----------------------------------------------------
// History Tab & Database Loader
// ----------------------------------------------------
async function loadMeetingHistory() {
  const historyList = document.getElementById('history-list');
  const historySearch = document.getElementById('history-search');
  const emptyState = document.getElementById('history-empty');

  historyList.innerHTML = '<div class="col-span-full py-12 text-center text-gray-400">Loading meeting history...</div>';

  try {
    const query = historySearch ? historySearch.value.trim() : '';
    const url = query ? `${API_BASE}/api/meetings?search=${encodeURIComponent(query)}` : `${API_BASE}/api/meetings`;
    const res = await fetch(url);
    const meetings = await res.json();

    historyList.innerHTML = '';

    if (!meetings || meetings.length === 0) {
      emptyState.classList.remove('hidden');
      return;
    }

    emptyState.classList.add('hidden');

    meetings.forEach(m => {
      const card = document.createElement('div');
      card.className = 'glass-card glass-card-hover rounded-xl p-5 border border-gray-800 flex flex-col justify-between space-y-4';

      const progressPercent = m.action_items_count > 0 
        ? Math.round((m.completed_items_count / m.action_items_count) * 100) 
        : 0;

      card.innerHTML = `
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 border border-blue-800/50">${escapeHtml(m.sentiment || 'Meeting')}</span>
            <span class="text-xs text-gray-400">${escapeHtml(m.created_at ? m.created_at.split('T')[0] : '')}</span>
          </div>
          <h3 class="font-semibold text-base text-gray-100 line-clamp-1">${escapeHtml(m.title)}</h3>
          <p class="text-xs text-gray-400 line-clamp-2">${escapeHtml(m.executive_summary || 'No summary available.')}</p>
        </div>

        <div class="space-y-3 pt-3 border-t border-gray-800/80">
          <div class="flex items-center justify-between text-xs text-gray-400">
            <span>Tasks: ${m.completed_items_count}/${m.action_items_count}</span>
            <span>${progressPercent}% Done</span>
          </div>
          <div class="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
            <div class="bg-emerald-500 h-1.5 rounded-full" style="width: ${progressPercent}%"></div>
          </div>

          <div class="flex items-center justify-between pt-2">
            <button class="btn-open-meeting text-xs font-medium text-blue-400 hover:text-blue-300 flex items-center space-x-1" data-id="${m.id}">
              <span>View Summary →</span>
            </button>
            <button class="btn-delete-meeting text-xs text-rose-400 hover:text-rose-300" data-id="${m.id}" title="Delete meeting">
              🗑️
            </button>
          </div>
        </div>
      `;

      card.querySelector('.btn-open-meeting').addEventListener('click', async () => {
        await loadSingleMeeting(m.id);
      });

      card.querySelector('.btn-delete-meeting').addEventListener('click', async (e) => {
        e.stopPropagation();
        if (confirm(`Delete "${m.title}"?`)) {
          await deleteMeeting(m.id);
        }
      });

      historyList.appendChild(card);
    });

  } catch (err) {
    historyList.innerHTML = `<div class="col-span-full py-8 text-center text-rose-400">Error loading history: ${err.message}</div>`;
  }
}

async function loadSingleMeeting(meetingId) {
  try {
    const res = await fetch(`${API_BASE}/api/meetings/${meetingId}`);
    if (!res.ok) throw new Error('Meeting not found');
    const data = await res.json();
    currentMeeting = data;

    // Switch to upload tab and show results
    document.querySelector('[data-tab="upload"]').click();
    renderMeetingResults(data);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

async function deleteMeeting(meetingId) {
  try {
    const res = await fetch(`${API_BASE}/api/meetings/${meetingId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Meeting deleted', 'info');
      loadMeetingHistory();
      if (currentMeeting && currentMeeting.id === meetingId) {
        document.getElementById('results-section').classList.add('hidden');
        currentMeeting = null;
      }
    }
  } catch (err) {
    showToast('Failed to delete meeting', 'error');
  }
}

function initHistoryTab() {
  const searchInput = document.getElementById('history-search');
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(timeout);
      timeout = setTimeout(loadMeetingHistory, 300);
    });
  }
}

// ----------------------------------------------------
// Health Check
// ----------------------------------------------------
async function checkBackendHealth() {
  const statusEl = document.getElementById('backend-status-badge');
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      if (statusEl) {
        statusEl.textContent = '● System Online';
        statusEl.className = 'text-xs px-2.5 py-1 rounded-full font-medium bg-emerald-950 text-emerald-400 border border-emerald-800/40';
      }
    }
  } catch (e) {
    if (statusEl) {
      statusEl.textContent = '● Connecting...';
      statusEl.className = 'text-xs px-2.5 py-1 rounded-full font-medium bg-amber-950 text-amber-400 border border-amber-800/40';
    }
  }
}

// ----------------------------------------------------
// Utilities
// ----------------------------------------------------
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
