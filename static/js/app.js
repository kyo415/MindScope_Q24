'use strict';
if (window.location.protocol === 'file:') {
  document.addEventListener('DOMContentLoaded', () => {
    const main = document.getElementById('main-content');
    if (main) {
      const banner = document.createElement('div');
      banner.className = 'local-file-warning';
      banner.innerHTML = '<strong>Bạn đang mở file HTML trực tiếp</strong>Để tải 10 câu hỏi và dự đoán Q24, hãy chạy <b>CHAY_Q24_WINDOWS.bat</b>, sau đó mở <b>http://127.0.0.1:5055</b>. Không dùng Live Server hoặc mở file HTML trực tiếp.';
      main.prepend(banner);
    }
  });
}


const STEPS = [
  { title: 'Thông tin chung', note: 'Một vài thông tin cơ bản để bắt đầu.', symbol: '◉', ids: ['Q1', 'Q2'] },
  { title: 'Trải nghiệm', note: 'Những trải nghiệm liên quan đến bạo lực và bắt nạt.', symbol: '◇', ids: ['Q15', 'Q16', 'Q17', 'Q20', 'Q21'] },
  { title: 'Cảm xúc & kết nối', note: 'Cảm xúc, giấc ngủ và các mối quan hệ xã hội.', symbol: '♡', ids: ['Q22', 'Q23', 'Q27'] },
];

const $ = (id) => document.getElementById(id);
let questions = [];
let stepIndex = 0;
let currentReceipt = null;

