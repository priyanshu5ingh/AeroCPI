import React, { useEffect, useState } from 'react';
import {
  IndexDashboardResponse,
  IndexExplanationResponse,
  IndexAuditResponse,
  SimpleIndexRun
} from './types';
import {
  fetchDashboard,
  fetchExplanation,
  fetchAudit,
  fetchIndexRuns
} from './services/api';
import { Header, PlatformTab } from './components/Header';
import { GuideView } from './pages/GuideView';
import { MarketView } from './pages/MarketView';
import { ProofView } from './pages/ProofView';
import { OverviewPage } from './pages/OverviewPage';
import { LiveMarketPage } from './pages/LiveMarketPage';
import { RoutesPage } from './pages/RoutesPage';
import { HorizonAnalysisPage } from './pages/HorizonAnalysisPage';
import { MethodologyPage } from './pages/MethodologyPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { ValidationLabPage } from './pages/ValidationLabPage';
import { AuditEvidencePage } from './pages/AuditEvidencePage';
import { RouteExplanationModal } from './components/RouteExplanationModal';
import { AuditModal } from './components/AuditModal';
import { LoadingSkeleton, ErrorView } from './components/StateViews';

const DEFAULT_RUN_ID = 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be';

export default function App() {
  const [currentRunId, setCurrentRunId] = useState<string>(DEFAULT_RUN_ID);
  const [runs, setRuns] = useState<SimpleIndexRun[]>([]);
  const [dashboard, setDashboard] = useState<IndexDashboardResponse | null>(null);
  const [explanation, setExplanation] = useState<IndexExplanationResponse | null>(null);
  const [audit, setAudit] = useState<IndexAuditResponse | null>(null);

  const normalizeTab = (rawTab: string | null): PlatformTab => {
    if (!rawTab) return 'guide';
    if (rawTab === 'overview') return 'overview';
    if (rawTab === 'aeroguide' || rawTab === 'guide') return 'guide';
    if (rawTab === 'market') return 'market';
    if (rawTab === 'proof') return 'proof';
    if (rawTab === 'live-market') return 'live-market';
    if (rawTab === 'routes') return 'routes';
    if (rawTab === 'horizon' || rawTab === 'horizons') return 'horizon';
    if (rawTab === 'methodology') return 'methodology';
    if (rawTab === 'data-quality') return 'data-quality';
    if (rawTab === 'validation') return 'validation';
    if (rawTab === 'audit') return 'audit';
    return rawTab as PlatformTab;
  };

  const [activeTab, setActiveTab] = useState<PlatformTab>(() => {
    if (typeof window === 'undefined') return 'guide';
    const params = new URLSearchParams(window.location.search);
    return normalizeTab(params.get('tab'));
  });

  const handleSelectTab = (tab: PlatformTab) => {
    if (tab === activeTab) return;
    const params = new URLSearchParams(window.location.search);
    params.set('tab', tab);
    window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
    setActiveTab(tab);
  };

  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      setActiveTab(normalizeTab(params.get('tab')));
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [is404, setIs404] = useState<boolean>(false);

  // Interaction Modal States
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState<boolean>(false);

  // Initial load of index runs list
  useEffect(() => {
    fetchIndexRuns()
      .then((data) => setRuns(data))
      .catch((err) => console.warn('Could not fetch index runs list:', err));
  }, []);

  // Fetch full dashboard, 5A explanation, and 5B audit for active runId
  const loadRunData = async (runId: string) => {
    setLoading(true);
    setError(null);
    setIs404(false);

    try {
      const [dashRes, expRes, auditRes] = await Promise.all([
        fetchDashboard(runId),
        fetchExplanation(runId),
        fetchAudit(runId)
      ]);

      setDashboard(dashRes);
      setExplanation(expRes);
      setAudit(auditRes);
    } catch (err: any) {
      console.error('Failed to fetch AeroCPI dashboard data:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message || 'Error loading dashboard.';
      if (status === 404) {
        setIs404(true);
      }
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRunData(currentRunId);
  }, [currentRunId]);

  const handleSelectRun = (runId: string) => {
    setCurrentRunId(runId);
  };

  if (loading && !dashboard) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <ErrorView
          message={error}
          is404={is404}
          onRetry={() => loadRunData(currentRunId)}
        />
      </div>
    );
  }

  if (!dashboard) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-blue-600 selection:text-white font-sans">
      <div>
        {/* Zone 1: Header */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-lg font-bold"
        >
          Skip to main content
        </a>
        <Header
          scope={dashboard.dashboard_scope}
          runs={runs}
          onSelectRun={handleSelectRun}
          activeTab={activeTab}
          onSelectTab={handleSelectTab}
          trustStatus={dashboard.trust.trust_status}
          onOpenTrace={() => handleSelectTab('proof')}
        />

        {/* Main Experience Canvas */}
        <main id="main-content" className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          {/* MODE 1: GUIDE (Default Landing: Should I book this flight?) */}
          {activeTab === 'guide' && (
            <GuideView
              onNavigateToMarket={() => handleSelectTab('market')}
              onNavigateToProof={() => handleSelectTab('proof')}
            />
          )}

          {/* MODE 2: MARKET (What is happening in India's airfare market?) */}
          {activeTab === 'market' && (
            <MarketView
              dashboard={dashboard}
              explanation={explanation}
              onSelectRoute={setSelectedRouteId}
            />
          )}

          {/* MODE 3: PROOF (Why should I trust this result?) */}
          {activeTab === 'proof' && (
            <ProofView
              dashboard={dashboard}
              audit={audit}
              onOpenAuditModal={() => setIsAuditModalOpen(true)}
              onNavigateToMethodology={() => handleSelectTab('methodology')}
              onNavigateToValidation={() => handleSelectTab('validation')}
            />
          )}

          {/* Secondary Legacy Pages for Deep Analysis and Tests */}
          {activeTab === 'overview' && (
            <OverviewPage
              dashboard={dashboard}
              onSelectRoute={setSelectedRouteId}
              onOpenAuditModal={() => setIsAuditModalOpen(true)}
            />
          )}

          {activeTab === 'live-market' && (
            <LiveMarketPage
              dashboard={dashboard}
              onSelectRoute={setSelectedRouteId}
            />
          )}

          {activeTab === 'routes' && (
            <RoutesPage
              dashboard={dashboard}
              explanation={explanation}
              onSelectRoute={setSelectedRouteId}
              onNavigateToExplorer={() => handleSelectTab('live-market')}
            />
          )}

          {activeTab === 'horizon' && (
            <HorizonAnalysisPage
              dashboard={dashboard}
              onNavigateToExplorer={() => handleSelectTab('live-market')}
              onSelectRoute={(routeId) => {
                setSelectedRouteId(routeId);
                handleSelectTab('routes');
              }}
            />
          )}

          {activeTab === 'methodology' && (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8">
              <MethodologyPage dashboard={dashboard} audit={audit} />
            </div>
          )}

          {activeTab === 'data-quality' && (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8">
              <DataQualityPage
                dashboard={dashboard}
                audit={audit}
                onNavigateToExplorer={() => handleSelectTab('live-market')}
              />
            </div>
          )}

          {activeTab === 'validation' && (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8">
              <ValidationLabPage
                dashboard={dashboard}
                audit={audit}
                onSelectTab={handleSelectTab}
                onOpenAuditModal={() => setIsAuditModalOpen(true)}
              />
            </div>
          )}

          {activeTab === 'audit' && audit && explanation && (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8">
              <AuditEvidencePage
                dashboard={dashboard}
                audit={audit}
                explanation={explanation}
                onOpenAuditModal={() => setIsAuditModalOpen(true)}
                onSelectTab={handleSelectTab}
              />
            </div>
          )}
        </main>
      </div>

      {/* Level 2 Route Explanation Modal (5A) */}
      <RouteExplanationModal
        routeId={selectedRouteId}
        explanation={explanation}
        onClose={() => setSelectedRouteId(null)}
      />

      {/* Level 3 Measurement Audit Modal (5B) */}
      <AuditModal
        isOpen={isAuditModalOpen}
        audit={audit}
        onClose={() => setIsAuditModalOpen(false)}
      />
    </div>
  );
}
