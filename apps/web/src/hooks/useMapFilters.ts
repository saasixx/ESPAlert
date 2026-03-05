import { useState, useCallback } from 'react';
import type { EventCategory } from '@/types/events';

/**
 * Hook for managing map category filters.
 * Controls which alert types are visible.
 */
export function useMapFilters() {
  const [activeCategories, setActiveCategories] = useState<Set<EventCategory>>(
    new Set(['meteo', 'seismic', 'traffic', 'maritime'])
  );

  const toggleCategory = useCallback((category: EventCategory) => {
    setActiveCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }, []);

  /** Determines the category from the API event type. */
  const getCategoryFromType = useCallback((eventType: string): EventCategory => {
    if (eventType.startsWith('traffic')) return 'traffic';
    if (eventType === 'earthquake' || eventType === 'tsunami') return 'seismic';
    if (['coastal', 'wave', 'tide'].includes(eventType)) return 'maritime';
    return 'meteo';
  }, []);

  return { activeCategories, toggleCategory, getCategoryFromType };
}