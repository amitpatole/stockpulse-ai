import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TourOverlay from '../TourOverlay';
import { TourContext, TourContextType } from '@/context/TourContext';
import { TourStep } from '../tourSteps';

const mockTourStep: TourStep = {
  id: 'test-step',
  title: 'Test Title',
  description: 'Test Description',
  selector: '[data-test="target"]',
  position: 'bottom',
};

const mockContextValue: TourContextType = {
  isActive: true,
  currentStep: 0,
  currentTourStep: mockTourStep,
  totalSteps: 3,
  completed: false,
  skipped: false,
  nextStep: vi.fn(),
  prevStep: vi.fn(),
  skipTour: vi.fn(),
  completeTour: vi.fn(),
  startTour: vi.fn(),
  goToStep: vi.fn(),
};

describe('TourOverlay', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const target = document.createElement('div');
    target.setAttribute('data-test', 'target');
    target.style.position = 'absolute';
    target.style.top = '100px';
    target.style.left = '100px';
    target.style.width = '200px';
    target.style.height = '100px';
    document.body.appendChild(target);
  });

  afterEach(() => {
    const elements = document.querySelectorAll('[data-test="target"]');
    elements.forEach(el => el.remove());
  });

  describe('Rendering', () => {
    it('renders nothing when tour is not active', () => {
      const inactiveContext: TourContextType = {
        ...mockContextValue,
        isActive: false,
      };

      const { container } = render(
        <TourContext.Provider value={inactiveContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(container.firstChild).toBeNull();
    });

    it('renders tour overlay when active', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    it('displays title and description', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    it('renders dark overlay backdrop', () => {
      const { container } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const backdrop = container.querySelector('.bg-black.bg-opacity-60');
      expect(backdrop).toBeInTheDocument();
    });

    it('renders close button', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByLabelText('Close tour')).toBeInTheDocument();
    });
  });

  describe('Step Indicator', () => {
    it('displays correct step indicator at step 1', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Step 1 of 3')).toBeInTheDocument();
    });

    it('displays correct step indicator at middle step', () => {
      const midStepContext: TourContextType = {
        ...mockContextValue,
        currentStep: 1,
      };

      render(
        <TourContext.Provider value={midStepContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Step 2 of 3')).toBeInTheDocument();
    });

    it('displays correct step indicator at last step', () => {
      const lastStepContext: TourContextType = {
        ...mockContextValue,
        currentStep: 2,
      };

      render(
        <TourContext.Provider value={lastStepContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Step 3 of 3')).toBeInTheDocument();
    });

    it('renders indicator dots matching total steps', () => {
      const { container } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const dots = container.querySelectorAll('.w-2.h-2.rounded-full');
      expect(dots.length).toBe(3);
    });

    it('highlights current step indicator dot', () => {
      const { container } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const dots = container.querySelectorAll('.w-2.h-2.rounded-full');
      expect(dots[0]).toHaveClass('bg-amber-400');
      expect(dots[1]).toHaveClass('bg-gray-300');
      expect(dots[2]).toHaveClass('bg-gray-300');
    });
  });

  describe('Navigation Buttons', () => {
    it('calls nextStep when Next button is clicked', () => {
      const nextStepMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        nextStep: nextStepMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const nextButton = screen.getByLabelText('Next step');
      fireEvent.click(nextButton);

      expect(nextStepMock).toHaveBeenCalled();
    });

    it('hides Back button on first step', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.queryByLabelText('Previous step')).not.toBeInTheDocument();
    });

    it('shows Back button on non-first steps', () => {
      const midStepContext: TourContextType = {
        ...mockContextValue,
        currentStep: 1,
      };

      render(
        <TourContext.Provider value={midStepContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByLabelText('Previous step')).toBeInTheDocument();
    });

    it('calls prevStep when Back button is clicked', () => {
      const prevStepMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        currentStep: 1,
        prevStep: prevStepMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const backButton = screen.getByLabelText('Previous step');
      fireEvent.click(backButton);

      expect(prevStepMock).toHaveBeenCalled();
    });

    it('calls skipTour when Skip button is clicked', () => {
      const skipTourMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        skipTour: skipTourMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const skipButton = screen.getByLabelText('Skip tour');
      fireEvent.click(skipButton);

      expect(skipTourMock).toHaveBeenCalled();
    });

    it('shows Done button on last step', () => {
      const lastStepContext: TourContextType = {
        ...mockContextValue,
        currentStep: 2,
        totalSteps: 3,
      };

      render(
        <TourContext.Provider value={lastStepContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByLabelText('Complete tour')).toBeInTheDocument();
      expect(screen.queryByLabelText('Next step')).not.toBeInTheDocument();
    });

    it('calls completeTour when Done button is clicked', () => {
      const completeTourMock = vi.fn();
      const lastStepContext: TourContextType = {
        ...mockContextValue,
        currentStep: 2,
        totalSteps: 3,
        completeTour: completeTourMock,
      };

      render(
        <TourContext.Provider value={lastStepContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const doneButton = screen.getByLabelText('Complete tour');
      fireEvent.click(doneButton);

      expect(completeTourMock).toHaveBeenCalled();
    });

    it('calls skipTour when close button is clicked', () => {
      const skipTourMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        skipTour: skipTourMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const closeButton = screen.getByLabelText('Close tour');
      fireEvent.click(closeButton);

      expect(skipTourMock).toHaveBeenCalled();
    });

    it('calls skipTour when backdrop is clicked', () => {
      const skipTourMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        skipTour: skipTourMock,
      };

      const { container } = render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const backdrop = container.querySelector('.bg-black.bg-opacity-60');
      fireEvent.click(backdrop!);

      expect(skipTourMock).toHaveBeenCalled();
    });
  });

  describe('Keyboard Navigation', () => {
    it('handles Escape key to skip tour', () => {
      const skipTourMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        skipTour: skipTourMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(skipTourMock).toHaveBeenCalled();
    });

    it('handles ArrowRight key to next step', () => {
      const nextStepMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        nextStep: nextStepMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      fireEvent.keyDown(window, { key: 'ArrowRight' });

      expect(nextStepMock).toHaveBeenCalled();
    });

    it('handles Enter key to next step', () => {
      const nextStepMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        nextStep: nextStepMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      fireEvent.keyDown(window, { key: 'Enter' });

      expect(nextStepMock).toHaveBeenCalled();
    });

    it('handles ArrowLeft key to previous step', () => {
      const prevStepMock = vi.fn();
      const contextValue: TourContextType = {
        ...mockContextValue,
        currentStep: 1,
        prevStep: prevStepMock,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      fireEvent.keyDown(window, { key: 'ArrowLeft' });

      expect(prevStepMock).toHaveBeenCalled();
    });

    it('calls completeTour with Enter on last step', () => {
      const completeTourMock = vi.fn();
      const lastStepContext: TourContextType = {
        ...mockContextValue,
        currentStep: 2,
        totalSteps: 3,
        completeTour: completeTourMock,
      };

      render(
        <TourContext.Provider value={lastStepContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      fireEvent.keyDown(window, { key: 'Enter' });

      expect(completeTourMock).toHaveBeenCalled();
    });

    it('ignores keyboard events when tour is not active', () => {
      const nextStepMock = vi.fn();
      const inactiveContext: TourContextType = {
        ...mockContextValue,
        isActive: false,
        nextStep: nextStepMock,
      };

      render(
        <TourContext.Provider value={inactiveContext}>
          <TourOverlay />
        </TourContext.Provider>
      );

      fireEvent.keyDown(window, { key: 'ArrowRight' });

      expect(nextStepMock).not.toHaveBeenCalled();
    });
  });

  describe('Spotlight', () => {
    it('renders spotlight around target element', () => {
      const { container } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const spotlight = container.querySelector('[style*="border"]');
      expect(spotlight).toBeInTheDocument();
    });

    it('handles missing selector gracefully', () => {
      const noSelectorStep: TourStep = {
        ...mockTourStep,
        selector: undefined,
      };

      const contextValue: TourContextType = {
        ...mockContextValue,
        currentTourStep: noSelectorStep,
      };

      const { container } = render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      const spotlight = container.querySelector('[style*="border"]');
      expect(spotlight).not.toBeInTheDocument();
    });

    it('handles non-existent target element gracefully', () => {
      const nonExistentStep: TourStep = {
        ...mockTourStep,
        selector: '[data-test="nonexistent"]',
      };

      const contextValue: TourContextType = {
        ...mockContextValue,
        currentTourStep: nonExistentStep,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('centers tooltip when no selector is provided', () => {
      const centerStep: TourStep = {
        ...mockTourStep,
        selector: undefined,
        position: 'center',
      };

      const contextValue: TourContextType = {
        ...mockContextValue,
        currentTourStep: centerStep,
      };

      render(
        <TourContext.Provider value={contextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });
  });

  describe('Tooltip Positioning', () => {
    it('renders tooltip with correct position attributes', () => {
      const { container } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const tooltip = container.querySelector('.bg-white.rounded-lg.shadow-2xl');
      expect(tooltip).toBeInTheDocument();
      expect(tooltip).toHaveStyle({ position: 'absolute' });
    });

    it('renders arrow indicator in tooltip', () => {
      const { container } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const arrow = container.querySelector('.bg-white.transform.rotate-45');
      expect(arrow).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('provides aria labels for buttons', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      expect(screen.getByLabelText('Next step')).toBeInTheDocument();
      expect(screen.getByLabelText('Skip tour')).toBeInTheDocument();
      expect(screen.getByLabelText('Close tour')).toBeInTheDocument();
    });

    it('buttons have correct type attributes', () => {
      render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });
  });

  describe('Event Cleanup', () => {
    it('removes event listeners on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      const { unmount } = render(
        <TourContext.Provider value={mockContextValue}>
          <TourOverlay />
        </TourContext.Provider>
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    });
  });
});
