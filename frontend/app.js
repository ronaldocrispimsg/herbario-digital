// ─────────────────────────────────────────────
//  CONFIGURAÇÃO — altere para apontar ao backend
// ─────────────────────────────────────────────
const API_BASE = '/api/v1';

// ─────────────────────────────────────────────
//  ESTADO GLOBAL
// ─────────────────────────────────────────────
let state = {
  token: localStorage.getItem('ba_token') || null,
  user:  JSON.parse(localStorage.getItem('ba_user') || 'null'),
  editingEspecime: null,
  editingTax: null,
  editingLoc: null,
  specPage: 1,
  taxPage: 1,
  locPage: 1,
  loanTab: 'ativos',
  allTaxonomias: [],
  allLocalidades: [],
  allEspecimes: [],
};

// ─────────────────────────────────────────────
//  HTTP
// ─────────────────────────────────────────────
async function api(method, path, body, isForm = false) {
  const headers = {};
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
  if (!isForm) headers['Content-Type'] = 'application/json';
  const opts = { method, headers };
  if (body) opts.body = isForm ? body : JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  if (res.status === 401) { logout(); return null; }
  const ct = res.headers.get('content-type') || '';
  const data = ct.includes('json') ? await res.json() : await res.text();
  if (!res.ok) throw new Error(data?.detail || JSON.stringify(data) || res.statusText);
  return data;
}

// ─────────────────────────────────────────────
//  TOAST
// ─────────────────────────────────────────────
function toast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${type === 'success' ? '✓' : '✕'}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ─────────────────────────────────────────────
//  AUTH
// ─────────────────────────────────────────────
async function doLogin() {
  const emailInput = document.getElementById('login-email');
  const passInput  = document.getElementById('login-senha');
  const email = emailInput.value.trim();
  const pass  = passInput.value;
  const err   = document.getElementById('login-error');
  const btn   = document.getElementById('login-btn');
  err.style.display = 'none';
  passInput.classList.remove('input-error');
  if (!email || !pass) { err.textContent = 'Preencha e-mail e senha.'; err.style.display = 'block'; return; }
  btn.disabled = true; btn.textContent = '…';
  try {
    const form = new URLSearchParams({ username: email, password: pass });
    const data = await api('POST', '/auth/login', form, true);
    state.token = data.access_token;
    state.user  = data.usuario;
    localStorage.setItem('ba_token', state.token);
    localStorage.setItem('ba_user', JSON.stringify(state.user));
    const currentPage = window.location.pathname.split('/').pop();
    if (currentPage === 'login.html') {
      window.location.href = 'index.html';
      return;
    }
    postLogin();
  } catch(e) {
    err.textContent = 'E-mail ou senha incorretos.';
    err.style.display = 'block';
    passInput.value = '';
    passInput.classList.add('input-error');
  } finally { btn.disabled = false; btn.textContent = 'Entrar'; }
}

function postLogin() {
  document.getElementById('user-name-badge').textContent = state.user?.nome || state.user?.email;
  document.getElementById('nav').style.display = 'flex';
  document.getElementById('topbar-right').style.display = 'flex';
  if (state.user?.perfil === 'administrador') {
    document.getElementById('nav-usuarios').style.display = '';
  } else {
    document.getElementById('nav-usuarios').style.display = 'none';
  }
  const loanBtn = document.querySelector('[data-screen="emprestimos"]');
  if (loanBtn) {
    loanBtn.style.display = state.user?.perfil === 'leitor' ? 'none' : '';
  }
  navigateTo('dashboard');
}

function logout() {
  state.token = null; state.user = null;
  localStorage.removeItem('ba_token');
  localStorage.removeItem('ba_user');
  window.location.href = 'login.html';
}

// ─────────────────────────────────────────────
//  NAVEGAÇÃO
// ─────────────────────────────────────────────
function navigateTo(screen) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const s = document.getElementById(`screen-${screen}`);
  if (s) s.classList.add('active');
  const nb = document.querySelector(`[data-screen="${screen}"]`);
  if (nb) nb.classList.add('active');
  if (screen === 'dashboard') loadDashboard();
  if (screen === 'especimes') { loadSelectsForEspecime(); searchEspecimes(1); }
  if (screen === 'taxonomias') loadTaxonomias(1);
  if (screen === 'localidades') loadLocalidades(1);
  if (screen === 'emprestimos') { loadSelectsForEmprestimo(); loadEmprestimos(); }
  if (screen === 'usuarios') loadUsuarios();
}

document.querySelectorAll('.nav-btn').forEach(b => {
  b.addEventListener('click', () => navigateTo(b.dataset.screen));
});