function text(id, value) { $(id).textContent = String(value); }
function getAnswer(code) {
  const selected = document.querySelector(`input[name="${code}"]:checked`);
  return selected ? Number(selected.value) : null;
}
function getAnswers() { return Object.fromEntries(questions.map(q => [q.id, getAnswer(q.id)])); }
function answeredCount() { return questions.filter(q => getAnswer(q.id) !== null).length; }
function displayPercent(n) { return `${(Number(n) * 100).toFixed(1).replace('.', ',')}%`; }
function focusSection(id) { $(id).scrollIntoView({ behavior: 'smooth', block: 'start' }); }
function clearError() {
  $('form-error').hidden = true;
  text('form-error', '');
  document.querySelectorAll('.question.invalid').forEach(x => x.classList.remove('invalid'));
}
function setError(message) {
  text('form-error', message);
  $('form-error').hidden = false;
}
function updateProgress() {
  const count = answeredCount();
  text('progress-text', `${count} / ${questions.length || 10} câu đã hoàn thành`);
  $('progress-bar').style.width = `${(count / (questions.length || 10)) * 100}%`;
  text('step-indicator', `BƯỚC 0${stepIndex + 1} / 03`);
  document.querySelectorAll('[data-step-item]').forEach(node => {
    const index = Number(node.dataset.stepItem);
    node.classList.toggle('active', index === stepIndex);
    node.classList.toggle('done', index < stepIndex);
  });
  document.querySelectorAll('.step-tab').forEach((node, index) => {
    node.classList.toggle('active', index === stepIndex);
    node.classList.toggle('done', index < stepIndex);
  });
}
function syncBullying() {
  const count = getAnswer('Q20');
  const items = [...document.querySelectorAll('input[name="Q21"]')];
  if (!items.length) return;
  for (const input of items) {
    if (count === 1) {
      input.checked = input.value === '1';
      input.disabled = input.value !== '1';
    } else if (count !== null) {
      input.disabled = input.value === '1';
      if (input.value === '1') input.checked = false;
    } else {
      input.disabled = false;
    }
  }
  const hint = $('q21-help');
  if (hint) {
    hint.textContent = count === 1
      ? 'Vì bạn chọn 0 ngày ở Q20, hệ thống tự chọn phương án “Không bị bắt nạt”.'
      : 'Nếu từng bị bắt nạt, hãy chọn hình thức xảy ra nhiều nhất.';
  }
}
function makeQuestion(question) {
  const block = document.createElement('div');
  block.className = 'question';
  block.id = `question-${question.id}`;
  const title = document.createElement('div');
  title.id = `label-${question.id}`;
  title.className = 'question-title';
  const badge = document.createElement('span');
  badge.className = 'question-code';
  badge.textContent = question.id;
  const questionTitle = document.createElement('span');
  questionTitle.textContent = question.text;
  title.append(badge, questionTitle);
  block.append(title);

  const choices = document.createElement('div');
  choices.className = 'option-grid';
  choices.setAttribute('role', 'group');
  choices.setAttribute('aria-labelledby', title.id);
  for (const option of question.options) {
    const label = document.createElement('label');
    label.className = 'option';
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = question.id;
    radio.value = String(option.value);
    radio.setAttribute('aria-label', option.label);
    const valueText = document.createElement('span');
    valueText.textContent = option.label;
    label.append(radio, valueText);
    radio.addEventListener('change', () => {
      clearError();
      if (question.id === 'Q20') syncBullying();
      updateProgress();
    });
    choices.append(label);
  }
  block.append(choices);
  if (question.id === 'Q21') {
    const hint = document.createElement('p');
    hint.className = 'question-help';
    hint.id = 'q21-help';
    block.append(hint);
  }
  return block;
}
function buildQuestions(payload) {
  questions = payload.questions;
  const byId = Object.fromEntries(questions.map(question => [question.id, question]));
  const destination = $('question-panels');
  destination.replaceChildren();
  STEPS.forEach((group, index) => {
    const panel = document.createElement('section');
    panel.className = 'step-panel';
    panel.dataset.index = index;
    panel.hidden = index !== 0;
    const heading = document.createElement('div');
    heading.className = 'step-heading';
    const icon = document.createElement('span');
    icon.className = 'step-heading-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = group.symbol;
    const content = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = `Bước ${index + 1} · ${group.title}`;
    const desc = document.createElement('p');
    desc.textContent = group.note;
    content.append(title, desc);
    heading.append(icon, content);
    panel.append(heading);
    for (const code of group.ids) {
      if (!byId[code]) throw new Error(`Không tìm thấy câu hỏi ${code}.`);
      panel.append(makeQuestion(byId[code]));
    }
    destination.append(panel);
  });
  $('loading').hidden = true;
  $('survey-form').hidden = false;
  syncBullying();
  updateProgress();
}
function validateStep() {
  clearError();
  const missing = STEPS[stepIndex].ids.filter(id => getAnswer(id) === null);
  if (!missing.length) return true;
  missing.forEach(id => $(`question-${id}`).classList.add('invalid'));
  setError(`Bạn cần hoàn thành ${missing.length} câu hỏi: ${missing.join(', ')}.`);
  $(`question-${missing[0]}`).scrollIntoView({ behavior: 'smooth', block: 'center' });
  return false;
}
function goToStep(nextIndex) {
  stepIndex = Math.min(STEPS.length - 1, Math.max(0, nextIndex));
  document.querySelectorAll('.step-panel').forEach(panel => {
    panel.hidden = Number(panel.dataset.index) !== stepIndex;
  });
  $('prev-btn').hidden = stepIndex === 0;
  $('next-btn').hidden = stepIndex === STEPS.length - 1;
  $('predict-btn').hidden = stepIndex !== STEPS.length - 1;
  $('consent-panel').hidden = stepIndex !== STEPS.length - 1;
  $('form-help').textContent = stepIndex === STEPS.length - 1
    ? 'Không bắt buộc lưu dữ liệu để dự đoán.'
    : 'Hãy chọn một phương án cho từng câu hỏi.';
  clearError();
  updateProgress();
  focusSection('survey-card');
}
async function requestJson(url, options = {}) {
  const response = await fetch(url, { cache: 'no-store', ...options });
  let data;
  try { data = await response.json(); } catch { throw new Error('Máy chủ trả về dữ liệu không hợp lệ.'); }
  if (!response.ok) {
    const message = typeof data.detail === 'string' ? data.detail : 'Yêu cầu không thành công.';
    throw new Error(message);
  }
  return data;
}
async function refreshModelInfo() {
  const country = $('country').value;
  text('model-caption', 'Đang tải thông tin mô hình…');
  try {
    const details = await requestJson(`/api/model-info?country=${encodeURIComponent(country)}`);
    if ($('country').value !== country) return;
    text('model-caption', `Random Forest · ${details.train_rows.toLocaleString('vi-VN')} mẫu huấn luyện · ${details.test_rows.toLocaleString('vi-VN')} mẫu kiểm tra`);
  } catch {
    text('model-caption', 'Thông tin mô hình hiện chưa khả dụng.');
  }
}
function showResult(result) {
  $('survey-card').hidden = true;
  $('result-card').hidden = false;
  text('result-label', result.predicted_label);
  text('result-code', `Q24 = ${result.predicted_code}  ·  ${result.country}`);
  text('result-orb', result.predicted_code === 1 ? '✳' : '◎');
  text('score-number', displayPercent(result.model_score_yes));
  $('score-bar').style.width = `${Math.max(0, Math.min(100, result.model_score_yes * 100))}%`;
  text('metric-f1', Number(result.metrics.f1).toFixed(3));
  text('metric-recall', Number(result.metrics.recall).toFixed(3));
  text('metric-auc', Number(result.metrics.roc_auc).toFixed(3));
  text('metric-description', `Đánh giá trên ${result.test_rows.toLocaleString('vi-VN')} mẫu kiểm tra của ${result.country}. Các chỉ số không đo mức chắc chắn cho từng cá nhân.`);
  currentReceipt = result.receipt || null;
  $('receipt-panel').hidden = !result.saved;
  text('receipt-value', currentReceipt || '');
  text('receipt-status', '');
  $('delete-current-btn').hidden = !currentReceipt;
  focusSection('result-card');
}
async function submitPrediction(event) {
  event.preventDefault();
  if (!validateStep()) return;
  const button = $('predict-btn');
  button.disabled = true;
  button.textContent = 'Đang xử lý dữ liệu…';
  try {
    const result = await requestJson('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        country: $('country').value,
        answers: getAnswers(),
        save_response: $('save-opt-in').checked,
      }),
    });
    showResult(result);
  } catch (error) {
    setError(error.message || 'Không thể kết nối với máy chủ.');
    $('form-error').scrollIntoView({ behavior: 'smooth', block: 'center' });
  } finally {
    button.disabled = false;
    button.textContent = '✧ Xem dự đoán Q24';
  }
}
function resetSurvey() {
  $('survey-form').reset();
  $('country').value = 'Bhutan';
  $('result-card').hidden = true;
  $('survey-card').hidden = false;
  $('receipt-panel').hidden = true;
  $('save-opt-in').checked = false;
  currentReceipt = null;
  $('result-card').querySelector('.metrics-section').open = false;
  syncBullying();
  goToStep(0);
  refreshModelInfo();
}
async function copyReceipt() {
  if (!currentReceipt) return;
  try {
    await navigator.clipboard.writeText(currentReceipt);
    text('receipt-status', 'Đã sao chép mã biên nhận. Hãy lưu mã tại nơi riêng tư.');
  } catch {
    text('receipt-status', 'Không thể tự sao chép. Hãy chọn và sao chép mã phía trên.');
  }
}
async function deleteCurrent() {
  if (!currentReceipt) return;
  if (!confirm('Xóa vĩnh viễn bản ghi khảo sát này khỏi SQLite?')) return;
  const button = $('delete-current-btn');
  button.disabled = true;
  try {
    await requestJson('/api/records/delete', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ receipt: currentReceipt }),
    });
    currentReceipt = null;
    text('receipt-status', 'Đã xóa bản ghi khỏi cơ sở dữ liệu.');
    text('receipt-value', 'Đã xóa');
    button.hidden = true;
  } catch (error) { text('receipt-status', error.message); }
  finally { button.disabled = false; }
}
async function lookupReceipt(event) {
  event.preventDefault();
  const receipt = $('receipt-input').value.trim();
  const output = $('lookup-output');
  output.hidden = false;
  output.replaceChildren();
  output.textContent = 'Đang kiểm tra mã biên nhận…';
  try {
    const record = await requestJson('/api/records/lookup', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ receipt }),
    });
    output.replaceChildren();
    const info = document.createElement('div');
    const date = new Date(record.created_at).toLocaleString('vi-VN');
    const details = Object.entries(record.answers).map(([k, v]) => `${k}=${v}`).join(' · ');
    info.textContent = `Đã tìm thấy bản ghi · ${date} · ${record.country}\nKết quả dự đoán: Q24=${record.predicted_code} (${record.predicted_label})\n10 mã câu trả lời: ${details}`;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Xóa bản ghi này';
    button.addEventListener('click', async () => {
      if (!confirm('Bạn chắc chắn muốn xóa bản ghi này?')) return;
      try {
        await requestJson('/api/records/delete', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ receipt }),
        });
        output.textContent = 'Đã xóa bản ghi khỏi cơ sở dữ liệu.';
        $('receipt-input').value = '';
      } catch (error) { output.textContent = error.message; }
    });
    output.append(info, button);
  } catch (error) { output.textContent = error.message; }
}
async function init() {
  $('country').addEventListener('change', refreshModelInfo);
  $('prev-btn').addEventListener('click', () => goToStep(stepIndex - 1));
  $('next-btn').addEventListener('click', () => { if (validateStep()) goToStep(stepIndex + 1); });
  $('survey-form').addEventListener('submit', submitPrediction);
  $('again-btn').addEventListener('click', resetSurvey);
  $('print-btn').addEventListener('click', () => window.print());
  $('copy-receipt-btn').addEventListener('click', copyReceipt);
  $('delete-current-btn').addEventListener('click', deleteCurrent);
  $('lookup-form').addEventListener('submit', lookupReceipt);
  try {
    const payload = await requestJson('/api/questions');
    if (!Array.isArray(payload.questions) || payload.questions.length !== 10) throw new Error('Bộ câu hỏi không đủ 10 mục.');
    buildQuestions(payload);
    await refreshModelInfo();
  } catch (error) {
    $('loading').textContent = `Không tải được câu hỏi: ${error.message}. Hãy kiểm tra terminal Python và tải lại trang.`;
  }
}
init();
