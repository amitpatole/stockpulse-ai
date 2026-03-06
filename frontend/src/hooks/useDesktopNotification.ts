```typescript
import { useCallback } from 'react';

export interface NotificationOptions {
  title: string;
  body?: string;
  icon?: string;
  badge?: string;
  tag?: string;
  requireInteraction?: boolean;
}

export function useDesktopNotification() {
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!('Notification' in window)) {
      console.warn('Desktop notifications not supported');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission !== 'denied') {
      try {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
      } catch (error) {
        console.error('Failed to request notification permission:', error);
        return false;
      }
    }

    return false;
  }, []);

  const sendNotification = useCallback(
    async (options: NotificationOptions): Promise<void> => {
      if (!('Notification' in window)) {
        return;
      }

      if (Notification.permission !== 'granted') {
        const granted = await requestPermission();
        if (!granted) return;
      }

      try {
        const notification = new Notification(options.title, {
          body: options.body,
          icon: options.icon || '/icon-192x192.png',
          badge: options.badge || '/icon-96x96.png',
          tag: options.tag || 'price-alert',
          requireInteraction: options.requireInteraction ?? false,
        });

        // Auto-close after 5 seconds if requireInteraction is false
        if (!options.requireInteraction) {
          setTimeout(() => notification.close(), 5000);
        }

        // Play sound
        playNotificationSound();
      } catch (error) {
        console.error('Failed to send notification:', error);
      }
    },
    [requestPermission],
  );

  return { sendNotification, requestPermission };
}

function playNotificationSound() {
  try {
    // Create a simple beep sound
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    // Notification API typically handles sound, this is a fallback
  }
}
```