// ─────────────────────────────────────────────
//  DASHBOARD
// ─────────────────────────────────────────────
async function loadDashboard() {
  try {
    const [especimes, taxonomias, localidades, usuarios] = await Promise.all([
      api('POST', '/especimes/buscar', { page:1, per_page:1 }),
      api('GET', '/taxonomias?per_page=1'),
      api('GET', '/localidades?per_page=1'),
      api('GET', '/usuarios').catch(() => null),
    ]);

    document.getElementById('stat-total').textContent = especimes?.total ?? '—';
    document.getElementById('stat-taxonomias').textContent = taxonomias?.total ?? '—';
    document.getElementById('stat-localidades').textContent = localidades?.total ?? '—';
    document.getElementById('stat-usuarios').textContent = usuarios?.total ?? '—';

    const statuses = ['ativo','emprestado','em_processamento','descartado'];
    const counts = {};
    await Promise.all(statuses.map(async s => {
      const r = await api('POST', '/especimes/buscar', { status: s, page:1, per_page:1 });
      counts[s] = r?.total || 0;
    }));
    document.getElementById('stat-ativos').textContent = counts.ativo ?? '—';
    document.getElementById('stat-emprestados').textContent = counts.emprestado ?? '—';
    renderBarChart('chart-status', [
      { label: 'Ativo', count: counts.ativo },
      { label: 'Emprestado', count: counts.emprestado },
      { label: 'Em Processamento', count: counts.em_processamento },
      { label: 'Descartado', count: counts.descartado },
    ]);

    const allSpec = await api('POST', '/especimes/buscar', { page:1, per_page:100 });
    const famCount = {};
    (allSpec?.items || []).forEach(e => {
      const f = e.taxonomia?.familia || 'Desconhecida';
      famCount[f] = (famCount[f] || 0) + 1;
    });
    const top = Object.entries(famCount).sort((a,b)=>b[1]-a[1]).slice(0,8);
    renderBarChart('chart-familias', top.map(([l,c]) => ({ label: l, count: c })));

  } catch(e) { toast('Erro ao carregar dashboard', 'error'); }
}

function renderBarChart(id, data) {
  const el = document.getElementById(id);
  if (!data.length) { el.innerHTML = '<div style="color:var(--muted);font-size:.82rem">Sem dados</div>'; return; }
  const max = Math.max(...data.map(d => d.count), 1);
  el.innerHTML = data.map(d => `
    <div class="bar-item">
      <span class="bar-label" title="${d.label}">${d.label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(d.count/max*100).toFixed(1)}%"></div></div>
      <span class="bar-count">${d.count}</span>
    </div>`).join('');
}

// ─────────────────────────────────────────────
//  ESPÉCIMES
// ─────────────────────────────────────────────
let searchTimer = null;
function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => searchEspecimes(1), 400);
}

function toggleFilters() {
  const r = document.getElementById('filter-row');
  r.style.display = r.style.display === 'none' ? 'flex' : 'none';
}

function clearFilters() {
  ['f-estado','f-municipio','f-bioma','f-coletor'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('f-status').value = '';
  searchEspecimes(1);
}

async function loadSelectsForEspecime() {
  try {
    if (!state.allTaxonomias.length) {
      const r = await api('GET', '/taxonomias?per_page=200');
      state.allTaxonomias = r?.items || [];
    }
    if (!state.allLocalidades.length) {
      const r = await api('GET', '/localidades?per_page=200');
      state.allLocalidades = r?.items || [];
    }
    fillSelect('e-taxonomia', state.allTaxonomias, t => t.nome_cientifico, t => t.id);
    fillSelect('e-localidade', state.allLocalidades,
      l => [l.municipio, l.estado].filter(Boolean).join(' — ') || l.localidade || `ID ${l.id}`,
      l => l.id, '— Sem localidade —');
  } catch(e) {}
}

function fillSelect(id, items, labelFn, valueFn, emptyLabel) {
  const sel = document.getElementById(id);
  const cur = sel.value;
  const opts = emptyLabel ? `<option value="">${emptyLabel}</option>` : '<option value="">— Selecione —</option>';
  sel.innerHTML = opts + items.map(i => `<option value="${valueFn(i)}">${labelFn(i)}</option>`).join('');
  if (cur) sel.value = cur;
}

async function searchEspecimes(page = 1) {
  state.specPage = page;
  const nome = document.getElementById('busca-nome')?.value.trim();
  const body = {
    page, per_page: 20,
    nome_cientifico: nome || undefined,
    estado: document.getElementById('f-estado')?.value || undefined,
    municipio: document.getElementById('f-municipio')?.value || undefined,
    bioma: document.getElementById('f-bioma')?.value || undefined,
    coletor: document.getElementById('f-coletor')?.value || undefined,
    status: document.getElementById('f-status')?.value || undefined,
  };
  Object.keys(body).forEach(k => body[k] === undefined && delete body[k]);

  const tbody = document.getElementById('tbody-especimes');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="6"><div class="loader"></div></td></tr>';

  try {
    const data = await api('POST', '/especimes/buscar', body);
    renderEspecimes(data);
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--danger)">Erro: ${e.message}</td></tr>`;
  }
}

