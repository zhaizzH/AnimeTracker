import { useEffect } from 'react';
import { bootstrapAuth } from '../auth/coordinator';

export function useBootstrapAuth() {
  useEffect(() => { void bootstrapAuth(); }, []);
}