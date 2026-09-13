import React, { useState } from 'react';
import { IndexDashboardResponse } from '../types';
import { HeroCard } from '../components/HeroCard';
import { SpatialRouteNetwork } from '../components/SpatialRouteNetwork';
import { DriverSection } from '../components/DriverSection';
import { CoveragePanel } from '../components/CoveragePanel';
import { TrustPanel } from '../components/TrustPanel';
import { AuditPanel } from '../components/AuditPanel';
import { MethodologyFooter } from '../components/MethodologyFooter';
import { TraceMeasurementModal } from '../components/TraceMeasurementModal';

interface OverviewPageProps {
  dashboard: IndexDashboardResponse;
  onSelectRoute: (routeId: string) => void;
  onOpenAuditModal: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  dashboard,
  onSelectRoute,
  onOpenAuditModal,
}) => {
  const [isTraceModalOpen, setIsTraceModalOpen] = useState(false);

  return (
    <div className="space-y-8">
      {/* Zone 1: Airfare Movement Hero Metric */}
      <HeroCard
        headline={dashboard.headline}
        drivers={dashboard.drivers}
        onTraceMeasurement={() => setIsTraceModalOpen(true)}
      />

      {/* Zone 2: Sovereign Route Basket Spatial Network + Attributions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <SpatialRouteNetwork
            drivers={dashboard.drivers}
            onSelectRoute={onSelectRoute}
          />
        </div>
        <div className="lg:col-span-5 flex flex-col">
          <DriverSection
            drivers={dashboard.drivers}
            onSelectRoute={onSelectRoute}
          />
        </div>
      </div>

      {/* Zone 3: Forward Booking Horizon Curve */}
      <CoveragePanel coverage={dashboard.coverage} />

      {/* Zone 4: Measurement Trust & Audit Evidence Strip */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TrustPanel trust={dashboard.trust} />
        <AuditPanel
          audit={dashboard.audit}
          onOpenAudit={onOpenAuditModal}
        />
      </section>

      {/* Zone 5: Methodology Provenance & Statutory Notice */}
      <MethodologyFooter methodology={dashboard.methodology} />

      {/* Flagship Trace Measurement Lineage Modal */}
      <TraceMeasurementModal
        isOpen={isTraceModalOpen}
        dashboard={dashboard}
        onClose={() => setIsTraceModalOpen(false)}
      />
    </div>
  );
};