function renderEspecimes(data) {
  const tbody = document.getElementById('tbody-especimes');
  const pag = document.getElementById('pag-especimes');
  if (!data?.items?.length) {
    tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="icon">🌱</div><p>Nenhum espécime encontrado</p></div></td></tr>';
    pag.style.display = 'none';
    return;
  }
  tbody.innerHTML = data.items.map(e => {
    const loc = e.localidade ? [e.localidade.municipio, e.localidade.estado].filter(Boolean).join(', ') : '—';
    return `<tr>
      <td data-label="Código" class="td-mono">${e.codigo_catalogo}</td>
      <td data-label="Nome Científico" class="td-sci">${e.taxonomia?.nome_cientifico || '—'}</td>
      <td data-label="Família">${e.taxonomia?.familia || '—'}</td>
      <td data-label="Localidade">${loc}</td>
      <td data-label="Status"><span class="tag tag-${e.status}">${e.status}</span></td>
      <td data-label="Ações" class="td-actions">
        <button class="btn btn-sm btn-ghost" onclick="viewEspecime(${e.id})">Ver</button>
        <button class="btn btn-sm" onclick="editEspecime(${JSON.stringify(e).replace(/"/g,'&quot;')})">Editar</button>
      </td>
    </tr>`;
  }).join('');
  renderPagination('pag-especimes', data.page, data.pages, p => searchEspecimes(p));
}

async function viewEspecime(id) {
  try {
    const e = await api('GET', `/especimes/${id}`);
    const body = document.getElementById('modal-detalhe-body');
    const loc = e.localidade;
    const tax = e.taxonomia;
    body.innerHTML = `
      <div class="detail-header">
        <div class="detail-img">🌿</div>
        <div class="detail-info">
          <h3>${tax?.nome_cientifico || 'Espécime'}</h3>
          ${tax?.nome_comum ? `<div class="common">${tax.nome_comum}</div>` : ''}
          <div class="code">${e.codigo_catalogo}</div>
          <span class="tag tag-${e.status}" style="margin-top:8px">${e.status}</span>
        </div>
      </div>
      <div class="detail-grid">
        ${field('Família', tax?.familia)}
        ${field('Gênero', tax?.genero)}
        ${field('Autor', tax?.autor_descricao)}
        ${field('Coletor', e.coletor_principal)}
        ${field('Data Coleta', e.data_coleta ? new Date(e.data_coleta).toLocaleDateString('pt-BR') : null)}
        ${field('Tipo Coleta', e.tipo_coleta)}
        ${field('Nº Campo', e.numero_campo)}
        ${field('Nº Indivíduos', e.numero_individuos)}
        ${field('Estado', loc?.estado)}
        ${field('Município', loc?.municipio)}
        ${field('Bioma', loc?.bioma)}
        ${loc?.latitude ? field('Coordenadas', `${loc.latitude.toFixed(4)}, ${loc.longitude?.toFixed(4)}`) : ''}
        ${field('Preservação', e.meio_preservacao)}
        ${field('Localização Física', e.localizacao_fisica)}
        ${field('Identificado por', e.identificado_por)}
        ${field('Confiança', e.nivel_confianca_id)}
        ${field('Voucher GenBank', e.voucher_genbank)}
      </div>
      ${e.habitat ? `<div style="margin-top:16px"><div class="detail-field"><div class="key">Habitat</div><div class="val">${e.habitat}</div></div></div>` : ''}
      ${e.observacoes ? `<div style="margin-top:8px"><div class="detail-field"><div class="key">Observações</div><div class="val">${e.observacoes}</div></div></div>` : ''}`;
    openModal('modal-detalhe-overlay');
  } catch(e) { toast('Erro ao carregar espécime', 'error'); }
}

function field(label, val) {
  if (!val && val !== 0) return '';
  return `<div class="detail-field"><div class="key">${label}</div><div class="val">${val}</div></div>`;
}

