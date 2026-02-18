'use client';

import { LanguageProvider } from '@/contexts/LanguageContext';
import { ExperimentProvider } from '@/contexts/ExperimentContext';
import ExperimentShell from '@/components/experiment/ExperimentShell';

export default function ExperimentPage() {
  return (
    <LanguageProvider>
      <ExperimentProvider>
        <ExperimentShell />
      </ExperimentProvider>
    </LanguageProvider>
  );
}
