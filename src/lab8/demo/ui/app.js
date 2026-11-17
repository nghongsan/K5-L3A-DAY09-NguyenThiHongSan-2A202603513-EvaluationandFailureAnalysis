const $ = (s) => document.querySelector(s);
const info = {
 workflow: {name:'Workflow',icon:'⇢',color:'#11816c',tint:'#edf7f2',tag:'FIXED STEPS',summary:'Các bước Python cố định. Model chỉ hỗ trợ soạn phản hồi.',explain:'Một checklist đã định trước: đọc claim → kiểm đơn → tính quote → gọi host. Phù hợp khi luật nghiệp vụ và đường đi đã rõ.'},
 single: {name:'Single Agent',icon:'◉',color:'#596db5',tint:'#f0f2fb',tag:'BOUNDED REACT',summary:'Một agent đọc kết quả, chọn tool tiếp theo. Tối đa 8 lượt.',explain:'Callback decide xem observation rồi chọn tool đọc tiếp. Vòng ReAct giới hạn 8 lượt. MockLLM mô phỏng usage; code chọn tool và tính tiền.'},
 orchestrator: {name:'Orchestrator',icon:'⌘',color:'#b88b42',tint:'#fbf5eb',tag:'READ-ONLY DELEGATION',summary:'Điều phối giao việc cho investigator qua handoff đã lọc.',explain:'Orchestrator chuyển handoff trong allowlist cho investigator. Investigator chỉ có tool đọc; orchestrator nhận quote rồi gọi host để ghi tiền.'}
};
let cases = [], data = null, selected = 'workflow';
const money = (n) => new Intl.NumberFormat('vi-VN').format(n);
const escape = (v) => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function renderCards() {
 $('#cards').innerHTML = Object.entries(info).map(([shape, i]) => {
  const row = data?.rows.find(r => r.shape === shape), r = row?.result;
  const refunded = r ? r.refund_effects.reduce((sum, e) => sum + e.amount_vnd, 0) : null;
  return `<article class="card" style="--tone:${i.color};--tint:${i.tint}"><div class="card-top"><span class="architecture-icon">${i.icon}</span><div><h3>${i.name}</h3><span class="tag">${i.tag}</span></div></div><p class="card-summary">${i.summary}</p><div class="result-line"><span class="status ${r?.status || ''}">${r ? escape(r.status) : 'CHƯA CHẠY'}</span><span class="verified">${row ? row.passed ? '✓ Khớp kỳ vọng public' : '✕ Không khớp kỳ vọng' : '—'}</span></div><div class="refund-label">TIỀN HOÀN TRONG LEDGER</div><div class="refund-amount">${r ? money(refunded) : '—'}<small>VND</small></div><div class="quote">Quote đầy đủ: ${r ? money(r.proposal_amount) + 'đ' : '—'}</div><div class="metrics"><div><strong>${r ? r.model_calls : '—'}</strong><span>MODEL CALLS</span></div><div><strong>${r ? r.tool_calls : '—'}</strong><span>TOOL CALLS</span></div><div><strong>${r ? money(r.cost_estimate) : '—'}</strong><span>VND MÔ PHỎNG / LƯỢT CUỐI</span></div></div><div class="ledger-note"><span>${r ? r.refund_effects.length : '—'} refund effect</span><span>${r ? r.committed_audit_count : '—'} committed audit</span></div></article>`;
 }).join('');
}
const labels = {tool:'Gọi tool đọc',claim:'Kiểm tra claim',lookup_order:'Kiểm tra đơn & quyền sở hữu',quote:'Code tính quote',react:'Kết thúc vòng ReAct',decision:'Quyết định cuối',handoff:'Chuyển handoff đã lọc',investigator:'Investigator trả kết quả',issue_refund:'Host kiểm tra và ghi refund',crash:'Crash được mô phỏng',error:'Lỗi'};
function renderTrace() {
 $('#explain-title').textContent = info[selected].name;
 $('#explain-body').textContent = info[selected].explain;
 document.querySelectorAll('[data-shape]').forEach(b => {b.classList.toggle('selected', b.dataset.shape === selected); b.setAttribute('aria-pressed', String(b.dataset.shape === selected));});
 if (!data) return;
 const row = data.rows.find(r => r.shape === selected);
 $('#trace').innerHTML = row.attempts.map(a => `<h4 class="attempt-title">LẦN ${a.number} <span> / ${escape(a.status)}${a.crash_at ? ' · sau effect, trước checkpoint' : ''}</span></h4>${a.events.map((event, idx) => `<div class="event"><span class="event-number">${idx+1}</span><strong>${escape(labels[event.kind] || event.kind)}</strong><code>${escape(JSON.stringify(event.payload, null, 2))}</code></div>`).join('') || '<p class="subtle">Không có sự kiện trước crash.</p>'}`).join('');
}
function updateScenario() {
 const scenario = cases.find(c => c.id === $('#case').value);
 $('#scenario-description').textContent = scenario?.description || '';
 $('#mode-note').textContent = $('#mode').value === 'retry' ? 'Mỗi kiến trúc chạy hai lần trên cùng database. Kiểm tra vẫn chỉ có một refund.' : $('#mode').value === 'crash' ? 'C-001 sẽ crash sau khi ghi effect, rồi chạy lại trên cùng database để kiểm tra phục hồi.' : 'Mỗi lần so sánh tạo dữ liệu mới cho từng kiến trúc.';
}
async function run() {
 const seed = Number($('#seed').value);
 if (!Number.isInteger(seed) || seed < 0 || seed > 999999 || !$('#seed').value.trim()) { $('#error').textContent = 'Seed phải là số nguyên từ 0 đến 999999.'; $('#error').hidden = false; return; }
 $('#error').hidden = true;
 $('#run').disabled = true; $('#case').disabled = true; $('#mode').disabled = true; $('#seed').disabled = true;
 $('#run').textContent = 'Đang chạy backend…'; $('#run-state').textContent = 'Đang xử lý 3 kiến trúc…'; $('#cards').classList.add('loading');
 try {
  const response = await fetch('/api/compare', {method:'POST', headers:{'Content-Type':'application/json','X-Demo-Request':'1'},body:JSON.stringify({claim_id:$('#case').value, seed, mode:$('#mode').value})});
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'Backend không phản hồi.');
  data = payload; renderCards(); renderTrace();
  $('#run-state').textContent = `${data.claim_id} · seed ${data.seed} · ${data.rows.filter(r => r.passed).length}/3 đúng kỳ vọng`;
 } catch(e) { $('#error').textContent = e.message; $('#error').hidden = false; $('#run-state').textContent = 'Chạy thất bại · chưa có kết quả mới'; }
 finally { $('#run').disabled = false; $('#case').disabled = false; $('#mode').disabled = false; $('#seed').disabled = false; $('#run').innerHTML = '<span>▶</span> Chạy so sánh'; $('#cards').classList.remove('loading'); }
}
$('#run').addEventListener('click',run);
$('#case').addEventListener('change', () => { if ($('#mode').value === 'crash' && $('#case').value !== 'C-001') $('#mode').value = 'run'; updateScenario(); });
$('#mode').addEventListener('change', () => {if ($('#mode').value === 'crash') $('#case').value = 'C-001'; updateScenario();});
document.querySelectorAll('[data-shape]').forEach(b => b.addEventListener('click', () => {selected=b.dataset.shape;renderTrace();}));
renderCards(); renderTrace();
fetch('/api/cases').then(r => {if(!r.ok) throw new Error('Không tải được kịch bản.'); return r.json();}).then(payload => {cases=payload.cases;$('#case').innerHTML=cases.map(c => `<option value="${escape(c.id)}">${escape(c.id)} · ${escape(c.title)}</option>`).join('');updateScenario();$('#run').disabled=false;}).catch(e => {$('#error').textContent=e.message;$('#error').hidden=false;$('#scenario-description').textContent='Kiểm tra Python server rồi tải lại trang.';});