function editEspecime(e) {
  if (typeof e === 'string') e = JSON.parse(e);
  state.editingEspecime = e.id;
  document.getElementById('modal-especime-title').textContent = 'Editar Espécime';
  openModal('modal-especime-overlay');
  document.getElementById('e-codigo').value = e.codigo_catalogo || '';
  document.getElementById('e-taxonomia').value = e.taxonomia_id || '';
  document.getElementById('e-data-coleta').value = e.data_coleta ? e.data_coleta.substring(0,10) : '';
  document.getElementById('e-tipo-coleta').value = e.tipo_coleta || 'campo';
  document.getElementById('e-coletor').value = e.coletor_principal || '';
  document.getElementById('e-num-campo').value = e.numero_campo || '';
  document.getElementById('e-localidade').value = e.localidade_id || '';
  document.getElementById('e-num-ind').value = e.numero_individuos || 1;
  document.getElementById('e-sexo').value = e.sexo || '';
  document.getElementById('e-estagio').value = e.estagio_vida || '';
  document.getElementById('e-preservacao').value = e.meio_preservacao || '';
  document.getElementById('e-loc-fisica').value = e.localizacao_fisica || '';
  document.getElementById('e-habitat').value = e.habitat || '';
  document.getElementById('e-obs').value = e.observacoes || '';
  document.getElementById('e-status').value = e.status || 'ativo';
  document.getElementById('e-id-por').value = e.identificado_por || '';
  document.getElementById('e-confianca').value = e.nivel_confianca_id || '';
  document.getElementById('e-genbank').value = e.voucher_genbank || '';
}

function openModalEspecime() {
  state.editingEspecime = null;
  document.getElementById('modal-especime-title').textContent = 'Novo Espécime';
  ['e-codigo','e-coletor','e-num-campo','e-estagio','e-preservacao','e-loc-fisica','e-habitat','e-obs','e-id-por','e-genbank']
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  document.getElementById('e-taxonomia').value = '';
  document.getElementById('e-localidade').value = '';
  document.getElementById('e-data-coleta').value = '';
  document.getElementById('e-num-ind').value = '1';
  document.getElementById('e-status').value = 'ativo';
  document.getElementById('e-tipo-coleta').value = 'campo';
  document.getElementById('e-sexo').value = '';
  document.getElementById('e-confianca').value = '';
  openModal('modal-especime-overlay');
}

async function saveEspecime() {
  const btn = document.getElementById('btn-save-especime');
  btn.disabled = true; btn.textContent = '…';
  try {
    const body = {
      codigo_catalogo: document.getElementById('e-codigo').value.trim(),
      taxonomia_id: parseInt(document.getElementById('e-taxonomia').value),
      data_coleta: document.getElementById('e-data-coleta').value || undefined,
      tipo_coleta: document.getElementById('e-tipo-coleta').value,
      coletor_principal: document.getElementById('e-coletor').value || undefined,
      numero_campo: document.getElementById('e-num-campo').value || undefined,
      localidade_id: document.getElementById('e-localidade').value ? parseInt(document.getElementById('e-localidade').value) : undefined,
      numero_individuos: parseInt(document.getElementById('e-num-ind').value) || 1,
      sexo: document.getElementById('e-sexo').value || undefined,
      estagio_vida: document.getElementById('e-estagio').value || undefined,
      meio_preservacao: document.getElementById('e-preservacao').value || undefined,
      localizacao_fisica: document.getElementById('e-loc-fisica').value || undefined,
      habitat: document.getElementById('e-habitat').value || undefined,
      observacoes: document.getElementById('e-obs').value || undefined,
      status: document.getElementById('e-status').value,
      identificado_por: document.getElementById('e-id-por').value || undefined,
      nivel_confianca_id: document.getElementById('e-confianca').value || undefined,
      voucher_genbank: document.getElementById('e-genbank').value || undefined,
    };
    Object.keys(body).forEach(k => body[k] === undefined && delete body[k]);
    if (state.editingEspecime) {
      await api('PUT', `/especimes/${state.editingEspecime}`, body);
      toast('Espécime atualizado!');
    } else {
      await api('POST', '/especimes', body);
      toast('Espécime cadastrado!');
    }
    closeModal('modal-especime-overlay');
    searchEspecimes(state.specPage);
  } catch(e) { toast(e.message, 'error'); }
  finally { btn.disabled = false; btn.textContent = 'Salvar'; }
}

