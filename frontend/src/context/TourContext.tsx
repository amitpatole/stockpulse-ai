```typescript
'use client';

import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { TOUR_STEPS, TourStep } from '@/components/onboarding/tourSteps';

export interface TourState {
  completed: boolean;
  completedAt?: string;
  skipped: boolean;
}

export interface TourContextType {
  isActive: boolean;
  currentStep: number;
  currentTourStep: TourStep;
  totalSteps: number;
  completed: boolean;
  skipped: boolean;
  nextStep: () => void;
  prevStep: () => void;
  skipTour: () => void;
  completeTour: () => void;
  startTour: () => void;
  goToStep: (step: number) => void;
}

export const TourContext = createContext<TourContextType | undefined>(undefined);

const STORAGE_KEY = 'tickerpulse_tour_state';

function loadTourState(): TourState {
  if (typeof window === 'undefined') {
    return { completed: false, skipped: false };
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.warn('Failed to load tour state from localStorage:', error);
  }
  return { completed: false, skipped: false };
}

function saveTourState(state: TourState): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.warn('Failed to save tour state to localStorage:', error);
  }
}

interface TourProviderProps {
  children: ReactNode;
}

export function TourProvider({ children }: TourProviderProps) {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [tourState, setTourState] = useState<TourState>({ completed: false, skipped: false });
  const [mounted, setMounted] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    const state = loadTourState();
    setTourState(state);
    if (!state.completed && !state.skipped) {
      setCurrentStep(0);
    }
    setMounted(true);
  }, []);

  const isActive = !tourState.completed && !tourState.skipped && mounted;
  const currentTourStep = TOUR_STEPS[currentStep] || TOUR_STEPS[0];
  const totalSteps = TOUR_STEPS.length;

  const nextStep = (): void => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      completeTour();
    }
  };

  const prevStep = (): void => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const skipTour = (): void => {
    const newState: TourState = {
      completed: true,
      completedAt: new Date().toISOString(),
      skipped: true,
    };
    setTourState(newState);
    saveTourState(newState);
  };

  const completeTour = (): void => {
    const newState: TourState = {
      completed: true,
      completedAt: new Date().toISOString(),
      skipped: false,
    };
    setTourState(newState);
    saveTourState(newState);
  };

  const startTour = (): void => {
    setCurrentStep(0);
    setTourState({ completed: false, skipped: false });
    saveTourState({ completed: false, skipped: false });
  };

  const goToStep = (step: number): void => {
    if (step >= 0 && step < totalSteps) {
      setCurrentStep(step);
    }
  };

  const value: TourContextType = {
    isActive,
    currentStep,
    currentTourStep,
    totalSteps,
    completed: tourState.completed,
    skipped: tourState.skipped,
    nextStep,
    prevStep,
    skipTour,
    completeTour,
    startTour,
    goToStep,
  };

  return <TourContext.Provider value={value}>{children}</TourContext.Provider>;
}
```