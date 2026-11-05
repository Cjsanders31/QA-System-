const query = document.querySelector('#query');
const askForm = document.querySelector('#askForm');
const answerSection = document.querySelector('#answerSection');
const answer = document.querySelector('#answer');
const sources = document.querySelector('#sources');

function renderLibrary(files) {
  document.querySelector('#docCount').textContent = `${files.length} PDF${files.length === 1 ? '' : 's'}`;
  document.querySelector('#library').innerHTML = files.map((file) => `<div class="library-file"><span class="file-icon">PDF</span><span>${file}</span></div>`).join('');
}

async function refreshStatus() {
  const status = await fetch('/api/status').then((response) => response.json());
  document.querySelector('#statusText').textContent = `${status.documents} documents · ${status.chunks} passages indexed`;
  const files = await fetch('/api/library').then((response) => response.json());
  renderLibrary(files.files || []);
}

async function ask(question) {
  if (!question.trim()) return;
  answerSection.classList.remove('hidden');
  answer.innerHTML = '<span class="loading">Reading across your papers<span>.</span><span>.</span><span>.</span></span>';
  sources.innerHTML = '';
  const result = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: question }) }).then((response) => response.json());
  answer.textContent = result.answer;
  document.querySelector('#resultMeta').textContent = `${result.sources.length} relevant passages`;
  sources.innerHTML = result.sources.map((source) => `<article class="source"><div class="source-meta"><strong>${source.filename}</strong><span>PAGE ${source.page} · ${(source.score * 100).toFixed(0)}% MATCH</span></div><p>${source.text}</p></article>`).join('');
}

askForm.addEventListener('submit', (event) => { event.preventDefault(); ask(query.value); });
query.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); ask(query.value); } });
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => { query.value = button.dataset.question; ask(query.value); }));
document.querySelector('#fileInput').addEventListener('change', async (event) => { const data = new FormData(); [...event.target.files].forEach((file) => data.append('files', file)); await fetch('/api/ingest', { method: 'POST', body: data }); await refreshStatus(); });
refreshStatus();