// ─────────────────────────────────────────────
//  TAXONOMIAS
// ─────────────────────────────────────────────
let taxTimer = null;
function debounceSearchTax() { clearTimeout(taxTimer); taxTimer = setTimeout(() => loadTaxonomias(1), 400); }

async function loadTaxonomias(page = 1) {
  state.taxPage = page;
  const q = document.getElementById('busca-tax')?.value.trim();
  const params = new URLSearchParams({ page, per_page: 20 });
  if (q) params.set('q', q);
  const tbody = document.getElementById('tbody-taxonomias');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="6"><div class="loader"></div></td></tr>';
  try {
    const data = await api('GET', `/taxonomias?${params}`);
    if (!data?.items?.length) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="icon">🌱</div><p>Nenhuma taxonomia encontrada</p></div></td></tr>';
      document.getElementById('pag-taxonomias').style.display = 'none';
      return;
    }
    tbody.innerHTML = data.items.map(t => `<tr>
      <td data-label="ID" class="td-mono">${t.id}</td>
      <td data-label="Nome Científico" class="td-sci">${t.nome_cientifico}</td>
      <td data-label="Família">${t.familia || '—'}</td>
      <td data-label="Gênero">${t.genero || '—'}</td>
      <td data-label="Nome Comum">${t.nome_comum || '—'}</td>
      <td data-label="Ações" class="td-actions">
        <button class="btn btn-sm btn-ghost" onclick='editTaxonomia(${JSON.stringify(t).replace(/'/g,"&#39;")})'>Editar</button>
      </td>
    </tr>`).join('');
    renderPagination('pag-taxonomias', data.page, data.pages, p => loadTaxonomias(p));
    state.allTaxonomias = [];
  } catch(e) { tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--danger)">Erro: ${e.message}</td></tr>`; }
}

function openModalTaxonomia() {
  state.editingTax = null;
  document.getElementById('modal-tax-title').textContent = 'Nova Taxonomia';
  ['t-nome-ci','t-reino','t-filo','t-classe','t-ordem','t-familia','t-genero','t-epiteto','t-autor','t-nome-com','t-notas']
    .forEach(id => document.getElementById(id).value = '');
  document.getElementById('t-ano').value = '';
  openModal('modal-tax-overlay');
}

function editTaxonomia(t) {
  if (typeof t === 'string') t = JSON.parse(t);
  state.editingTax = t.id;
  document.getElementById('modal-tax-title').textContent = 'Editar Taxonomia';
  document.getElementById('t-nome-ci').value = t.nome_cientifico || '';
  document.getElementById('t-reino').value = t.reino || '';
  document.getElementById('t-filo').value = t.filo || '';
  document.getElementById('t-classe').value = t.classe || '';
  document.getElementById('t-ordem').value = t.ordem || '';
  document.getElementById('t-familia').value = t.familia || '';
  document.getElementById('t-genero').value = t.genero || '';
  document.getElementById('t-epiteto').value = t.epiteto_especifico || '';
  document.getElementById('t-autor').value = t.autor_descricao || '';
  document.getElementById('t-ano').value = t.ano_descricao || '';
  document.getElementById('t-nome-com').value = t.nome_comum || '';
  document.getElementById('t-notas').value = t.notas_taxonomicas || '';
  openModal('modal-tax-overlay');
}

async function saveTaxonomia() {
  try {
    const body = {
      nome_cientifico: document.getElementById('t-nome-ci').value.trim(),
      reino: document.getElementById('t-reino').value || undefined,
      filo: document.getElementById('t-filo').value || undefined,
      classe: document.getElementById('t-classe').value || undefined,
      ordem: document.getElementById('t-ordem').value || undefined,
      familia: document.getElementById('t-familia').value || undefined,
      genero: document.getElementById('t-genero').value || undefined,
      epiteto_especifico: document.getElementById('t-epiteto').value || undefined,
      autor_descricao: document.getElementById('t-autor').value || undefined,
      ano_descricao: document.getElementById('t-ano').value ? parseInt(document.getElementById('t-ano').value) : undefined,
      nome_comum: document.getElementById('t-nome-com').value || undefined,
      notas_taxonomicas: document.getElementById('t-notas').value || undefined,
    };
    Object.keys(body).forEach(k => body[k] === undefined && delete body[k]);
    if (state.editingTax) {
      await api('PUT', `/taxonomias/${state.editingTax}`, body);
      toast('Taxonomia atualizada!');
    } else {
      await api('POST', '/taxonomias', body);
      toast('Taxonomia criada!');
    }
    closeModal('modal-tax-overlay');
    loadTaxonomias(state.taxPage);
  } catch(e) { toast(e.message, 'error'); }
}

