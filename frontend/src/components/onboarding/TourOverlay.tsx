```typescript
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useTour } from '@/hooks/useTour';

interface ElementPosition {
  top: number;
  left: number;
  width: number;
  height: number;
}

interface TooltipPosition {
  top: number;
  left: number;
  arrowPosition: 'top' | 'bottom' | 'left' | 'right';
}

const SPOTLIGHT_PADDING = 8;
const TOOLTIP_OFFSET = 20;
const TOOLTIP_MARGIN = 12;

export function TourOverlay(): React.ReactElement | null {
  const { isActive, currentTourStep, currentStep, totalSteps, nextStep, prevStep, skipTour, completeTour } = useTour();

  const [elementPosition, setElementPosition] = useState<ElementPosition | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<TooltipPosition>({ top: 0, left: 0, arrowPosition: 'bottom' });
  const overlayRef = useRef<HTMLDivElement>(null);

  // Find and track target element position
  useEffect(() => {
    const updatePositions = (): void => {
      if (!currentTourStep.selector) {
        setElementPosition(null);
        return;
      }

      const element = document.querySelector(currentTourStep.selector);
      if (!element) {
        setElementPosition(null);
        return;
      }

      const rect = element.getBoundingClientRect();
      setElementPosition({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height,
      });
    };

    updatePositions();
    window.addEventListener('resize', updatePositions);
    window.addEventListener('scroll', updatePositions);

    return () => {
      window.removeEventListener('resize', updatePositions);
      window.removeEventListener('scroll', updatePositions);
    };
  }, [currentTourStep.selector]);

  // Calculate tooltip position based on target element or center
  useEffect(() => {
    if (!elementPosition) {
      // Center tooltip if no element found
      setTooltipPosition({
        top: window.innerHeight / 2 - 100,
        left: window.innerWidth / 2 - 160,
        arrowPosition: 'bottom',
      });
      return;
    }

    const { top, left, width, height } = elementPosition;
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    let tooltipTop = 0;
    let tooltipLeft = 0;
    let arrowPosition: 'top' | 'bottom' | 'left' | 'right' = 'bottom';

    const tooltipWidth = 320;
    const tooltipHeight = 160;

    switch (currentTourStep.position) {
      case 'bottom':
        tooltipTop = top + height + TOOLTIP_OFFSET;
        tooltipLeft = left + width / 2 - tooltipWidth / 2;
        arrowPosition = 'top';
        break;
      case 'top':
        tooltipTop = top - TOOLTIP_OFFSET - tooltipHeight;
        tooltipLeft = left + width / 2 - tooltipWidth / 2;
        arrowPosition = 'bottom';
        break;
      case 'right':
        tooltipTop = top + height / 2 - tooltipHeight / 2;
        tooltipLeft = left + width + TOOLTIP_OFFSET;
        arrowPosition = 'left';
        break;
      case 'left':
        tooltipTop = top + height / 2 - tooltipHeight / 2;
        tooltipLeft = left - TOOLTIP_OFFSET - tooltipWidth;
        arrowPosition = 'right';
        break;
      case 'center':
        tooltipTop = window.innerHeight / 2 - tooltipHeight / 2;
        tooltipLeft = window.innerWidth / 2 - tooltipWidth / 2;
        arrowPosition = 'bottom';
        break;
    }

    // Clamp to viewport
    tooltipLeft = Math.max(TOOLTIP_MARGIN, Math.min(tooltipLeft, viewportWidth - tooltipWidth - TOOLTIP_MARGIN));
    tooltipTop = Math.max(TOOLTIP_MARGIN, Math.min(tooltipTop, viewportHeight - tooltipHeight - TOOLTIP_MARGIN));

    setTooltipPosition({ top: tooltipTop, left: tooltipLeft, arrowPosition });
  }, [elementPosition, currentTourStep.position]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (!isActive) return;

      switch (e.key) {
        case 'ArrowRight':
        case 'Enter':
          e.preventDefault();
          if (currentStep === totalSteps - 1) {
            completeTour();
          } else {
            nextStep();
          }
          break;
        case 'ArrowLeft':
          e.preventDefault();
          prevStep();
          break;
        case 'Escape':
          e.preventDefault();
          skipTour();
          break;
      }
    };

    if (isActive) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isActive, currentStep, totalSteps, nextStep, prevStep, skipTour, completeTour]);

  if (!isActive) return null;

  return (
    <div ref={overlayRef} className="fixed inset-0 z-[9999] pointer-events-none" style={{ perspective: '1000px' }}>
      {/* Fullscreen overlay backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-60 pointer-events-auto cursor-pointer" onClick={skipTour} />

      {/* Spotlight cutout */}
      {elementPosition && (
        <div
          className="absolute pointer-events-auto"
          style={{
            top: elementPosition.top - SPOTLIGHT_PADDING,
            left: elementPosition.left - SPOTLIGHT_PADDING,
            width: elementPosition.width + SPOTLIGHT_PADDING * 2,
            height: elementPosition.height + SPOTLIGHT_PADDING * 2,
            border: '2px solid #fbbf24',
            borderRadius: '8px',
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.6)',
          }}
        />
      )}

      {/* Tooltip */}
      <div
        className="absolute bg-white rounded-lg shadow-2xl p-6 max-w-sm pointer-events-auto"
        style={{
          top: `${tooltipPosition.top}px`,
          left: `${tooltipPosition.left}px`,
          width: '320px',
        }}
      >
        {/* Arrow indicator */}
        <div
          className="absolute w-3 h-3 bg-white transform rotate-45"
          style={{
            ...(tooltipPosition.arrowPosition === 'top' && { top: '-6px', left: '50%', marginLeft: '-6px' }),
            ...(tooltipPosition.arrowPosition === 'bottom' && { bottom: '-6px', left: '50%', marginLeft: '-6px' }),
            ...(tooltipPosition.arrowPosition === 'left' && { left: '-6px', top: '50%', marginTop: '-6px' }),
            ...(tooltipPosition.arrowPosition === 'right' && { right: '-6px', top: '50%', marginTop: '-6px' }),
          }}
        />

        {/* Close button */}
        <button
          onClick={skipTour}
          className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 text-lg leading-none"
          aria-label="Close tour"
          type="button"
        >
          ×
        </button>

        {/* Content */}
        <h2 className="text-lg font-bold text-gray-900 mb-2 pr-6">{currentTourStep.title}</h2>
        <p className="text-sm text-gray-600 mb-4">{currentTourStep.description}</p>

        {/* Step indicator */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs text-gray-500">
            Step {currentStep + 1} of {totalSteps}
          </span>
          <div className="flex gap-1">
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === currentStep ? 'bg-amber-400' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Navigation buttons */}
        <div className="flex gap-2">
          {currentStep > 0 && (
            <button
              onClick={prevStep}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition"
              aria-label="Previous step"
              type="button"
            >
              Back
            </button>
          )}
          <button
            onClick={skipTour}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition"
            aria-label="Skip tour"
            type="button"
          >
            Skip
          </button>
          {currentStep === totalSteps - 1 ? (
            <button
              onClick={completeTour}
              className="flex-1 px-3 py-2 text-sm font-medium text-white bg-amber-400 rounded hover:bg-amber-500 transition"
              aria-label="Complete tour"
              type="button"
            >
              Done
            </button>
          ) : (
            <button
              onClick={nextStep}
              className="flex-1 px-3 py-2 text-sm font-medium text-white bg-amber-400 rounded hover:bg-amber-500 transition"
              aria-label="Next step"
              type="button"
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```