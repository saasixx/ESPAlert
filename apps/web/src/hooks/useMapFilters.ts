import { useState, useCallback } from 'react';
import type { EventCategory } from '@/types/events';

/**
 * Hook para gestionar los filtros de categorías del mapa.
 * Controla qué tipos de alerta son visibles.
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

  /** Determina la categoría a partir del tipo de evento de la API. */
  const getCategoryFromType = useCallback((eventType: string): EventCategory => {
    if (eventType.startsWith('traffic')) return 'traffic';
    if (eventType === 'earthquake' || eventType === 'tsunami') return 'seismic';
    if (['coastal', 'wave', 'tide'].includes(eventType)) return 'maritime';
    return 'meteo';
  }, []);

  return { activeCategories, toggleCategory, getCategoryFromType };
}