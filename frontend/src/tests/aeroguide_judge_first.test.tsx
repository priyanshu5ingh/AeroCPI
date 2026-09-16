import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { GuideView } from '../pages/GuideView';
import { MarketView } from '../pages/MarketView';
import { ProofView } from '../pages/ProofView';
import { DecisionTraceDrawer } from '../components/DecisionTraceDrawer';
import * as apiModule from '../services/api';
import {
  IndexDashboardResponse,
  IndexExplanationResponse,
  IndexAuditResponse,
  AeroGuideAnalyzeResponse,
  ForecastingReadinessResponse
} from '../types';

const mockAnalyzeResponse: AeroGuideAnalyzeResponse = {
  request_id: 'REQ-BLR-DEL-20261018-001',
  origin: 'BLR',
  destination: 'DEL',
  route_id: 'BLR-DEL',
  travel_date: '2026-10-18',
  days_to_departure: 15,
  current_observed_fare: 6425.0,
  currency: 'INR',
  price_position: 'TYPICAL',
  route_historical_median: 6980.0,
  route_historical_min: 5200.0,
  route_historical_max: 9800.0,
  observations_in_sample: 184,
  model_outlook_status: 'INSUFFICIENT_LONGITUDINAL_HISTORY',
  model_probabilities: null,
  model_outlook_message: 'Longitudinal panel accumulating daily observations.',
  booking_guidance: 'WAIT',
  guidance_reason: 'Fare is currently above observed route median with sufficient lead time.',
  decision_policy_version: 'DECISION_POLICY_V1',
  airline_alternatives: [
    {
      carrier_code: '6E',
      airline_name: 'IndiGo',
      observed_fare: 6425.0,
      currency: 'INR',
      stops: 0,
      duration_minutes: 165,
      source_id: 'SRC_GOOGLE_FLIGHTS',
      source_evidence: 'Google Flights Live Quote',
      source_state: 'OBSERVED',
      is_direct_airline: false,
      current_position: 'LOW'
    },
    {
      carrier_code: 'AI',
      airline_name: 'Air India',
      observed_fare: 6710.0,
      currency: 'INR',
      stops: 0,
      duration_minutes: 170,
      source_id: 'SRC_GOOGLE_FLIGHTS',
      source_evidence: 'Google Flights Live Quote',
      source_state: 'OBSERVED',
      is_direct_airline: false,
      current_position: 'TYPICAL'
    }
  ],
  flexible_dates: [
    {
      travel_date: '2026-10-16',
      days_diff: -2,
      observed_fare: 5890.0,
      difference_from_requested: -535.0,
      percent_difference: -8.3,
      carrier_code: '6E',
      stops: 0,
      source_evidence: 'Observed Quote',
      is_lower_fare: true,
      label: '-2 Days'
    },
    {
      travel_date: '2026-10-18',
      days_diff: 0,
      observed_fare: 6425.0,
      difference_from_requested: 0.0,
      percent_difference: 0.0,
      carrier_code: '6E',
      stops: 0,
      source_evidence: 'Selected Baseline',
      is_lower_fare: false,
      label: 'Selected Date'
    }
  ],
  sources_available: ['SRC_GOOGLE_FLIGHTS', 'SRC_DUFFEL'],
  decision_trace: [
    {
      stage_number: 1,
      stage_name: 'Search Request & Context',
      status: 'VERIFIED',
      evidence_summary: 'Requested flight query BLR to DEL on 2026-10-18.',
      structured_payload: { origin: 'BLR', destination: 'DEL', travel_date: '2026-10-18' }
    },
    {
      stage_number: 2,
      stage_name: 'Current Market Observations',
      status: 'COLLECTED',
      evidence_summary: 'Observed lowest fare of ₹6,425 across live search captures.',
      structured_payload: { lowest_fare: 6425.0 }
    },
    {
      stage_number: 3,
      stage_name: 'Source Agreement & Health',
      status: 'VERIFIED',
      evidence_summary: 'Multi-source telemetry evaluated across active adapters.',
      structured_payload: { primary_source: 'SRC_GOOGLE_FLIGHTS' }
    },
    {
      stage_number: 4,
      stage_name: 'Historical Price Position',
      status: 'EVALUATED',
      evidence_summary: 'Corridor median is ₹6,980 with P50 alignment.',
      structured_payload: { median: 6980.0, percentile: 50.0 }
    },
    {
      stage_number: 5,
      stage_name: 'Advance Purchase Position',
      status: 'EVALUATED',
      evidence_summary: 'T+15 days to departure indicates non-urgent purchase window.',
      structured_payload: { days_to_departure: 15 }
    },
    {
      stage_number: 6,
      stage_name: 'Multi-Carrier Intelligence',
      status: 'COLLECTED',
      evidence_summary: 'Quotes observed across 2 carriers with full provenance.',
      structured_payload: { carriers_count: 2 }
    },
    {
      stage_number: 7,
      stage_name: 'Smart Flexible Dates',
      status: 'EVALUATED',
      evidence_summary: 'Observed lower fare of ₹5,890 available on 2026-10-16.',
      structured_payload: { best_flex_fare: 5890.0 }
    },
    {
      stage_number: 8,
      stage_name: 'National Market State',
      status: 'VERIFIED',
      evidence_summary: 'AeroCPI National T+15 index is at 96.21 (FALLING).',
      structured_payload: { national_index: 96.21 }
    },
    {
      stage_number: 9,
      stage_name: 'AI Price Outlook',
      status: 'GATED_EVIDENCE_LIMITED',
      evidence_summary: 'Model training locked awaiting longitudinal target pairs.',
      structured_payload: { model_status: 'INSUFFICIENT_DATA' }
    },
    {
      stage_number: 10,
      stage_name: 'Decision Policy Engine (V1)',
      status: 'DECIDED',
      evidence_summary: 'Deterministic policy rule triggered WAIT guidance.',
      structured_payload: { policy: 'DECISION_POLICY_V1' }
    },
    {
      stage_number: 11,
      stage_name: 'Final Grounded Guidance',
      status: 'VERIFIED',
      evidence_summary: 'Verdict: WAIT. Factual summary generated without hallucination.',
      structured_payload: { verdict: 'WAIT' }
    }
  ],
  grounded_explanation: "Today's lowest observed fare for BLR ➔ DEL is ₹6,425, positioning near median ₹6,980. Decision engine [DECISION_POLICY_V1] recommends WAIT as advance purchase window allows price tracking.",
  longitudinal_readiness: {
    dataset_classification: 'INSUFFICIENT_LONGITUDINAL_HISTORY',
    model_training_status: 'DISABLED',
    required_target_pairs: 7,
    current_target_pairs: 0
  }
};

