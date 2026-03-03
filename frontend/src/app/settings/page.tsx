```typescript
'use client';

import { useState, useEffect } from 'react';
import {
  Key,
  CheckCircle,
  XCircle,
  Loader2,
  Shield,
  DollarSign,
  Database,
  Brain,
  Eye,
  EyeOff,
} from 'lucide-react';
import { clsx } from 'clsx';
import Header from '@/components/layout/Header';
import { useApi } from '@/hooks/useApi';
import { getAIProviders, getHealth, saveAIProvider, testAIProvider, setAgentFramework, saveBudgetSettings, getBudgetSettings, getAgentFramework } from '@/lib/api';
import { ToastContainer, useToast } from '@/components/ui/Toast';
import type { AIProvider, HealthCheck } from '@/lib/types';

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'border-green-500/30 bg-green-500/5',
  anthropic: 'border-orange-500/30 bg-orange-500/5',
  google: 'border-blue-500/30 bg-blue-500/5',
  xai: 'border-purple-500/30 bg-purple-500/5',
};

const PROVIDER_ICONS: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google AI',
  xai: 'xAI',
};

interface ProviderCardProps {
  provider: AIProvider;
  onSave: (provider: string, apiKey: string, model: string) => Promise<void>;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

function ProviderCard({ provider, onSave, onSuccess, onError }: ProviderCardProps) {
  const [showKey, setShowKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [selectedModel, setSelectedModel] = useState(provider.default_model || '');
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const colorClass = PROVIDER_COLORS[provider.name] || 'border-slate-500/30 bg-slate-500/5';
  const providerId = `provider-${provider.name}`;

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const data = await testAIProvider(provider.name);
      setTestResult(data.success ? 'success' : 'error');
      if (!data.success) {
        onError(`Failed to test ${provider.display_name}: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      onError(`Failed to test ${provider.display_name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim()) {
      onError('API key is required');
      return;
    }

    setSaving(true);
    try {
      await onSave(provider.name, apiKey, selectedModel);
      onSuccess(`${provider.display_name} configuration saved`);
      setApiKey('');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      onError(`Failed to save ${provider.display_name} configuration: ${message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <article className={clsx('rounded-xl border p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500', colorClass)}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-700/50">
            <Brain className="h-5 w-5 text-slate-300" aria-hidden="true" />
          </div>
          <div>
            <h3 id={providerId} className="text-sm font-semibold text-white">
              {provider.display_name || PROVIDER_ICONS[provider.name] || provider.name}
            </h3>
            <span
              className={clsx('text-xs', provider.configured ? 'text-emerald-400' : 'text-slate-500')}
              role="status"
              aria-label={`${provider.display_name} configuration status: ${provider.configured ? 'Configured' : 'Not configured'}`}
            >
              {provider.configured ? 'Configured' : 'Not configured'}
            </span>
          </div>
        </div>

        {provider.configured ? (
          <CheckCircle className="h-5 w-5 text-emerald-400" aria-hidden="true" />
        ) : (
          <XCircle className="h-5 w-5 text-slate-600" aria-hidden="true" />
        )}
      </div>

      {/* API Key Input */}
      <div className="mt-4">
        <label htmlFor={`api-key-${provider.name}`} className="mb-1.5 block text-xs text-slate-400">
          API Key <span aria-label="required">*</span>
        </label>
        <div className="relative">
          <input
            id={`api-key-${provider.name}`}
            type={showKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={`Enter ${provider.display_name || provider.name} API key`}
            aria-required="true"
            className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 pr-10 text-sm text-white placeholder-slate-600 outline-none focus-visible:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            aria-label={showKey ? 'Hide API key' : 'Show API key'}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            {showKey ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </div>

      {/* Model Selector */}
      <div className="mt-3">
        <label htmlFor={`model-${provider.name}`} className="mb-1.5 block text-xs text-slate-400">
          Default Model
        </label>
        <select
          id={`model-${provider.name}`}
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-white outline-none focus-visible:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {provider.models && provider.models.length > 0 ? (
            provider.models.map((model) => (
              <option key={model} value={model} className="bg-slate-800">
                {model}
              </option>
            ))
          ) : (
            <option value="" className="bg-slate-800">
              No models available
            </option>
          )}
        </select>
      </div>

      {/* Action Buttons */}
      <div className="mt-4 flex items-center gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !apiKey.trim()}
          aria-busy={saving}
          aria-label={`Save ${provider.display_name} configuration`}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {saving ? <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" /> : <CheckCircle className="h-3 w-3" aria-hidden="true" />}
          Save
        </button>

        <button
          onClick={handleTest}
          disabled={testing || !provider.configured}
          aria-busy={testing}
          aria-label={`Test ${provider.display_name} connection`}
          className="flex items-center gap-2 rounded-lg bg-slate-700 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-600 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {testing ? <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" /> : <Key className="h-3 w-3" aria-hidden="true" />}
          Test Connection
        </button>

        {testResult === 'success' && (
          <span className="flex items-center gap-1 text-xs text-emerald-400" role="status">
            <CheckCircle className="h-3 w-3" aria-hidden="true" /> Connected
          </span>
        )}
        {testResult === 'error' && (
          <span className="flex items-center gap-1 text-xs text-red-400" role="status">
            <XCircle className="h-3 w-3" aria-hidden="true" /> Failed
          </span>
        )}
      </div>
    </article>
  );
}

export default function SettingsPage() {
  const { data: providers, loading: providersLoading } = useApi<AIProvider[]>(getAIProviders, []);
  const { data: health } = useApi<HealthCheck>(getHealth, [], { refreshInterval: 30000 });

  const [framework, setFramework] = useState<'crewai' | 'openclaw'>('crewai');
  const [monthlyBudget, setMonthlyBudget] = useState(50);
  const [dailyWarning, setDailyWarning] = useState(5);
  const [frameworkSaving, setFrameworkSaving] = useState(false);
  const [budgetSaving, setBudgetSaving] = useState(false);

  const { toasts, removeToast, success: showSuccess, error: showError } = useToast();

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [budgetData, frameworkData] = await Promise.all([getBudgetSettings(), getAgentFramework()]);
        setMonthlyBudget(budgetData.monthly_budget);
        setDailyWarning(budgetData.daily_warning);
        setFramework((frameworkData.current_framework as 'crewai' | 'openclaw') || 'crewai');
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    };
    loadSettings();
  }, []);

  const handleSaveProvider = async (provider: string, apiKey: string, model: string) => {
    try {
      await saveAIProvider(provider, apiKey, model);
    } catch (err) {
      throw err;
    }
  };

  const handleSetFramework = async () => {
    setFrameworkSaving(true);
    try {
      await setAgentFramework(framework);
      showSuccess(`Agent framework set to ${framework === 'crewai' ? 'CrewAI' : 'OpenClaw'}`);
    } catch (err) {
      showError('Failed to save framework selection');
    } finally {
      setFrameworkSaving(false);
    }
  };

  const handleSaveBudget = async () => {
    if (monthlyBudget < 0 || dailyWarning < 0) {
      showError('Budget values must be non-negative');
      return;
    }

    if (dailyWarning > monthlyBudget) {
      showError('Daily warning threshold cannot exceed monthly budget');
      return;
    }

    setBudgetSaving(true);
    try {
      await saveBudgetSettings(monthlyBudget, dailyWarning);
      showSuccess('Budget settings saved successfully');
    } catch (err) {
      showError('Failed to save budget settings');
    } finally {
      setBudgetSaving(false);
    }
  };

  return (
    <div className="flex flex-col">
      <Header title="Settings" subtitle="Configure AI providers and system settings" />

      <main id="main" className="flex-1 p-6">
        <ToastContainer toasts={toasts} onRemove={removeToast} />

        {/* AI Providers Section */}
        <section className="mb-8">
          <h2 className="mb-4 text-sm font-semibold text-white">AI Providers</h2>

          {providersLoading && !providers && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-56 animate-pulse rounded-xl border border-slate-700/50 bg-slate-800/30" />
              ))}
            </div>
          )}

          {providers && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {providers.map((provider) => (
                <ProviderCard
                  key={provider.name}
                  provider={provider}
                  onSave={handleSaveProvider}
                  onSuccess={showSuccess}
                  onError={showError}
                />
              ))}
            </div>
          )}

          {providers && providers.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-700 bg-slate-800/20 p-6 text-center">
              <p className="text-sm text-slate-500">No AI providers found. Check backend configuration.</p>
            </div>
          )}
        </section>

        {/* Agent Framework Section */}
        <section className="mb-8">
          <h2 className="mb-4 text-sm font-semibold text-white">Agent Framework</h2>
          <article className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
            <div className="flex items-center gap-3">
              <Shield className="h-5 w-5 text-blue-400" aria-hidden="true" />
              <div className="flex-1">
                <p className="text-sm font-medium text-white">Framework Selection</p>
                <p className="text-xs text-slate-400">Choose the AI agent orchestration framework</p>
              </div>
            </div>

            <fieldset data-testid="framework-selection" className="mt-4">
              <legend className="sr-only">Framework Selection</legend>
              <div className="flex gap-3">
                <button
                  data-testid="framework-crewai"
                  onClick={() => setFramework('crewai')}
                  aria-pressed={framework === 'crewai'}
                  className={clsx(
                    'flex-1 rounded-lg border px-4 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
                    framework === 'crewai' ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                  )}
                >
                  <p className="text-sm font-medium text-white">CrewAI</p>
                  <p className="mt-0.5 text-xs text-slate-400">Default framework - stable and well-tested</p>
                </button>
                <button
                  data-testid="framework-openclaw"
                  onClick={() => setFramework('openclaw')}
                  aria-pressed={framework === 'openclaw'}
                  className={clsx(
                    'flex-1 rounded-lg border px-4 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
                    framework === 'openclaw' ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                  )}
                >
                  <p className="text-sm font-medium text-white">OpenClaw</p>
                  <p className="mt-0.5 text-xs text-slate-400">Alternative framework - experimental</p>
                </button>
              </div>
            </fieldset>

            <button
              data-testid="save-framework-button"
              onClick={handleSetFramework}
              disabled={frameworkSaving}
              aria-busy={frameworkSaving}
              className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
            >
              {frameworkSaving && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              Save Framework Selection
            </button>
          </article>
        </section>

        {/* Budget Settings Section */}
        <section className="mb-8">
          <h2 className="mb-4 text-sm font-semibold text-white">Cost Budget</h2>
          <article className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
            <div className="flex items-center gap-3 mb-4">
              <DollarSign className="h-5 w-5 text-amber-400" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-white">Budget Controls</p>
                <p className="text-xs text-slate-400">Set spending limits for AI agent operations</p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="monthly-budget" className="mb-1.5 block text-xs text-slate-400">
                  Monthly Budget Limit <span aria-label="required">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-500" aria-hidden="true">
                    $
                  </span>
                  <input
                    id="monthly-budget"
                    data-testid="monthly-budget"
                    type="number"
                    value={monthlyBudget}
                    onChange={(e) => setMonthlyBudget(parseFloat(e.target.value) || 0)}
                    step="1"
                    min="0"
                    aria-label="Monthly budget limit in dollars"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2 pl-7 pr-3 text-sm text-white outline-none focus-visible:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 font-mono"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="daily-warning" className="mb-1.5 block text-xs text-slate-400">
                  Daily Warning Threshold <span aria-label="required">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-500" aria-hidden="true">
                    $
                  </span>
                  <input
                    id="daily-warning"
                    data-testid="daily-warning"
                    type="number"
                    value={dailyWarning}
                    onChange={(e) => setDailyWarning(parseFloat(e.target.value) || 0)}
                    step="0.50"
                    min="0"
                    aria-label="Daily warning threshold in dollars"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2 pl-7 pr-3 text-sm text-white outline-none focus-visible:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 font-mono"
                  />
                </div>
              </div>
            </div>

            <button
              data-testid="save-budget-button"
              onClick={handleSaveBudget}
              disabled={budgetSaving}
              aria-busy={budgetSaving}
              className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
            >
              {budgetSaving && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              Save Budget Settings
            </button>
          </article>
        </section>

        {/* System Health Section */}
        <section>
          <h2 className="mb-4 text-sm font-semibold text-white">System Status</h2>
          <article className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
            <div className="flex items-center gap-3 mb-4">
              <Database className="h-5 w-5 text-emerald-400" aria-hidden="true" />
              <div>
                <p className="text-sm font-medium text-white">Data Providers & Health</p>
                <p className="text-xs text-slate-400">Current status of system components</p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg bg-slate-900/50 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span
                    className={clsx(
                      'h-2 w-2 rounded-full',
                      health?.status === 'ok' ? 'bg-emerald-500' : 'bg-red-500'
                    )}
                    aria-hidden="true"
                  />
                  <span className="text-sm text-slate-300">Backend API</span>
                </div>
                <span className="text-xs text-slate-400" role="status">
                  {health ? health.status === 'ok' ? 'Healthy' : 'Unhealthy' : 'Checking...'}
                </span>
              </div>

              <div className="flex items-center justify-between rounded-lg bg-slate-900/50 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span
                    className={clsx(
                      'h-2 w-2 rounded-full',
                      health?.database === 'ok' ? 'bg-emerald-500' : health ? 'bg-red-500' : 'bg-slate-500'
                    )}
                    aria-hidden="true"
                  />
                  <span className="text-sm text-slate-300">Database</span>
                </div>
                <span className="text-xs text-slate-400" role="status">
                  {health?.database === 'ok' ? 'Connected' : health ? 'Error' : 'Checking...'}
                </span>
              </div>

              <div className="flex items-center justify-between rounded-lg bg-slate-900/50 px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
                  <span className="text-sm text-slate-300">yfinance (Free)</span>
                </div>
                <span className="text-xs text-slate-400" role="status">
                  Default Provider
                </span>
              </div>

              {health?.version && (
                <div className="mt-3 flex items-center justify-between border-t border-slate-700/50 pt-3">
                  <span className="text-xs text-slate-500">Version</span>
                  <span className="text-xs font-mono text-slate-400">{health.version}</span>
                </div>
              )}
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
```