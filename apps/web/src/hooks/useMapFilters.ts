import { useState, useCallback } from 'react';
import type { EventCategory } from '@/types/events';

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

  const getCategoryFromType = (eventType: string): EventCategory => {
    if (eventType.startsWith('traffic')) return 'traffic';
    if (eventType === 'earthquake' || eventType === 'tsunami') return 'seismic';
    if (['coastal', 'wave', 'tide'].includes(eventType)) return 'maritime';
    return 'meteo';
  };

  return { activeCategories, toggleCategory, getCategoryFromType };
}