const mockDashboardData: IndexDashboardResponse = {
  dashboard_scope: {
    run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
    reference_date: '2026-09-10',
    calculation_date: '2026-09-12',
    cabin: 'ECONOMY',
    dashboard_timestamp: '2026-09-12T05:31:08.404165Z'
  },
  headline: {
    horizon_code: 'T+15',
    index_name: 'AeroCPI_T15',
    index_value: 96.209,
    reference_date: '2026-09-10',
    calculation_date: '2026-09-12',
    change_from_base: -3.791,
    direction: 'DOWN',
    is_headline: true
  },
  drivers: {
    top_positive_drivers: [
      {
        route_id: 'DEL-HYD',
        origin: 'DEL',
        destination: 'HYD',
        base_representative_fare: 8825.0,
        current_representative_fare: 9807.0,
        route_index_value: 111.127,
        point_contribution: 1.0675,
        direction: 'POSITIVE',
        active_weight: 0.103153
      }
    ],
    top_negative_drivers: [
      {
        route_id: 'GOI-BOM',
        origin: 'GOI',
        destination: 'BOM',
        base_representative_fare: 9539.0,
        current_representative_fare: 5230.0,
        route_index_value: 54.828,
        point_contribution: -4.7391,
        direction: 'NEGATIVE',
        active_weight: 0.08039
      }
    ]
  },
  coverage: {
    headline_horizon_code: 'T+15',
    headline_coverage_ratio: 1.0,
    horizon_coverage: [
      {
        horizon_code: 'T+15',
        index_value: 96.209,
        base_coverage_ratio: 1.0,
        current_coverage_ratio: 1.0,
        matched_coverage_ratio: 1.0,
        active_routes_count: 10,
        total_basket_routes_count: 10,
        active_weight_sum: 1.0
      }
    ]
  },
  trust: {
    trust_score: 95.0,
    trust_status: 'HIGH_CONFIDENCE',
    reason_codes: [],
    is_diagnostic_only: true,
    trust_evaluation_status: 'EVALUATED'
  },
  methodology: {
    methodology_version: 'AeroCPI_V1',
    basket_version: 'DGCA-10-2026.1',
    proxy_weight_version: 'DGCA-TRAFFIC-2025',
    software_version: '2026.1.0',
    reference_date: '2026-09-10',
    calculation_date: '2026-09-12',
    cabin: 'ECONOMY',
    headline_horizon: 'T+15',
    disclaimer: 'AeroCPI is an independent index.'
  },
  audit: {
    canonical_run_fingerprint: 'eac9d1876c3aa2989dbdd4720777e51ae3ed386d00315f9d4bd0e813f826fa72',
    manifest_sha256: 'sha256_mock_manifest',
    manifest_present: true,
    raw_input_artifacts_available: true,
    reproducibility_status: 'ARTIFACT_REPRODUCIBLE',
    limitations: []
  },
  disclaimer: 'AeroCPI is independent.'
};

