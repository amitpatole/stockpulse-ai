/**
 * TickerPulse AI - Setup Wizard Logic
 * Vanilla JS step-based state machine.
 */

const TOTAL_STEPS = 7;
let currentStep = 1;
let selectedFramework = 'crewai';

// ─── Progress Bar ────────────────────────────────────────────

function renderProgress() {
  const container = document.getElementById('progress-steps');
  container.innerHTML = '';
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const dot = document.createElement('div');
    dot.className = 'progress-dot';
    if (i === currentStep) dot.classList.add('active');
    if (i < currentStep) dot.classList.add('completed');
    container.appendChild(dot);

    if (i < TOTAL_STEPS) {
      const line = document.createElement('div');
      line.className = 'progress-line';
      if (i < currentStep) line.classList.add('completed');
      container.appendChild(line);
    }
  }
}

// ─── Navigation ──────────────────────────────────────────────

function showStep(step) {
  document.querySelectorAll('.step').forEach((el) => el.classList.remove('active'));
  const target = document.getElementById(`step-${step}`);
  if (target) target.classList.add('active');

  // Update buttons
  const backBtn = document.getElementById('btn-back');
  const nextBtn = document.getElementById('btn-next');

  backBtn.style.visibility = step === 1 ? 'hidden' : 'visible';

  if (step === 1) {
    nextBtn.textContent = 'Get Started';
  } else if (step === TOTAL_STEPS) {
    nextBtn.textContent = 'Launch TickerPulse AI';
  } else {
    nextBtn.textContent = 'Next';
  }

  // Build summary on last step
  if (step === TOTAL_STEPS) {
    buildSummary();
  }

  renderProgress();
}

function nextStep() {
  if (currentStep === TOTAL_STEPS) {
    saveAndLaunch();
    return;
  }
  if (currentStep < TOTAL_STEPS) {
    currentStep++;
    showStep(currentStep);
  }
}

function prevStep() {
  if (currentStep > 1) {
    currentStep--;
    showStep(currentStep);
  }
}

// ─── AI Provider Testing ─────────────────────────────────────

function onKeyInput(provider) {
  const input = document.getElementById(`key-${provider}`);
  const card = document.getElementById(`card-${provider}`);
  const status = document.getElementById(`status-${provider}`);
  const btn = document.getElementById(`test-${provider}`);

  if (input.value.trim()) {
    status.textContent = 'Set';
    status.className = 'status';
    card.classList.remove('configured');
    btn.className = 'btn btn-test btn-sm';
    btn.textContent = 'Test Connection';
  } else {
    status.textContent = 'Not set';
    status.className = 'status';
    card.classList.remove('configured');
  }
}

async function testProvider(provider) {
  const input = document.getElementById(`key-${provider}`);
  const btn = document.getElementById(`test-${provider}`);
  const status = document.getElementById(`status-${provider}`);
  const card = document.getElementById(`card-${provider}`);
  const apiKey = input.value.trim();

  if (!apiKey) {
    status.textContent = 'No key';
    return;
  }

  btn.textContent = 'Testing...';
  btn.disabled = true;

  try {
    const result = await window.tickerpulse.testAiProvider({
      provider: provider,
      api_key: apiKey,
    });

    if (result.success) {
      status.textContent = 'Connected';
      status.className = 'status ok';
      card.classList.add('configured');
      btn.className = 'btn btn-test btn-sm success';
      btn.textContent = 'Connected';
    } else {
      status.textContent = 'Failed';
      status.className = 'status';
      card.classList.remove('configured');
      btn.className = 'btn btn-test btn-sm error';
      btn.textContent = result.error || 'Failed';
    }
  } catch (err) {
    btn.className = 'btn btn-test btn-sm error';
    btn.textContent = 'Error';
  }

  btn.disabled = false;
}

// ─── Framework Selection ─────────────────────────────────────

function selectFramework(fw) {
  selectedFramework = fw;
  document.getElementById('fw-crewai').classList.toggle('selected', fw === 'crewai');
  document.getElementById('fw-openclaw').classList.toggle('selected', fw === 'openclaw');
}

// ─── Gather Config ───────────────────────────────────────────

function gatherConfig() {
  return {
    anthropic_api_key: document.getElementById('key-anthropic').value.trim(),
    openai_api_key: document.getElementById('key-openai').value.trim(),
    google_ai_key: document.getElementById('key-google').value.trim(),
    xai_api_key: document.getElementById('key-xai').value.trim(),
    market_timezone: document.getElementById('timezone').value,
    monthly_budget_limit: parseFloat(document.getElementById('budget-monthly').value) || 1500,
    daily_budget_warning: parseFloat(document.getElementById('budget-daily').value) || 75,
    polygon_api_key: document.getElementById('key-polygon').value.trim(),
    alpha_vantage_key: document.getElementById('key-alphavantage').value.trim(),
    finnhub_api_key: document.getElementById('key-finnhub').value.trim(),
    twelve_data_key: document.getElementById('key-twelvedata').value.trim(),
    default_agent_framework: selectedFramework,
  };
}

// ─── Summary ─────────────────────────────────────────────────

function buildSummary() {
  const config = gatherConfig();
  const grid = document.getElementById('summary-grid');

  const providers = [];
  if (config.anthropic_api_key) providers.push('Anthropic');
  if (config.openai_api_key) providers.push('OpenAI');
  if (config.google_ai_key) providers.push('Google');
  if (config.xai_api_key) providers.push('xAI');

  const dataSources = ['yfinance (free)'];
  if (config.polygon_api_key) dataSources.push('Polygon');
  if (config.alpha_vantage_key) dataSources.push('Alpha Vantage');
  if (config.finnhub_api_key) dataSources.push('Finnhub');
  if (config.twelve_data_key) dataSources.push('Twelve Data');

  const items = [
    { label: 'AI Providers', value: providers.length ? providers.join(', ') : 'None (add in Settings)' },
    { label: 'Market Timezone', value: config.market_timezone },
    { label: 'Monthly Budget', value: `$${config.monthly_budget_limit}` },
    { label: 'Daily Warning', value: `$${config.daily_budget_warning}` },
    { label: 'Data Sources', value: dataSources.join(', ') },
    { label: 'Agent Framework', value: config.default_agent_framework === 'crewai' ? 'CrewAI' : 'OpenClaw' },
  ];

  grid.innerHTML = '';
  items.forEach((item) => {
    const div = document.createElement('div');
    div.className = 'summary-item';

    const labelSpan = document.createElement('span');
    labelSpan.className = 'label';
    labelSpan.textContent = item.label;

    const valueSpan = document.createElement('span');
    valueSpan.className = 'value';
    valueSpan.textContent = item.value;

    div.appendChild(labelSpan);
    div.appendChild(valueSpan);
    grid.appendChild(div);
  });
}

// ─── Save & Launch ───────────────────────────────────────────

async function saveAndLaunch() {
  const btn = document.getElementById('btn-next');
  btn.textContent = 'Saving...';
  btn.disabled = true;

  const config = gatherConfig();

  try {
    const result = await window.tickerpulse.saveConfig(config);
    if (result.success) {
      btn.textContent = 'Launching...';
      window.tickerpulse.completeWizard();
    } else {
      btn.textContent = 'Error saving';
      btn.disabled = false;
    }
  } catch (err) {
    btn.textContent = 'Error';
    btn.disabled = false;
  }
}

// ─── Init ────────────────────────────────────────────────────

renderProgress();
showStep(1);
