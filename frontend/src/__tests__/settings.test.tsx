/**
 * Settings Page Component Tests
 *
 * Tests verify that:
 * - AI Provider cards render and handle configuration
 * - Framework selection works correctly
 * - Budget settings validation and persistence
 * - Toast notifications for success/error states
 * - Loading and error handling
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import SettingsPage from '@/app/settings/page';
import * as api from '@/lib/api';

// Mock components
jest.mock('@/components/layout/Header', () => {
  return function MockHeader({ title, subtitle }: { title: string; subtitle: string }) {
    return <div data-testid="mock-header">{title} - {subtitle}</div>;
  };
});

jest.mock('@/components/ui/Toast', () => ({
  ToastContainer: ({ toasts }: { toasts: any[] }) => (
    <div data-testid="toast-container">
      {toasts.map((t, i) => (
        <div key={i} data-testid={`toast-${i}`}>{t.message}</div>
      ))}
    </div>
  ),
  useToast: () => ({
    toasts: [],
    removeToast: jest.fn(),
    success: jest.fn(),
    error: jest.fn(),
  }),
}));

// Mock hooks and API
jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn((fetcher, deps, opts) => {
    // Default mock return values
    if (fetcher.name === 'getAIProviders' || fetcher.toString().includes('getAIProviders')) {
      return {
        data: [
          { name: 'openai', display_name: 'OpenAI', configured: true, models: ['gpt-4', 'gpt-3.5-turbo'], default_model: 'gpt-4' },
          { name: 'anthropic', display_name: 'Anthropic', configured: false, models: ['claude-opus', 'claude-sonnet'], default_model: 'claude-opus' },
        ],
        loading: false,
        error: null,
        refetch: jest.fn(),
      };
    }
    if (fetcher.name === 'getHealth' || fetcher.toString().includes('getHealth')) {
      return {
        data: { status: 'ok', database: 'ok', version: '1.0.0' },
        loading: false,
        error: null,
      };
    }
    return { data: null, loading: false, error: null, refetch: jest.fn() };
  }),
}));

jest.mock('@/lib/api');

describe('Settings Page', () => {
  const mockGetAIProviders = api.getAIProviders as jest.Mock;
  const mockGetHealth = api.getHealth as jest.Mock;
  const mockSaveAIProvider = api.saveAIProvider as jest.Mock;
  const mockTestAIProvider = api.testAIProvider as jest.Mock;
  const mockSetAgentFramework = api.setAgentFramework as jest.Mock;
  const mockSaveBudgetSettings = api.saveBudgetSettings as jest.Mock;
  const mockGetBudgetSettings = api.getBudgetSettings as jest.Mock;
  const mockGetAgentFramework = api.getAgentFramework as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetBudgetSettings.mockResolvedValue({
      monthly_budget: 50,
      daily_warning: 5,
    });
    mockGetAgentFramework.mockResolvedValue({
      current_framework: 'crewai',
    });
  });

  // ============================================================
  // Rendering & Layout
  // ============================================================

  it('should render settings page with header', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    });
    expect(screen.getByText(/Configure AI providers and system settings/i)).toBeInTheDocument();
  });

  it('should render AI Providers section', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('AI Providers')).toBeInTheDocument();
    });
  });

  it('should render Agent Framework section', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Agent Framework')).toBeInTheDocument();
    });
  });

  it('should render Cost Budget section', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Cost Budget')).toBeInTheDocument();
    });
  });

  it('should render System Status section', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('System Status')).toBeInTheDocument();
    });
  });

  // ============================================================
  // AI Providers Section
  // ============================================================

  it('should display loading skeleton while providers are loading', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: null,
      loading: true,
      error: null,
    }));

    const { container } = render(<SettingsPage />);

    await waitFor(() => {
      const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  it('should display provider cards when providers are loaded', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
    });
  });

  it('should show configured status for configured providers', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      const configuredStatuses = screen.getAllByText('Configured');
      expect(configuredStatuses.length).toBeGreaterThan(0);
    });
  });

  it('should show not configured status for unconfigured providers', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      const notConfiguredStatuses = screen.getAllByText(/Not configured/i);
      expect(notConfiguredStatuses.length).toBeGreaterThan(0);
    });
  });

  // ============================================================
  // Framework Selection
  // ============================================================

  it('should render framework selection buttons', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('framework-crewai')).toBeInTheDocument();
      expect(screen.getByTestId('framework-openclaw')).toBeInTheDocument();
    });
  });

  it('should select CrewAI by default', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      const crewaiButton = screen.getByTestId('framework-crewai');
      expect(crewaiButton.className).toContain('border-blue-500');
    });
  });

  it('should toggle framework selection on click', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      const openclawButton = screen.getByTestId('framework-openclaw');
      fireEvent.click(openclawButton);

      expect(openclawButton.className).toContain('border-blue-500');
    });
  });

  it('should save framework selection on button click', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      const openclawButton = screen.getByTestId('framework-openclaw');
      fireEvent.click(openclawButton);
    });

    const saveFrameworkButton = screen.getByTestId('save-framework-button');
    fireEvent.click(saveFrameworkButton);

    await waitFor(() => {
      expect(mockSetAgentFramework).toHaveBeenCalledWith('openclaw');
    });
  });

  it('should disable save button while framework is being saved', async () => {
    mockSetAgentFramework.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<SettingsPage />);

    await waitFor(() => {
      const saveFrameworkButton = screen.getByTestId('save-framework-button');
      fireEvent.click(saveFrameworkButton);

      expect(saveFrameworkButton).toBeDisabled();
    });
  });

  // ============================================================
  // Budget Settings
  // ============================================================

  it('should render monthly budget input', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('monthly-budget')).toBeInTheDocument();
    });
  });

  it('should render daily warning threshold input', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByTestId('daily-warning')).toBeInTheDocument();
    });
  });

  it('should load budget settings on mount', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(mockGetBudgetSettings).toHaveBeenCalled();
    });
  });

  it('should populate monthly budget from API response', async () => {
    mockGetBudgetSettings.mockResolvedValue({
      monthly_budget: 100,
      daily_warning: 10,
    });

    render(<SettingsPage />);

    await waitFor(() => {
      const monthlyBudgetInput = screen.getByTestId('monthly-budget') as HTMLInputElement;
      expect(monthlyBudgetInput.value).toBe('100');
    });
  });

  it('should allow changing monthly budget value', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await waitFor(() => {
      const monthlyBudgetInput = screen.getByTestId('monthly-budget') as HTMLInputElement;
      expect(monthlyBudgetInput).toBeInTheDocument();
    });

    const monthlyBudgetInput = screen.getByTestId('monthly-budget');
    await user.clear(monthlyBudgetInput);
    await user.type(monthlyBudgetInput, '150');

    expect((monthlyBudgetInput as HTMLInputElement).value).toBe('150');
  });

  it('should save budget settings when button clicked', async () => {
    mockSaveBudgetSettings.mockResolvedValue({ success: true });

    render(<SettingsPage />);

    await waitFor(() => {
      const saveBudgetButton = screen.getByTestId('save-budget-button');
      expect(saveBudgetButton).toBeInTheDocument();
    });

    const saveBudgetButton = screen.getByTestId('save-budget-button');
    fireEvent.click(saveBudgetButton);

    await waitFor(() => {
      expect(mockSaveBudgetSettings).toHaveBeenCalled();
    });
  });

  it('should validate that daily warning cannot exceed monthly budget', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await waitFor(() => {
      const monthlyBudgetInput = screen.getByTestId('monthly-budget');
      expect(monthlyBudgetInput).toBeInTheDocument();
    });

    const monthlyBudgetInput = screen.getByTestId('monthly-budget');
    const dailyWarningInput = screen.getByTestId('daily-warning');

    await user.clear(monthlyBudgetInput);
    await user.type(monthlyBudgetInput, '50');

    await user.clear(dailyWarningInput);
    await user.type(dailyWarningInput, '100');

    const saveBudgetButton = screen.getByTestId('save-budget-button');
    fireEvent.click(saveBudgetButton);

    // Should not call API due to validation error
    // This would be caught by the error toast
    await waitFor(() => {
      expect(mockSaveBudgetSettings).not.toHaveBeenCalled();
    });
  });

  it('should validate that budget values are non-negative', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);

    await waitFor(() => {
      const monthlyBudgetInput = screen.getByTestId('monthly-budget');
      expect(monthlyBudgetInput).toBeInTheDocument();
    });

    const monthlyBudgetInput = screen.getByTestId('monthly-budget');
    await user.clear(monthlyBudgetInput);
    await user.type(monthlyBudgetInput, '-50');

    const saveBudgetButton = screen.getByTestId('save-budget-button');
    fireEvent.click(saveBudgetButton);

    // Should not call API due to validation
    await waitFor(() => {
      expect(mockSaveBudgetSettings).not.toHaveBeenCalled();
    });
  });

  // ============================================================
  // System Status
  // ============================================================

  it('should display health check status', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Backend API')).toBeInTheDocument();
      expect(screen.getByText('Database')).toBeInTheDocument();
    });
  });

  it('should show healthy status when backend is ok', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });
  });

  it('should show database connection status', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('should display version information when available', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
    });
  });

  // ============================================================
  // Error Handling
  // ============================================================

  it('should handle API errors gracefully', async () => {
    mockGetBudgetSettings.mockRejectedValue(new Error('Network error'));

    render(<SettingsPage />);

    // Should not crash and should show defaults
    await waitFor(() => {
      const monthlyBudgetInput = screen.getByTestId('monthly-budget') as HTMLInputElement;
      expect(monthlyBudgetInput).toBeInTheDocument();
    });
  });

  it('should disable save buttons while loading', async () => {
    mockSaveBudgetSettings.mockImplementation(() => new Promise(() => {}));

    render(<SettingsPage />);

    await waitFor(() => {
      const saveBudgetButton = screen.getByTestId('save-budget-button');
      fireEvent.click(saveBudgetButton);

      expect(saveBudgetButton).toBeDisabled();
    });
  });

  // ============================================================
  // Integration Tests
  // ============================================================

  it('should load all settings on mount', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      expect(mockGetBudgetSettings).toHaveBeenCalled();
      expect(mockGetAgentFramework).toHaveBeenCalled();
    });
  });

  it('should maintain independent state for different sections', async () => {
    render(<SettingsPage />);

    await waitFor(() => {
      const crewaiButton = screen.getByTestId('framework-crewai');
      const openclawButton = screen.getByTestId('framework-openclaw');

      // Select openclaw
      fireEvent.click(openclawButton);
      expect(openclawButton.className).toContain('border-blue-500');

      // Change budget
      const monthlyBudgetInput = screen.getByTestId('monthly-budget');
      fireEvent.change(monthlyBudgetInput, { target: { value: '100' } });

      // Framework selection should still be openclaw
      expect(openclawButton.className).toContain('border-blue-500');
    });
  });

  it('should render without crashing with minimal data', async () => {
    jest.mocked(require('@/hooks/useApi').useApi).mockImplementation(() => ({
      data: [],
      loading: false,
      error: null,
    }));

    const { container } = render(<SettingsPage />);
    expect(container).toBeInTheDocument();
  });
});