// ─────────────────────────────────────────────
//  LOCALIDADES
// ─────────────────────────────────────────────
async function loadLocalidades(page = 1) {
  state.locPage = page;
  const tbody = document.getElementById('tbody-localidades');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="7"><div class="loader"></div></td></tr>';
  try {
    const data = await api('GET', `/localidades?page=${page}&per_page=20`);
    if (!data?.items?.length) {
      tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="icon">📍</div><p>Nenhuma localidade cadastrada</p></div></td></tr>';
      document.getElementById('pag-localidades').style.display = 'none';
      return;
    }
    tbody.innerHTML = data.items.map(l => `<tr>
      <td data-label="ID" class="td-mono">${l.id}</td>
      <td data-label="País">${l.pais || '—'}</td>
      <td data-label="Estado">${l.estado || '—'}</td>
      <td data-label="Município">${l.municipio || '—'}</td>
      <td data-label="Bioma">${l.bioma || '—'}</td>
      <td data-label="Coords">${l.latitude != null ? `${l.latitude.toFixed(3)}, ${l.longitude?.toFixed(3)}` : '—'}</td>
      <td data-label="Ações" class="td-actions">
        <button class="btn btn-sm btn-ghost" onclick='editLocalidade(${JSON.stringify(l).replace(/'/g,"&#39;")})'>Editar</button>
      </td>
    </tr>`).join('');
    renderPagination('pag-localidades', data.page, data.pages, p => loadLocalidades(p));
    state.allLocalidades = [];
  } catch(e) { tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--danger)">Erro: ${e.message}</td></tr>`; }
}

function openModalLocalidade() {
  state.editingLoc = null;
  document.getElementById('modal-loc-title').textContent = 'Nova Localidade';
  ['l-estado','l-municipio','l-localidade','l-lat','l-lon','l-alt','l-prec','l-metodo','l-bioma']
    .forEach(id => document.getElementById(id).value = '');
  document.getElementById('l-pais').value = 'Brasil';
  openModal('modal-loc-overlay');
}

function editLocalidade(l) {
  if (typeof l === 'string') l = JSON.parse(l);
  state.editingLoc = l.id;
  document.getElementById('modal-loc-title').textContent = 'Editar Localidade';
  document.getElementById('l-pais').value = l.pais || 'Brasil';
  document.getElementById('l-estado').value = l.estado || '';
  document.getElementById('l-municipio').value = l.municipio || '';
  document.getElementById('l-localidade').value = l.localidade || '';
  document.getElementById('l-lat').value = l.latitude || '';
  document.getElementById('l-lon').value = l.longitude || '';
  document.getElementById('l-alt').value = l.altitude_m || '';
  document.getElementById('l-prec').value = l.precisao_coordenadas_m || '';
  document.getElementById('l-metodo').value = l.metodo_geolocalizacao || '';
  document.getElementById('l-bioma').value = l.bioma || '';
  openModal('modal-loc-overlay');
}

async function saveLocalidade() {
  try {
    const body = {
      pais: document.getElementById('l-pais').value || 'Brasil',
      estado: document.getElementById('l-estado').value || undefined,
      municipio: document.getElementById('l-municipio').value || undefined,
      localidade: document.getElementById('l-localidade').value || undefined,
      latitude: document.getElementById('l-lat').value ? parseFloat(document.getElementById('l-lat').value) : undefined,
      longitude: document.getElementById('l-lon').value ? parseFloat(document.getElementById('l-lon').value) : undefined,
      altitude_m: document.getElementById('l-alt').value ? parseFloat(document.getElementById('l-alt').value) : undefined,
      precisao_coordenadas_m: document.getElementById('l-prec').value ? parseFloat(document.getElementById('l-prec').value) : undefined,
      metodo_geolocalizacao: document.getElementById('l-metodo').value || undefined,
      bioma: document.getElementById('l-bioma').value || undefined,
    };
    Object.keys(body).forEach(k => body[k] === undefined && delete body[k]);
    if (state.editingLoc) {
      await api('PUT', `/localidades/${state.editingLoc}`, body);
      toast('Localidade atualizada!');
    } else {
      await api('POST', '/localidades', body);
      toast('Localidade criada!');
    }
    closeModal('modal-loc-overlay');
    loadLocalidades(state.locPage);
  } catch(e) { toast(e.message, 'error'); }
}

// ─────────────────────────────────────────────
//  EMPRÉSTIMOS
// ─────────────────────────────────────────────
function switchLoanTab(tab) {
  state.loanTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  loadEmprestimos();
}

