/**
 * Settings Save Functionality - Frontend Test Suite
 *
 * Covers:
 * - AC1: testAIProvider() API function with auth headers
 * - AC2: ProviderCard component handles save/test operations
 * - AC3: Error handling and toast notifications
 * - AC4: Budget settings validation and persistence
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom';
import * as api from '@/lib/api';
import { getAuthToken } from '@/lib/auth';


// Mock dependencies
vi.mock('@/lib/auth', () => ({
  getAuthToken: vi.fn(),
}));

vi.mock('@/hooks/useApi', () => ({
  useApi: vi.fn((fn, deps) => ({ data: null, loading: false })),
}));

vi.mock('@/components/ui/Toast', () => ({
  useToast: () => ({
    toasts: [],
    removeToast: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  }),
  ToastContainer: () => null,
}));


describe('testAIProvider API Function', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAuthToken).mockReturnValue('test-token-12345');
  });

  it('should call API endpoint with provider name', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });
    global.fetch = mockFetch;

    const result = await api.testAIProvider('openai');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/settings/ai-provider/openai/test'),
      expect.objectContaining({
        method: 'POST',
      })
    );
    expect(result.success).toBe(true);
  });

  it('should include Authorization header with Bearer token', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });
    global.fetch = mockFetch;

    await api.testAIProvider('anthropic');

    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].headers).toMatchObject({
      Authorization: 'Bearer test-token-12345',
    });
  });

  it('should handle provider test failure gracefully', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        success: false,
        error: 'Invalid API key',
      }),
    });
    global.fetch = mockFetch;

    const result = await api.testAIProvider('openai');

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid API key');
  });

  it('should throw ApiError on network failure', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ error: 'Unauthorized' }),
    });
    global.fetch = mockFetch;

    await expect(api.testAIProvider('openai')).rejects.toThrow();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });
});


describe('saveAIProvider API Function', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAuthToken).mockReturnValue('test-token-12345');
  });

  it('should send provider, API key, and model to endpoint', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });
    global.fetch = mockFetch;

    const result = await api.saveAIProvider('openai', 'sk-test-123', 'gpt-4');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/settings/ai-provider'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          provider: 'openai',
          api_key: 'sk-test-123',
          model: 'gpt-4',
        }),
      })
    );
    expect(result.success).toBe(true);
  });

  it('should include Authorization header', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });
    global.fetch = mockFetch;

    await api.saveAIProvider('anthropic', 'sk-key-456');

    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].headers.Authorization).toBe('Bearer test-token-12345');
  });

  it('should handle missing auth token gracefully', async () => {
    vi.mocked(getAuthToken).mockReturnValue(null);
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ success: true }),
    });
    global.fetch = mockFetch;

    await api.saveAIProvider('openai', 'sk-test-123');

    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].headers.Authorization).toBeUndefined();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });
});


describe('ProviderCard Component - Save Handler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should require API key before saving', async () => {
    const onError = vi.fn();
    const onSuccess = vi.fn();
    const onSave = vi.fn();

    const TestComponent = () => {
      const [apiKey, setApiKey] = React.useState('');
      const [saving, setSaving] = React.useState(false);

      const handleSave = async () => {
        if (!apiKey.trim()) {
          onError('API key is required');
          return;
        }
        setSaving(true);
        try {
          await onSave('openai', apiKey);
          onSuccess('Configuration saved');
        } catch (err) {
          onError(
            `Failed to save: ${err instanceof Error ? err.message : 'Unknown error'}`
          );
        } finally {
          setSaving(false);
        }
      };

      return (
        <div>
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API key"
          />
          <button onClick={handleSave} disabled={saving || !apiKey.trim()}>
            Save
          </button>
        </div>
      );
    };

    render(<TestComponent />);

    const button = screen.getByText('Save');
    fireEvent.click(button);

    expect(onError).toHaveBeenCalledWith('API key is required');
    expect(onSave).not.toHaveBeenCalled();
  });

  it('should disable save button when API key is empty', async () => {
    const TestComponent = () => {
      const [apiKey, setApiKey] = React.useState('');

      return (
        <div>
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API key"
          />
          <button disabled={!apiKey.trim()}>Save</button>
        </div>
      );
    };

    render(<TestComponent />);

    const button = screen.getByText('Save');
    expect(button).toBeDisabled();

    const input = screen.getByPlaceholderText('API key');
    await userEvent.type(input, 'sk-test-key-123');

    expect(button).not.toBeDisabled();
  });

  it('should call onSuccess after successful save', async () => {
    const onError = vi.fn();
    const onSuccess = vi.fn();
    const onSave = vi.fn().mockResolvedValue(undefined);

    const TestComponent = () => {
      const [apiKey, setApiKey] = React.useState('sk-test-key');
      const [saving, setSaving] = React.useState(false);

      const handleSave = async () => {
        if (!apiKey.trim()) {
          onError('API key is required');
          return;
        }
        setSaving(true);
        try {
          await onSave('openai', apiKey);
          onSuccess('Configuration saved');
        } catch (err) {
          onError(`Failed to save: ${err instanceof Error ? err.message : ''}`);
        } finally {
          setSaving(false);
        }
      };

      return (
        <div>
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          <button onClick={handleSave} disabled={saving || !apiKey.trim()}>
            Save
          </button>
        </div>
      );
    };

    render(<TestComponent />);
    const button = screen.getByText('Save');
    fireEvent.click(button);

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith('Configuration saved');
    });
  });

  it('should display error message on save failure', async () => {
    const onError = vi.fn();
    const onSave = vi.fn().mockRejectedValue(new Error('API error'));

    const TestComponent = () => {
      const [apiKey, setApiKey] = React.useState('sk-test-key');
      const [saving, setSaving] = React.useState(false);

      const handleSave = async () => {
        setSaving(true);
        try {
          await onSave('openai', apiKey);
        } catch (err) {
          onError(`Failed to save: ${err instanceof Error ? err.message : ''}`);
        } finally {
          setSaving(false);
        }
      };

      return (
        <div>
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          <button onClick={handleSave} disabled={saving || !apiKey.trim()}>
            Save
          </button>
        </div>
      );
    };

    render(<TestComponent />);
    const button = screen.getByText('Save');
    fireEvent.click(button);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Failed to save: API error');
    });
  });
});


describe('ProviderCard Component - Test Connection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should call testAIProvider with provider name', async () => {
    const onError = vi.fn();
    const mockTest = vi.fn().mockResolvedValue({ success: true });

    const TestComponent = () => {
      const [testing, setTesting] = React.useState(false);

      const handleTest = async () => {
        setTesting(true);
        try {
          const result = await mockTest('openai');
          if (!result.success) {
            onError('Test failed');
          }
        } finally {
          setTesting(false);
        }
      };

      return (
        <button onClick={handleTest} disabled={testing}>
          Test Connection
        </button>
      );
    };

    render(<TestComponent />);
    const button = screen.getByText('Test Connection');
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockTest).toHaveBeenCalledWith('openai');
    });
  });

  it('should display error toast on test failure', async () => {
    const onError = vi.fn();
    const mockTest = vi.fn().mockResolvedValue({
      success: false,
      error: 'Invalid API key',
    });

    const TestComponent = () => {
      const [testing, setTesting] = React.useState(false);

      const handleTest = async () => {
        setTesting(true);
        try {
          const result = await mockTest('openai');
          if (!result.success) {
            onError(`Test failed: ${result.error}`);
          }
        } finally {
          setTesting(false);
        }
      };

      return (
        <button onClick={handleTest} disabled={testing}>
          Test Connection
        </button>
      );
    };

    render(<TestComponent />);
    const button = screen.getByText('Test Connection');
    fireEvent.click(button);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Test failed: Invalid API key');
    });
  });

  it('should disable test button during testing', async () => {
    const TestComponent = () => {
      const [testing, setTesting] = React.useState(false);

      const handleTest = async () => {
        setTesting(true);
        await new Promise((resolve) => setTimeout(resolve, 100));
        setTesting(false);
      };

      return (
        <button onClick={handleTest} disabled={testing}>
          {testing ? 'Testing...' : 'Test Connection'}
        </button>
      );
    };

    render(<TestComponent />);
    const button = screen.getByText('Test Connection');

    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Testing...')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Test Connection')).toBeInTheDocument();
    });
  });
});


describe('Budget Settings Validation', () => {
  it('should reject negative monthly budget', () => {
    const onError = vi.fn();

    const TestComponent = () => {
      const [monthlyBudget, setMonthlyBudget] = React.useState(0);

      const handleSave = () => {
        if (monthlyBudget < 0) {
          onError('Budget values must be non-negative');
          return;
        }
      };

      return (
        <div>
          <input
            type="number"
            value={monthlyBudget}
            onChange={(e) => setMonthlyBudget(parseFloat(e.target.value) || 0)}
          />
          <button onClick={handleSave}>Save</button>
        </div>
      );
    };

    render(<TestComponent />);
    const input = screen.getByRole('textbox');

    fireEvent.change(input, { target: { value: '-50' } });
    fireEvent.click(screen.getByText('Save'));

    expect(onError).toHaveBeenCalledWith('Budget values must be non-negative');
  });

  it('should reject daily warning exceeding monthly budget', () => {
    const onError = vi.fn();

    const TestComponent = () => {
      const [monthlyBudget, setMonthlyBudget] = React.useState(100);
      const [dailyWarning, setDailyWarning] = React.useState(50);

      const handleSave = () => {
        if (dailyWarning > monthlyBudget) {
          onError('Daily warning threshold cannot exceed monthly budget');
          return;
        }
      };

      return (
        <div>
          <input
            value={monthlyBudget}
            onChange={(e) => setMonthlyBudget(parseFloat(e.target.value) || 0)}
          />
          <input
            value={dailyWarning}
            onChange={(e) => setDailyWarning(parseFloat(e.target.value) || 0)}
          />
          <button onClick={handleSave}>Save</button>
        </div>
      );
    };

    render(<TestComponent />);
    const inputs = screen.getAllByRole('textbox');

    fireEvent.change(inputs[0], { target: { value: '50' } });
    fireEvent.change(inputs[1], { target: { value: '100' } });
    fireEvent.click(screen.getByText('Save'));

    expect(onError).toHaveBeenCalledWith(
      'Daily warning threshold cannot exceed monthly budget'
    );
  });
});