describe('AeroGuide Judge-First UX Test Suite', () => {
  beforeEach(() => {
    vi.spyOn(apiModule, 'analyzeAirfare').mockResolvedValue(mockAnalyzeResponse);
    vi.spyOn(apiModule, 'fetchAirlines').mockResolvedValue([]);
    vi.spyOn(apiModule, 'fetchSourceCapabilities').mockResolvedValue([
      {
        source_id: 'SRC_GOOGLE_FLIGHTS',
        source_name: 'Google Flights',
        source_type: 'SEARCH_AGGREGATOR',
        access_status: 'OBSERVED',
        is_public_unrestricted: true,
        fare_breakdown_supported: false,
        health_status: 'HEALTHY',
        availability_rate: 1.0,
        median_response_time_ms: 120
      }
    ]);
    vi.spyOn(apiModule, 'fetchForecastingReadiness').mockResolvedValue({
      dataset_classification: 'INSUFFICIENT_LONGITUDINAL_HISTORY',
      model_training_status: 'DISABLED',
      total_observations: 17244,
      unique_routes: 15,
      unique_travel_dates: 38,
      unique_search_dates: 7,
      longitudinal_pairs_count: 140,
      repeated_trajectories: 1,
      trajectories_with_gte_3_searches: 0,
      seven_day_target_pairs: 0,
      fourteen_day_target_pairs: 0,
      longest_history_days: 0,
      source_coverage: ['SRC_DUFFEL', 'SRC_GOOGLE_FLIGHTS'],
      airline_coverage: ['6E', 'AI', 'QP', 'SG'],
      overall_readiness: 'INSUFFICIENT_LONGITUDINAL_HISTORY',
      readiness_notes: 'Longitudinal panel collecting daily searches.',
      required_collection_schedule: {
        pinned_travel_dates: 14,
        routes_per_run: 10,
        consecutive_collection_days_required: 14,
        target_observations_required: 35000
      }
    });
    vi.spyOn(apiModule, 'fetchRouteCoverage').mockResolvedValue([
      {
        route_id: 'DEL-BOM',
        origin: 'DEL',
        destination: 'BOM',
        tier: 'TIER_1_DGCA_CORE',
        description: 'Top 10 DGCA Sovereign Basket Corridor',
        is_cpi_basket_member: true,
        airlines_observed: ['6E', 'AI', 'QP', 'SG'],
        sources_configured: ['SRC_GOOGLE_FLIGHTS', 'SRC_DUFFEL'],
        sources_accessible: ['SRC_GOOGLE_FLIGHTS'],
        sources_collected: ['SRC_GOOGLE_FLIGHTS', 'SRC_DUFFEL'],
        observations_count: 3992,
        last_collection: '2026-09-16T16:46:54.812851',
        coverage_status: 'ACTIVE_OBSERVED'
      }
    ]);
    vi.spyOn(apiModule, 'fetchTrajectoryDetail').mockResolvedValue({
      route_id: 'BLR-DEL',
      origin: 'BLR',
      destination: 'DEL',
      travel_date: '2026-10-18',
      search_dates_count: 7,
      observations_count: 184,
      search_points: [],
      target_evaluations: [],
      has_7_day_pair: false,
      status: 'COLLECTING'
    });
    vi.spyOn(apiModule, 'fetchWhatChanged').mockResolvedValue({
      national_state: {
        market_state: 'FALLING',
        headline_index: 96.21,
        point_change: -3.79
      },
      top_positive_drivers: [],
      top_negative_drivers: [],
      all_routes: []
    });
    vi.spyOn(apiModule, 'fetchMarketState').mockResolvedValue({
      market_state: 'FALLING',
      headline_index: 96.21,
      point_change: -3.79,
      percentage_change: -3.79,
      horizon_code: 'T+15',
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      summary: 'Domestic airfares are softer/below baseline.',
      trust_status: 'HIGH_CONFIDENCE'
    });
  });

  it('1. Renders GuideView with Hero Question and dominant Decision Card', async () => {
    render(<GuideView />);
    await waitFor(() => {
      expect(screen.getByText(/Should you book this flight\?/i)).toBeInTheDocument();
      expect(screen.getAllByText(/6,?425/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/WAIT/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/COLLECTING LONGITUDINAL EVIDENCE/i)).toBeInTheDocument();
      expect(screen.getByText(/WHY THIS DECISION/i)).toBeInTheDocument();
    });
  });

  it('2. Enforces INSUFFICIENT_DATA state with zero fake probability values when model is collecting', async () => {
    render(<GuideView />);
    await waitFor(() => {
      expect(screen.getAllByText(/AI OUTLOOK/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/0 \/ 7 valid 7-day targets/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Forecast unavailable/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/INSUFFICIENT_DATA/i).length).toBeGreaterThan(0);
      // Ensure no synthetic % bars are rendered
      expect(screen.queryByText(/↓ FALL 50%/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/↑ RISE 50%/i)).not.toBeInTheDocument();
    });
  });

  it('3. Opens and closes 11-node Decision Trace Drawer cleanly', async () => {
    render(<GuideView />);
    await waitFor(() => {
      expect(screen.getByText(/WHY THIS DECISION/i)).toBeInTheDocument();
    });

    // Open trace drawer
    fireEvent.click(screen.getByText(/WHY THIS DECISION/i));

    await waitFor(() => {
      expect(screen.getByText(/11-Node Decision Trace/i)).toBeInTheDocument();
      expect(screen.getByText(/Deterministic Computation Vector/i)).toBeInTheDocument();
      expect(screen.getByText(/Trace Stages/i)).toBeInTheDocument();
    });

    // Close trace drawer
    const doneBtn = screen.getByText('Done Inspecting');
    fireEvent.click(doneBtn);

    await waitFor(() => {
      expect(screen.queryByText(/Deterministic Computation Vector/i)).not.toBeInTheDocument();
    });
  });

  it('4. Toggles Multi-Carrier Pricing Breakdown on demand without visual dilution', async () => {
    render(<GuideView />);
    await waitFor(() => {
      expect(screen.getByText(/Multi-Carrier Airfare Distribution/i)).toBeInTheDocument();
      expect(screen.getByText(/View 2 Carrier Quotes/i)).toBeInTheDocument();
    });

    // Initially collapsed
    expect(screen.queryByText(/IndiGo/i)).not.toBeInTheDocument();

    // Toggle expand
    fireEvent.click(screen.getByText(/View 2 Carrier Quotes/i));

    await waitFor(() => {
      expect(screen.getByText(/IndiGo/i)).toBeInTheDocument();
      expect(screen.getByText(/Air India/i)).toBeInTheDocument();
      expect(screen.getByText(/Collapse Carriers/i)).toBeInTheDocument();
    });
  });

  it('5. Renders MarketView with National Index, 6-state badge, and 5A Attribution Drivers', async () => {
    render(
      <MarketView
        dashboard={mockDashboardData}
        explanation={null}
      />
    );
    await waitFor(() => {
      expect(screen.getByText(/India Airfare Market/i)).toBeInTheDocument();
      expect(screen.getAllByText('96.21').length).toBeGreaterThan(0);
      expect(screen.getAllByText(/FALLING/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/GOI.*BOM/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/DEL.*HYD/i).length).toBeGreaterThan(0);
    });
  });

  it('6. Renders ProofView with 4-step credibility narrative and 5-stage source lifecycle machine', async () => {
    render(
      <ProofView
        dashboard={mockDashboardData}
        audit={null}
      />
    );
    await waitFor(() => {
      expect(screen.getByText(/Measurement Proof & Audit/i)).toBeInTheDocument();
      expect(screen.getAllByText(/DATA/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/MEASUREMENT/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/PROVENANCE/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/AUDIT/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Multi-Source Lifecycle State Machine/i)).toBeInTheDocument();
      expect(screen.getByText(/01 DOCUMENTED/i)).toBeInTheDocument();
      expect(screen.getByText(/05 OBSERVED/i)).toBeInTheDocument();
    });
  });
});