async function loadSelectsForEmprestimo() {
  try {
    if (!state.allEspecimes.length) {
      const r = await api('POST', '/especimes/buscar', { page:1, per_page:200, status:'ativo' });
      state.allEspecimes = r?.items || [];
    }
    fillSelect('em-especime', state.allEspecimes,
      e => `${e.codigo_catalogo} — ${e.taxonomia?.nome_cientifico || 'Sem taxonomia'}`,
      e => e.id);
  } catch(e) {}
}

async function loadEmprestimos() {
  const container = document.getElementById('emprestimos-list');
  container.innerHTML = '<div style="text-align:center;padding:40px"><div class="loader"></div></div>';
  try {
    const params = new URLSearchParams({ page:1, per_page:50 });
    if (state.loanTab === 'ativos') {
      params.set('apenas_ativos', 'true');
    } else {
      params.set('apenas_ativos', 'false');
    }
    const data = await api('GET', `/emprestimos?${params}`);
    if (!data?.items?.length) {
      container.innerHTML = '<div class="empty-state"><div class="icon">📦</div><p>Nenhum empréstimo encontrado</p></div>';
      return;
    }
    container.innerHTML = data.items.map(em => {
      const saida = new Date(em.data_saida).toLocaleDateString('pt-BR');
      const retorno = em.data_prevista_retorno ? new Date(em.data_prevista_retorno).toLocaleDateString('pt-BR') : '—';
      const nome = em.especime?.taxonomia?.nome_cientifico || 'Espécime';
      const cod = em.especime?.codigo_catalogo || `#${em.especime_id}`;
      return `<div class="loan-card">
        <div>
          <div class="lc-title">${nome}</div>
          <div class="lc-code">${cod}</div>
          <div class="lc-meta">📍 ${em.instituicao_destino} · 👤 ${em.pesquisador_responsavel}</div>
          <div class="lc-meta">📅 Saída: ${saida} · Retorno previsto: ${retorno}</div>
          ${em.finalidade ? `<div class="lc-meta" style="margin-top:4px;color:var(--text)">${em.finalidade}</div>` : ''}
        </div>
        <div class="loan-card-actions">
          ${em.ativo ? `<button class="btn btn-sm btn-warn" onclick="devolverEmprestimo(${em.id})">Devolver</button>` : '<span class="tag tag-descartado">Devolvido</span>'}
        </div>
      </div>`;
    }).join('');
  } catch(e) { container.innerHTML = `<div style="color:var(--danger);padding:20px">Erro: ${e.message}</div>`; }
}

function openModalEmprestimo() {
  ['em-inst','em-pesq','em-saida','em-retorno','em-final','em-obs'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('em-especime').value = '';
  const today = new Date().toISOString().substring(0,10);
  document.getElementById('em-saida').value = today;
  openModal('modal-emp-overlay');
}

async function saveEmprestimo() {
  try {
    const body = {
      especime_id: parseInt(document.getElementById('em-especime').value),
      instituicao_destino: document.getElementById('em-inst').value.trim(),
      pesquisador_responsavel: document.getElementById('em-pesq').value.trim(),
      data_saida: document.getElementById('em-saida').value,
      data_prevista_retorno: document.getElementById('em-retorno').value || undefined,
      finalidade: document.getElementById('em-final').value || undefined,
      observacoes: document.getElementById('em-obs').value || undefined,
    };
    await api('POST', '/emprestimos', body);
    toast('Empréstimo registrado!');
    closeModal('modal-emp-overlay');
    loadEmprestimos();
  } catch(e) { toast(e.message, 'error'); }
}

async function devolverEmprestimo(id) {
  if (!confirm('Confirmar devolução deste espécime?')) return;
  try {
    const today = new Date().toISOString();
    await api('PUT', `/emprestimos/${id}`, { data_retorno: today, ativo: false });
    toast('Devolução registrada!');
    loadEmprestimos();
  } catch(e) { toast(e.message, 'error'); }
}

// ─────────────────────────────────────────────
//  USUÁRIOS
// ─────────────────────────────────────────────
async function loadUsuarios() {
  const tbody = document.getElementById('tbody-usuarios');
  tbody.innerHTML = '<tr class="loading-row"><td colspan="6"><div class="loader"></div></td></tr>';
  try {
    const data = await api('GET', '/usuarios?page=1&per_page=50');
    if (!data?.items?.length) { tbody.innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="icon">👤</div><p>Nenhum usuário</p></div></td></tr>'; return; }
    tbody.innerHTML = data.items.map(u => `<tr>
      <td data-label="ID" class="td-mono">${u.id}</td>
      <td data-label="Nome">${u.nome}</td>
      <td data-label="E-mail" style="color:var(--muted);font-size:.82rem">${u.email}</td>
      <td data-label="Perfil"><span class="tag ${u.perfil==='administrador'?'tag-emprestado':u.perfil==='curador'?'tag-em_processamento':'tag-ativo'}">${u.perfil}</span></td>
      <td data-label="Status"><span class="tag ${u.ativo?'tag-ativo':'tag-descartado'}">${u.ativo?'Ativo':'Inativo'}</span></td>
      <td data-label="Ações" class="td-actions">
        ${u.id !== state.user?.id ? `<button class="btn btn-sm btn-danger" onclick="toggleUserAtivo(${u.id},${u.ativo})">${u.ativo?'Desativar':'Ativar'}</button>` : '<span style="color:var(--muted);font-size:.78rem">Você</span>'}
      </td>
    </tr>`).join('');
  } catch(e) { tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--danger)">Erro: ${e.message}</td></tr>`; }
}

function openModalUsuario() {
  ['u-nome','u-email','u-senha'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('u-perfil').value = 'leitor';
  openModal('modal-usr-overlay');
}

async function saveUsuario() {
  try {
    const body = {
      nome: document.getElementById('u-nome').value.trim(),
      email: document.getElementById('u-email').value.trim(),
      senha: document.getElementById('u-senha').value,
      perfil: document.getElementById('u-perfil').value,
    };
    await api('POST', '/usuarios', body);
    toast('Usuário criado!');
    closeModal('modal-usr-overlay');
    loadUsuarios();
  } catch(e) { toast(e.message, 'error'); }
}

async function toggleUserAtivo(id, ativo) {
  if (!confirm(`${ativo ? 'Desativar' : 'Ativar'} este usuário?`)) return;
  try {
    await api('PUT', `/usuarios/${id}`, { ativo: !ativo });
    toast(`Usuário ${ativo ? 'desativado' : 'ativado'}!`);
    loadUsuarios();
  } catch(e) { toast(e.message, 'error'); }
}

// ─────────────────────────────────────────────
//  PAGINAÇÃO
// ─────────────────────────────────────────────
function renderPagination(id, page, pages, onClick) {
  const el = document.getElementById(id);
  if (!pages || pages <= 1) { el.style.display = 'none'; return; }
  el.style.display = 'flex';
  const from = Math.max(1, page - 2), to = Math.min(pages, page + 2);
  let btns = '';
  if (from > 1) btns += `<button class="page-btn" onclick="(${onClick})(1)">1</button>`;
  if (from > 2) btns += `<span style="color:var(--muted);padding:4px 4px">…</span>`;
  for (let i = from; i <= to; i++) btns += `<button class="page-btn${i===page?' current':''}" onclick="(${onClick})(${i})">${i}</button>`;
  if (to < pages - 1) btns += `<span style="color:var(--muted);padding:4px 4px">…</span>`;
  if (to < pages) btns += `<button class="page-btn" onclick="(${onClick})(${pages})">${pages}</button>`;
  el.innerHTML = `<span>Página ${page} de ${pages}</span><div class="pagination-btns">${btns}</div>`;
}

// ─────────────────────────────────────────────
//  MODAL UTILS
// ─────────────────────────────────────────────
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
function closeOverlay(e, id) { if (e.target.id === id) closeModal(id); }
document.addEventListener('keydown', e => { if (e.key === 'Escape') document.querySelectorAll('.overlay.open').forEach(o => o.classList.remove('open')); });

// ─────────────────────────────────────────────
//  INIT
// ─────────────────────────────────────────────
(function init() {
  const currentPage = window.location.pathname.split('/').pop();
  const isLoginPage = currentPage === 'login.html';

  if (state.token && state.user) {
    if (isLoginPage) {
      window.location.href = 'index.html';
      return;
    }
    postLogin();
  } else if (!isLoginPage) {
    window.location.href = 'login.html';
    return;
  }

  const pwInput = document.getElementById('login-senha');
  const emailInput = document.getElementById('login-email');
  if (pwInput) {
    pwInput.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); doLogin(); } });
    pwInput.addEventListener('input', () => {
      pwInput.classList.remove('input-error');
      const err = document.getElementById('login-error');
      if (err) err.style.display = 'none';
    });
  }
  if (emailInput) {
    emailInput.addEventListener('input', () => {
      const err = document.getElementById('login-error');
      if (err) err.style.display = 'none';
    });
  }
})();
