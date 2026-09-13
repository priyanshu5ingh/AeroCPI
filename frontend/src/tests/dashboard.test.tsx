import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import App from '../App';
import { RouteExplanationModal } from '../components/RouteExplanationModal';
import { AuditModal } from '../components/AuditModal';
import * as apiModule from '../services/api';
import { IndexDashboardResponse, IndexExplanationResponse, IndexAuditResponse } from '../types';

// Mock API Data matching real production run e1c05338-bc7a-4e2f-8b81-f855ca54c3be
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
      { horizon_code: 'T+1', index_value: 63.496, base_coverage_ratio: 1.0, current_coverage_ratio: 1.0, matched_coverage_ratio: 1.0, active_routes_count: 10, total_basket_routes_count: 10, active_weight_sum: 1.0 },
      { horizon_code: 'T+7', index_value: 99.863, base_coverage_ratio: 1.0, current_coverage_ratio: 1.0, matched_coverage_ratio: 1.0, active_routes_count: 10, total_basket_routes_count: 10, active_weight_sum: 1.0 },
      { horizon_code: 'T+15', index_value: 96.209, base_coverage_ratio: 1.0, current_coverage_ratio: 1.0, matched_coverage_ratio: 1.0, active_routes_count: 10, total_basket_routes_count: 10, active_weight_sum: 1.0 },
      { horizon_code: 'T+30', index_value: 90.6, base_coverage_ratio: 1.0, current_coverage_ratio: 1.0, matched_coverage_ratio: 1.0, active_routes_count: 10, total_basket_routes_count: 10, active_weight_sum: 1.0 },
      { horizon_code: 'T+45', index_value: 88.949, base_coverage_ratio: 1.0, current_coverage_ratio: 1.0, matched_coverage_ratio: 1.0, active_routes_count: 10, total_basket_routes_count: 10, active_weight_sum: 1.0 }
    ]
  },
  trust: {
    trust_score: null,
    trust_status: 'UNEVALUATED',
    reason_codes: [],
    is_diagnostic_only: true,
    trust_evaluation_status: 'UNEVALUATED'
  },
  methodology: {
    methodology_version: 'AEROCPI_STATISTICAL_INDEX_V1',
    basket_version: 'BASKET-DGCA-2025-TOP10',
    proxy_weight_version: 'DGCA_BASKET_2025_TOP10',
    software_version: '0.4.0-milestone4d',
    reference_date: '2026-09-10',
    calculation_date: '2026-09-12',
    cabin: 'ECONOMY',
    headline_horizon: 'T+15',
    disclaimer: 'AeroCPI is an independent real-time airfare price index designed to augment CPI and is not statistically equivalent to CPI.'
  },
  audit: {
    canonical_run_fingerprint: 'cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca',
    manifest_sha256: 'cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca',
    manifest_present: true,
    raw_input_artifacts_available: false,
    reproducibility_status: 'ARTIFACT_REPRODUCIBLE',
    limitations: ['LIM1', 'LIM2', 'LIM3']
  },
  disclaimer: 'AeroCPI is an independent real-time airfare price index designed to augment CPI and is not statistically equivalent to CPI.'
};

const mockExplanationData: IndexExplanationResponse = {
  explanation_scope: { run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be', reference_date: '2026-09-10', calculation_date: '2026-09-12', cabin: 'ECONOMY', basket_version: 'BASKET-DGCA-2025-TOP10' },
  index_run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
  headline_horizon_code: 'T+15',
  headline_index_value: 96.209,
  reference_date: '2026-09-10',
  calculation_date: '2026-09-12',
  methodology_version: 'AEROCPI_STATISTICAL_INDEX_V1',
  route_basket_version: 'BASKET-DGCA-2025-TOP10',
  proxy_weight_version: 'DGCA_BASKET_2025_TOP10',
  software_version: '0.4.0-milestone4d',
  canonical_run_fingerprint: 'cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca',
  horizons: [
    {
      horizon_code: 'T+15',
      horizon_days: 15,
      collection_date: '2026-09-12',
      index_name: 'AeroCPI_T15',
      index_value: 96.209,
      matched_sample_index_value: 96.209,
      is_headline: true,
      active_routes_count: 10,
      base_routes_count: 10,
      total_basket_routes_count: 10,
      base_coverage_ratio: 1.0,
      current_coverage_ratio: 1.0,
      matched_coverage_ratio: 1.0,
      active_weight_sum: 1.0,
      reason_codes: [],
      route_contributions: [
        {
          route_id: 'DEL-HYD',
          horizon_code: 'T+15',
          collection_date: '2026-09-12',
          origin_code: 'DEL',
          destination_code: 'HYD',
          base_representative_fare: 8825.0,
          current_representative_fare: 9807.0,
          price_relative: 1.11127,
          route_index_value: 111.127,
          dgca_basket_weight: 0.103153,
          active_weight: 0.103153,
          log_contribution: 0.01088,
          point_contribution: 1.0675,
          direction: 'POSITIVE'
        }
      ],
      missing_routes: []
    }
  ],
  trust_summary: { trust_evaluation_id: null, trust_score: null, trust_status: 'UNEVALUATED', reason_codes: [], is_diagnostic_only: true },
  calculation_manifest: {}
};

const mockAuditData: IndexAuditResponse = {
  audit_scope: { run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be', reference_date: '2026-09-10', calculation_date: '2026-09-12', cabin: 'ECONOMY', basket_version: 'BASKET-DGCA-2025-TOP10', audit_timestamp: '2026-09-12T05:31:08Z' },
  run_identity: { run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be', run_timestamp: '2026-09-12', reference_period: '2026-09-10', comparison_period: '2026-09-12', index_method: 'JEVONS', frequency: 'DAILY', headline_index_value: 96.209, headline_horizon_code: 'T+15' },
  versions: { methodology_version: 'AEROCPI_STATISTICAL_INDEX_V1', route_basket_version: 'BASKET-DGCA-2025-TOP10', proxy_weight_version: 'DGCA_BASKET_2025_TOP10', software_version: '0.4.0-milestone4d', quality_rule_version: '1.0', normalization_version: '1.0' },
  population_audit: { total_observations_queried: 7924, total_eligible_observations: 7924, total_excluded_observations: 0, rejection_breakdown: {}, reference_date_count: 2664, calculation_date_count: 2668, provenance_status: 'DERIVED_FROM_PERSISTED_RUN_ARTIFACT' },
  route_audit: { total_basket_routes: 10, expected_route_horizon_pairs: 50, calculated_route_horizon_pairs: 50, unavailable_route_horizon_pairs: 0, horizon_route_counts: [] },
  coverage_audit: { headline_coverage_ratio: 1.0, horizon_coverage: [], temporal_coverage_status: 'NOT_APPLICABLE' },
  trust_audit: { trust_evaluation_id: null, trust_score: null, trust_status: 'UNEVALUATED', reason_codes: [], is_diagnostic_only: true, trust_evaluation_status: 'UNEVALUATED' },
  reproducibility_audit: { canonical_run_fingerprint: 'cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca', manifest_sha256: 'cacd4054fff9', manifest_present: true, raw_input_artifacts_available: false, is_reproducible: true, reproducibility_status: 'ARTIFACT_REPRODUCIBLE' },
  calculation_manifest: {},
  limitations: ['LIM1', 'LIM2', 'LIM3']
};

describe('AeroCPI Milestone 6 Dashboard UI Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(apiModule, 'fetchDashboard').mockResolvedValue(mockDashboardData);
    vi.spyOn(apiModule, 'fetchExplanation').mockResolvedValue(mockExplanationData);
    vi.spyOn(apiModule, 'fetchAudit').mockResolvedValue(mockAuditData);
    vi.spyOn(apiModule, 'fetchIndexRuns').mockResolvedValue([
      { run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be', run_timestamp: '2026-09-12', reference_period: '2026-09-10', comparison_period: '2026-09-12', index_value: 96.209 }
    ]);
    vi.spyOn(apiModule, 'fetchObservationExplorer').mockResolvedValue({
      total: 5332,
      page: 1,
      page_size: 50,
      total_pages: 107,
      has_next: true,
      has_prev: false,
      observations: [
        {
          observation_id: '5384e147-ee3d-43c6-a855-cf5909208abf',
          route_id: 'DEL-HYD',
          source: 'SRC_GOOGLE_FLIGHTS',
          collection_timestamp: '2026-09-12T02:46:21.788673',
          travel_date: '2026-09-27',
          advance_purchase_days: 15,
          carrier: '6E',
          cabin: 'ECONOMY',
          total_fare: 9807.0,
          base_fare: 8335.95,
          taxes: 1471.05,
          fees: 0.0,
          stops: 0,
          duration_minutes: 130,
          currency: 'INR',
          validation_status: 'FLAG',
          index_eligibility: 'ELIGIBLE',
          quality_status: 'VALID',
          anomaly_flags: []
        }
      ]
    });
    vi.spyOn(apiModule, 'fetchRouteIntelligence').mockResolvedValue({
      route_id: 'DEL-HYD',
      origin: 'DEL',
      destination: 'HYD',
      dgca_weight: 0.103153,
      active_weight: 0.103153,
      collection_dates: ['2026-09-10', '2026-09-12'],
      route_index_value: 111.127,
      base_representative_fare: 8825.0,
      current_representative_fare: 9807.0,
      point_contribution: 1.0675,
      direction: 'POSITIVE',
      horizon_results: [
        { horizon_code: 'T+1', base_representative_fare: 8984.0, current_representative_fare: 8825.0, price_relative: 0.9823, point_contribution: -0.1481 },
        { horizon_code: 'T+7', base_representative_fare: 8904.5, current_representative_fare: 8827.0, price_relative: 0.9913, point_contribution: -0.0899 },
        { horizon_code: 'T+15', base_representative_fare: 8825.0, current_representative_fare: 9807.0, price_relative: 1.1113, point_contribution: 1.0675 },
        { horizon_code: 'T+30', base_representative_fare: 8828.0, current_representative_fare: 9004.5, price_relative: 1.02, point_contribution: 0.1944 },
        { horizon_code: 'T+45', base_representative_fare: 10425.0, current_representative_fare: 9809.0, price_relative: 0.9409, point_contribution: -0.5929 }
      ],
      coverage_ratio: 1.0,
      quality_summary: {
        completeness: 'COMPLETE',
        eligibility_ratio: 1.0,
        anomalies_detected: 0
      }
    });
    vi.spyOn(apiModule, 'fetchHorizonsIntelligence').mockResolvedValue([
      {
        horizon_code: 'T+1',
        horizon_days: 1,
        index_value: 63.496,
        base_coverage_ratio: 1.0,
        current_coverage_ratio: 1.0,
        matched_coverage_ratio: 1.0,
        active_routes_count: 10,
        total_basket_routes_count: 10,
        active_weight_sum: 1.0,
        is_headline: false,
        top_positive_routes: [],
        top_negative_routes: [
          {
            route_id: 'BLR-DEL',
            origin: 'BLR',
            destination: 'DEL',
            base_representative_fare: 9500.0,
            current_representative_fare: 6000.0,
            route_index_value: 63.16,
            point_contribution: -10.1977,
            direction: 'NEGATIVE',
            active_weight: 0.141
          }
        ]
      },
      {
        horizon_code: 'T+7',
        horizon_days: 7,
        index_value: 99.863,
        base_coverage_ratio: 1.0,
        current_coverage_ratio: 1.0,
        matched_coverage_ratio: 1.0,
        active_routes_count: 10,
        total_basket_routes_count: 10,
        active_weight_sum: 1.0,
        is_headline: false,
        top_positive_routes: [
          {
            route_id: 'BLR-CCU',
            origin: 'BLR',
            destination: 'CCU',
            base_representative_fare: 8000.0,
            current_representative_fare: 8500.0,
            route_index_value: 106.25,
            point_contribution: 0.6383,
            direction: 'POSITIVE',
            active_weight: 0.061
          }
        ],
        top_negative_routes: [
          {
            route_id: 'GOI-BOM',
            origin: 'GOI',
            destination: 'BOM',
            base_representative_fare: 7000.0,
            current_representative_fare: 6500.0,
            route_index_value: 92.86,
            point_contribution: -2.2218,
            direction: 'NEGATIVE',
            active_weight: 0.080
          }
        ]
      },
      {
        horizon_code: 'T+15',
        horizon_days: 15,
        index_value: 96.209,
        base_coverage_ratio: 1.0,
        current_coverage_ratio: 1.0,
        matched_coverage_ratio: 1.0,
        active_routes_count: 10,
        total_basket_routes_count: 10,
        active_weight_sum: 1.0,
        is_headline: true,
        top_positive_routes: [
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
        top_negative_routes: [
          {
            route_id: 'GOI-BOM',
            origin: 'GOI',
            destination: 'BOM',
            base_representative_fare: 9539.0,
            current_representative_fare: 5230.0,
            route_index_value: 54.828,
            point_contribution: -4.7391,
            direction: 'NEGATIVE',
            active_weight: 0.080006
          }
        ]
      },
      {
        horizon_code: 'T+30',
        horizon_days: 30,
        index_value: 90.600,
        base_coverage_ratio: 1.0,
        current_coverage_ratio: 1.0,
        matched_coverage_ratio: 1.0,
        active_routes_count: 10,
        total_basket_routes_count: 10,
        active_weight_sum: 1.0,
        is_headline: false,
        top_positive_routes: [],
        top_negative_routes: []
      },
      {
        horizon_code: 'T+45',
        horizon_days: 45,
        index_value: 88.949,
        base_coverage_ratio: 1.0,
        current_coverage_ratio: 1.0,
        matched_coverage_ratio: 1.0,
        active_routes_count: 10,
        total_basket_routes_count: 10,
        active_weight_sum: 1.0,
        is_headline: false,
        top_positive_routes: [],
        top_negative_routes: []
      }
    ]);
    vi.spyOn(apiModule, 'fetchDataQualitySummary').mockResolvedValue({
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      total_observations: 2668,
      eligible_observations: 2668,
      eligibility_ratio: 1.0,
      completeness: { VALID: 2668 },
      timestamp_validity: { VALID: 2668 },
      fare_integrity: { VALID: 2668 },
      route_mapping: { VALID: 2668 },
      duplicate_risk: { NONE: 2668 },
      anomaly_flags_breakdown: {},
      source_health_breakdown: { HEALTHY: 2 },
      quality_rule_version: 'QR-2026.1'
    });
    vi.spyOn(apiModule, 'fetchDataQualityRoutes').mockResolvedValue({
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      routes: [
        { route_id: 'DEL-BOM', total_quotes: 270, eligible_quotes: 270, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'DEL-BLR', total_quotes: 265, eligible_quotes: 265, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'BOM-BLR', total_quotes: 260, eligible_quotes: 260, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'DEL-HYD', total_quotes: 268, eligible_quotes: 268, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'CCU-DEL', total_quotes: 266, eligible_quotes: 266, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'BOM-GOI', total_quotes: 264, eligible_quotes: 264, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'DEL-MAA', total_quotes: 268, eligible_quotes: 268, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'BLR-HYD', total_quotes: 270, eligible_quotes: 270, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'DEL-PNQ', total_quotes: 267, eligible_quotes: 267, eligibility_ratio: 1.0, anomaly_flags: [] },
        { route_id: 'DEL-PAT', total_quotes: 270, eligible_quotes: 270, eligibility_ratio: 1.0, anomaly_flags: [] }
      ]
    });
    vi.spyOn(apiModule, 'fetchDataQualitySources').mockResolvedValue({
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      sources: [
        { source_name: 'GOOGLE_FLIGHTS_API', status: 'HEALTHY', observations_contributed: 2668, latency_ms: 245 },
        { source_name: 'DUFFEL_API', status: 'STANDBY', observations_contributed: 0, latency_ms: 0 }
      ]
    });
    vi.spyOn(apiModule, 'fetchMethodologyConfiguration').mockResolvedValue({
      configuration_version: '2026.1.0-default',
      configuration_fingerprint: 'eac9d1876c3aa2989dbdd4720777e51ae3ed386d00315f9d4bd0e813f826fa72',
      basket_version: 'DGCA-10-2026.1',
      horizon_set: ['T+1', 'T+7', 'T+15', 'T+30', 'T+45'],
      validation_rule_version: 'VAL-2026.1',
      outlier_rule_version: 'IQR-1.5-v1',
      source_policy_version: 'MULTI-SOURCE-V1',
      aggregation_version: 'JEVONS-GEOMETRIC-V1',
      publication_threshold_version: 'PUB-THRESH-V1',
      effective_from: '2026-09-12T14:40:51.618925',
      effective_to: null,
      human_descriptions: {
        basket_version: 'DGCA 10 Top Indian Domestic Routes Basket based on annual passenger traffic',
        horizon_set: '5 Advance Purchase Booking Windows: T+1 (Spot), T+7 (1 Wk), T+15 (Headline 2 Wks), T+30 (1 Mo), T+45 (6 Wks)',
        validation_rule_version: 'Structural Validation Rule Suite V1 (Cabin Y-class, Non-stop priority, INR currency)',
        outlier_rule_version: 'Interquartile Range (IQR 1.5x) Outlier Detection Engine',
        source_policy_version: 'Multi-Source Agreement & Aggregation Policy',
        aggregation_version: 'Unweighted Jevons Geometric Mean & Weighted Geometric National Aggregation with Active Weight Renormalization',
        publication_threshold_version: 'Minimum 80% Basket Coverage & 85% Active Weight Sum Publication Threshold'
      }
    });
    vi.spyOn(apiModule, 'fetchPublicationReadiness').mockResolvedValue({
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      status: 'PUBLISHABLE',
      is_publishable: true,
      reasons: ['All headline coverage, active weight, and observation health criteria satisfied'],
      headline_coverage_ratio: 1.0,
      active_weight_sum: 1.0,
      trust_status: 'UNEVALUATED',
      evaluated_at: '2026-09-12T14:40:51.646649+00:00'
    });
    vi.spyOn(apiModule, 'fetchValidationBenchmarks').mockResolvedValue([]);
    vi.spyOn(apiModule, 'fetchValidationRun').mockResolvedValue({
      validation_run_id: 'val-run-e1c05338',
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      benchmark_id: null,
      status: 'DISABLED_NO_BENCHMARK_DATA',
      validation_timestamp: '2026-09-12T14:40:51.646649+00:00',
      metrics: null
    });
    vi.spyOn(apiModule, 'fetchValidationMetrics').mockResolvedValue(null);
  });

  it('1. Renders complete executive dashboard with AeroCPI branding and sections', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
      expect(screen.getByText('AeroCPI_T15')).toBeInTheDocument();
      expect(screen.getByText('WHY DID IT MOVE?')).toBeInTheDocument();
      expect(screen.getByText('Coverage of AeroCPI basket')).toBeInTheDocument();
      expect(screen.getByText('Measurement Trust Evaluation')).toBeInTheDocument();
      expect(screen.getByText('AUDIT & EVIDENCE')).toBeInTheDocument();
    });
  });

  it('2. Reconciles headline metric and change from baseline', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('96.21').length).toBeGreaterThan(0);
      expect(screen.getByText(/3.79 index points/i)).toBeInTheDocument();
      expect(screen.getByText(/Independent airfare measurement index designed to augment CPI/i)).toBeInTheDocument();
    });
  });

  it('3. Renders positive and negative route drivers directly from API', async () => {
    render(<App />);

    await waitFor(() => {
      const driverSection = screen.getByTestId('driver-section');
      expect(within(driverSection).getByText('DEL-HYD')).toBeInTheDocument();
      expect(within(driverSection).getByText('+1.07')).toBeInTheDocument();
      expect(within(driverSection).getByText('GOI-BOM')).toBeInTheDocument();
      expect(within(driverSection).getByText('-4.74')).toBeInTheDocument();
    });
  });

  it('4. Highlights T+15 headline horizon in coverage panel', async () => {
    render(<App />);

    await waitFor(() => {
      const headlineBadges = screen.getAllByText('HEADLINE');
      expect(headlineBadges.length).toBeGreaterThan(0);
      expect(screen.getByText('T+15')).toBeInTheDocument();
    });
  });

  it('5. Renders UNEVALUATED trust status without a fake 0/100 score', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('UNEVALUATED')).toBeInTheDocument();
      expect(screen.getByText(/Trust evaluation not attached/i)).toBeInTheDocument();
      expect(screen.queryByText('0 / 100')).not.toBeInTheDocument();
    });
  });

  it('6. Renders artifact reproducibility status and manifest presence', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('ARTIFACT_REPRODUCIBLE')).toBeInTheDocument();
      expect(screen.getByText('Present')).toBeInTheDocument();
    });
  });

  it('7. Displays known limitation count in audit panel', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('3 items')).toBeInTheDocument();
    });
  });

  it('8. Renders Level 2 Route Explanation modal with 5A attribution detail', () => {
    render(
      <RouteExplanationModal
        routeId="DEL-HYD"
        explanation={mockExplanationData}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Milestone 5A Transparent Mathematical Route Attribution')).toBeInTheDocument();
    expect(screen.getByText('+1.0675 pts')).toBeInTheDocument();
    expect(screen.getByText('POSITIVE ATTRIBUTION')).toBeInTheDocument();
    expect(screen.getByText('₹8,825')).toBeInTheDocument();
    expect(screen.getByText('₹9,807')).toBeInTheDocument();
  });

  it('9. Renders Level 3 Measurement Audit modal with 5B audit details', () => {
    render(
      <AuditModal
        isOpen={true}
        audit={mockAuditData}
        onClose={() => {}}
      />
    );

    expect(screen.getByText('Milestone 5B Measurement Audit')).toBeInTheDocument();
    expect(screen.getByText('cacd4054fff92a9ef625325e33355c061a6432172eb51958f221600a1ba46bca')).toBeInTheDocument();
    expect(screen.getAllByText('7,924').length).toBeGreaterThan(0);
    expect(screen.getByText('DERIVED_FROM_PERSISTED_RUN_ARTIFACT')).toBeInTheDocument();
  });

  it('10. Renders HTTP 404 error view when API fails with 404', async () => {
    vi.spyOn(apiModule, 'fetchDashboard').mockRejectedValue({
      response: { status: 404, data: { detail: "Index run 'non-existent' not found" } }
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('HTTP 404 — INDEX RUN NOT FOUND')).toBeInTheDocument();
    });
  });

  it('11. Renders Observation Explorer evidence ledger and opens inspection drawer', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    // Navigate to Observation Explorer tab
    const explorerTab = screen.getAllByText('Observation Explorer')[0];
    fireEvent.click(explorerTab);

    // Verify ledger header and items
    await waitFor(() => {
      expect(screen.getByText('OBSERVATION EXPLORER')).toBeInTheDocument();
      expect(screen.getByText('OBSERVATION LEDGER')).toBeInTheDocument();
      expect(screen.getByText('SERVER-CERTIFIED')).toBeInTheDocument();
    });

    // Click "Inspect" button to trigger evidence drawer
    const inspectButton = screen.getByText('Inspect');
    fireEvent.click(inspectButton);

    await waitFor(() => {
      expect(screen.getByText('Observation Evidence Record')).toBeInTheDocument();
      expect(screen.getByText('1. OBSERVATION IDENTITY')).toBeInTheDocument();
      expect(screen.getByText('2. FARE DECOMPOSITION')).toBeInTheDocument();
      expect(screen.getByText('3. FLIGHT OPERATIONAL CONTEXT')).toBeInTheDocument();
      expect(screen.getByText('4. QUALITY & VALIDATION DIAGNOSTICS')).toBeInTheDocument();
      expect(screen.getByText('5. PROVENANCE & AUDIT TRAIL')).toBeInTheDocument();
    });
  });

  it('12. Renders Route Intelligence page with 10 corridor tabs, fetches corridor intelligence, and displays 5-horizon term structure', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    // Navigate to Route Intelligence tab
    const routeTab = screen.getAllByText('Route Intelligence')[0];
    fireEvent.click(routeTab);

    // Verify page header and corridor chips
    await waitFor(() => {
      expect(screen.getByText('ROUTE CORRIDOR INTELLIGENCE')).toBeInTheDocument();
      expect(screen.getByText('10 DGCA Corridors')).toBeInTheDocument();
      expect(screen.getAllByText('DEL-HYD').length).toBeGreaterThan(0);
      expect(screen.getAllByText('GOI-BOM').length).toBeGreaterThan(0);
      expect(screen.getAllByText('BLR-DEL').length).toBeGreaterThan(0);
    });

    // Verify corridor spotlight metrics and 5-horizon term structure
    await waitFor(() => {
      expect(screen.getByText('CORRIDOR SPOTLIGHT')).toBeInTheDocument();
      expect(screen.getAllByText('111.13').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('5-Horizon Advance Booking Term Structure')).toBeInTheDocument();
    });
  });

  it('13. Renders Horizon Analysis page with Forward Booking Horizon Curve and answers core questions', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    // Navigate to Horizon Analysis tab
    const horizonTab = screen.getAllByText('Horizon Analysis')[0];
    fireEvent.click(horizonTab);

    // Verify page header
    await waitFor(() => {
      expect(screen.getAllByText('Horizon Analysis')[0]).toBeInTheDocument();
    });

    // Verify Forward Booking Horizon Curve and Headline T+15
    await waitFor(() => {
      expect(screen.getByText('Forward Booking Horizon Curve / Term Structure')).toBeInTheDocument();
      expect(screen.getAllByText('T+15').length).toBeGreaterThan(0);
      
      
      
      expect(screen.getByText('5-Horizon Comparative Term Structure Summary')).toBeInTheDocument();
    });
  });

  it('14. Renders Data Quality page with decomposed health dimensions, route matrix, source status, and trust governance', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    // Navigate to Data Quality tab
    const dqTab = screen.getAllByText('Data Quality')[0];
    fireEvent.click(dqTab);

    // Verify page header and decomposed health dimensions
    await waitFor(() => {
      expect(screen.getByText('MEASUREMENT QUALITY & TRUST OBSERVATORY')).toBeInTheDocument();
      expect(screen.getByText('Decomposed Diagnostics')).toBeInTheDocument();
      expect(screen.getByText('Decomposed Measurement Health Dimensions')).toBeInTheDocument();
      expect(screen.getByText('1. Completeness')).toBeInTheDocument();
      expect(screen.getByText('2. Fare Integrity')).toBeInTheDocument();
      expect(screen.getByText('3. Observation Validity')).toBeInTheDocument();
      expect(screen.getByText('4. Outlier Governance')).toBeInTheDocument();
      expect(screen.getByText('5. Source Availability')).toBeInTheDocument();
      expect(screen.getByText('6. Basket / Horizon Stability')).toBeInTheDocument();
    });

    // Verify Route-Level Quality Matrix, Source Adapter Health, and Trust Status
    await waitFor(() => {
      expect(screen.getByText('Route-Level Quality Matrix (10 DGCA Corridors)')).toBeInTheDocument();
      expect(screen.getByText('Source-Level Availability & Breakdown Governance')).toBeInTheDocument();
      expect(screen.getAllByText('GOOGLE_FLIGHTS_API').length).toBeGreaterThan(0);
      expect(screen.getAllByText(/DUFFEL_API/i).length).toBeGreaterThan(0);
      expect(screen.getByText('Automated Exclusion & Flag Ledger')).toBeInTheDocument();
      expect(screen.getByText('Trust Engine & Reproducibility Audit')).toBeInTheDocument();
    });
  });

  it('15. Renders Methodology Studio with versioned configuration specifications, deterministic publication gate, and 7-stage pipeline', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    // Navigate to Methodology Studio tab
    const methodTab = screen.getAllByText('Methodology Studio')[0];
    fireEvent.click(methodTab);

    // Verify page header and versioned configuration section
    await waitFor(() => {
      expect(screen.getByText('METHODOLOGY STUDIO & MEASUREMENT SPECIFICATION')).toBeInTheDocument();
      expect(screen.getByText('Sovereign Standard')).toBeInTheDocument();
      expect(screen.getByText('Versioned Measurement Configuration & Governance')).toBeInTheDocument();
      expect(screen.getByText('1. Route Basket')).toBeInTheDocument();
      expect(screen.getByText('2. Horizon Set')).toBeInTheDocument();
      expect(screen.getByText('3. Validation Rules')).toBeInTheDocument();
      expect(screen.getByText('4. Outlier Governance')).toBeInTheDocument();
      expect(screen.getByText('5. Source Policy')).toBeInTheDocument();
      expect(screen.getByText('6. Aggregation Engine')).toBeInTheDocument();
      expect(screen.getByText('7. Publication Threshold & Gate Rules')).toBeInTheDocument();
    });

    // Verify Deterministic Publication Gate
    await waitFor(() => {
      expect(screen.getByText('Deterministic Publication Gate & Certification')).toBeInTheDocument();
      expect(screen.getByText('Headline Basket Coverage')).toBeInTheDocument();
      expect(screen.getByText('Active DGCA Weight Sum')).toBeInTheDocument();
      expect(screen.getByText('Trust Status Evaluation')).toBeInTheDocument();
      expect(screen.getByText('Publication Gate Verdict')).toBeInTheDocument();
    });

    // Verify 7-stage pipeline and log-linear proof
    await waitFor(() => {
      expect(screen.getByText('7-Stage End-to-End Calculation Pipeline Architecture')).toBeInTheDocument();
      expect(screen.getByText('Stage 1: Data Collection & Ingestion')).toBeInTheDocument();
      expect(screen.getByText('Mathematical Proof: Exact Additive Log-Linear Attribution')).toBeInTheDocument();
      expect(screen.getByText('AeroCPI Methodology Boundaries & Non-Equivalence Notice')).toBeInTheDocument();
    });

    // Switch to Stage 4 (Jevons Elementary)
    const stage4Button = screen.getByText('STAGE 4');
    fireEvent.click(stage4Button);

    await waitFor(() => {
      expect(screen.getByText('Stage 4: Jevons Elementary Route Index Computation')).toBeInTheDocument();
      expect(screen.getByText('Unweighted Geometric Mean of Price Relatives (Jᵣ)')).toBeInTheDocument();
    });
  });

  it('16. Renders Validation Lab with first-class DISABLED_NO_BENCHMARK_DATA state, protocol pipeline, and scientific interpretation', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    // Navigate to Validation Lab tab
    const valTab = screen.getAllByText('Validation Lab')[0];
    fireEvent.click(valTab);

    // Verify header and hero state
    await waitFor(() => {
      expect(screen.getAllByText('Validation Lab').length).toBeGreaterThan(1);
      expect(screen.getByText('Scientific Test Bench')).toBeInTheDocument();
      expect(screen.getByText('Independent Benchmarking & Measurement Validation')).toBeInTheDocument();
      expect(screen.getByText('VALIDATION STATUS')).toBeInTheDocument();
      expect(screen.getAllByText(/DISABLED_NO_BENCHMARK_DATA/i).length).toBeGreaterThan(0);
      expect(
        screen.getByText(
          /"No independent benchmark dataset is currently available for execution. AeroCPI therefore does not publish fabricated validation statistics."/i
        )
      ).toBeInTheDocument();
    });

    // Verify Section A: Validation Status & Execution Telemetry
    await waitFor(() => {
      expect(screen.getByText('A. Validation Status & Execution Telemetry')).toBeInTheDocument();
      expect(screen.getAllByText('NOT EXECUTED').length).toBeGreaterThan(0);
      expect(screen.getByText('0 Registered')).toBeInTheDocument();
    });

    // Verify Section B: Benchmark Definition & Specification Table
    await waitFor(() => {
      expect(screen.getByText('B. Independent Benchmark Specification & Definition')).toBeInTheDocument();
      expect(screen.getByText('1. Source Authority')).toBeInTheDocument();
      expect(screen.getByText('2. Route Basket Scope')).toBeInTheDocument();
      expect(screen.getByText('3. Temporal Window')).toBeInTheDocument();
      expect(screen.getByText('4. Lead Horizon Structure')).toBeInTheDocument();
      expect(screen.getByText('5. Cabin & Flight Rules')).toBeInTheDocument();
      expect(screen.getByText('6. Fare Metric Definition')).toBeInTheDocument();
      expect(screen.getByText('Registered Benchmark Specifications')).toBeInTheDocument();
    });

    // Open Benchmark Detail Inspector
    const inspectButton = screen.getAllByText('Inspect Spec')[0];
    fireEvent.click(inspectButton);

    await waitFor(() => {
      expect(screen.getByText('Benchmark Specification Inspector')).toBeInTheDocument();
      expect(screen.getAllByText('DGCA Official Domestic Passenger Yield Series').length).toBeGreaterThan(1);
      expect(screen.getByText('Directorate General of Civil Aviation (DGCA)')).toBeInTheDocument();
    });

    // Close Inspector
    const closeButton = screen.getByText('Close Inspector');
    fireEvent.click(closeButton);

    // Verify Section C: Validation Protocol & 6-Stage Pipeline
    await waitFor(() => {
      expect(screen.getByText('C. Validation Protocol & Execution Pipeline')).toBeInTheDocument();
      expect(screen.getAllByText('BENCHMARK').length).toBeGreaterThan(0);
      expect(screen.getByText('ALIGN')).toBeInTheDocument();
      expect(screen.getByText('MATCH')).toBeInTheDocument();
      expect(screen.getByText('COMPARE')).toBeInTheDocument();
      expect(screen.getByText('SCORE')).toBeInTheDocument();
      expect(screen.getByText('INTERPRET')).toBeInTheDocument();
      expect(screen.getByText('Stage 1: Benchmark Artifact Registration')).toBeInTheDocument();
    });

    // Switch protocol stage
    const matchStageButton = screen.getByText('MATCH');
    fireEvent.click(matchStageButton);

    await waitFor(() => {
      expect(screen.getByText('Stage 3: Cell-Level Observation Matching')).toBeInTheDocument();
    });

    // Verify Section D: Results in NO BENCHMARK state (Not Available metric shells, no fabricated stats)
    await waitFor(() => {
      expect(screen.getByText('D. Empirical Validation Results & Tracking Error')).toBeInTheDocument();
      expect(screen.getByText('NO VALIDATION RESULT')).toBeInTheDocument();
      expect(screen.getAllByText('Coverage Agreement').length).toBeGreaterThan(0);
      expect(screen.getByText('Level Error (MAD)')).toBeInTheDocument();
      expect(screen.getByText('Directional Agreement')).toBeInTheDocument();
      expect(screen.getByText('RMSE / MAE')).toBeInTheDocument();
      expect(screen.getByText('Pearson Correlation (r)')).toBeInTheDocument();
      expect(screen.getByText('Relative Deviation (MRD)')).toBeInTheDocument();
      expect(screen.getAllByText('Not Available').length).toBe(6);
    });

    // Verify Internal Index Integrity Tests (5/5 PASSED)
    await waitFor(() => {
      expect(screen.getByText('Internal Index Integrity Tests')).toBeInTheDocument();
      expect(screen.getByText('Time Reversal Test')).toBeInTheDocument();
      expect(screen.getByText('Proportionality / Homogeneity')).toBeInTheDocument();
      expect(screen.getByText('Dimensional Invariance')).toBeInTheDocument();
      expect(screen.getByText('Monotonicity')).toBeInTheDocument();
      expect(screen.getByText('Exact Log-Linear Route Point Additivity')).toBeInTheDocument();
      expect(screen.getByText('5 / 5 PASSED')).toBeInTheDocument();
    });

    // Verify Section E: Limitations & Interpretation
    await waitFor(() => {
      expect(screen.getByText('E. Limitations & Scientific Interpretation')).toBeInTheDocument();
      expect(screen.getByText('Internal Consistency is NOT Independent Validation')).toBeInTheDocument();
      expect(screen.getByText('AeroCPI Observations Cannot Serve as Benchmarks')).toBeInTheDocument();
      expect(screen.getByText('No Benchmark Means No Empirical Claim')).toBeInTheDocument();
      expect(screen.getByText('Validation Does Not Establish MoSPI CPI Equivalence')).toBeInTheDocument();
      expect(screen.getByText('MoSPI CPI Augmentation Principle & Structural Comparison')).toBeInTheDocument();
    });

    // Verify Section F: Validation Provenance Trace and Cross-Module Links
    await waitFor(() => {
      expect(screen.getByText('F. Validation Provenance Trace')).toBeInTheDocument();
      expect(screen.getByText('View Methodology →')).toBeInTheDocument();
      expect(screen.getByText('Inspect Measurement Trace →')).toBeInTheDocument();
      expect(screen.getByText('Inspect Configuration →')).toBeInTheDocument();
      expect(screen.getByText('View Production Run →')).toBeInTheDocument();
    });
  });

  it('17. Renders executed validation metrics when independent benchmark is active and returned by backend', async () => {
    vi.spyOn(apiModule, 'fetchValidationRun').mockResolvedValue({
      validation_run_id: 'val-run-executed-001',
      run_id: 'e1c05338-bc7a-4e2f-8b81-f855ca54c3be',
      benchmark_id: 'BM-DGCA-YIELDS-V1',
      status: 'ACTIVE',
      validation_timestamp: '2026-09-12T14:40:51.646649+00:00',
      metrics: {
        metric_id: 'metric-001',
        validation_run_id: 'val-run-executed-001',
        coverage: 0.95,
        directional_agreement: 0.88,
        correlation: 0.9412,
        absolute_deviation: 1.45,
        relative_deviation: 0.0152,
        route_level_deviation: {
          'DEL-BOM': 1.12,
          'BLR-DEL': 1.68
        },
        created_at: '2026-09-12T14:40:51.646649+00:00'
      }
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getAllByText('AeroCPI')[0]).toBeInTheDocument();
    });

    const valTab = screen.getAllByText('Validation Lab')[0];
    fireEvent.click(valTab);

    await waitFor(() => {
      expect(screen.getByText('95.0%')).toBeInTheDocument();
      expect(screen.getByText('88.0%')).toBeInTheDocument();
      expect(screen.getByText('0.9412')).toBeInTheDocument();
      expect(screen.getByText('1.45 pts')).toBeInTheDocument();
      expect(screen.getByText('1.52%')).toBeInTheDocument();
      expect(screen.getByText('DEL-BOM')).toBeInTheDocument();
      expect(screen.getByText('1.12 pts')).toBeInTheDocument();
    });
  });

it('18. Renders Audit & Measurement Trace page with 9-stage provenance visual, strictly respects zero-client-calculation rule, and populates artifacts correctly from the 5B/5A APIs', async () => { render(<App />); await waitFor(() => { expect(screen.getAllByText('Overview')[0]).toBeInTheDocument(); }); const auditTab = screen.getAllByText('Audit & Trace')[0]; fireEvent.click(auditTab); await waitFor(() => { expect(screen.getAllByText(/Measurement Trace Architecture/i).length).toBeGreaterThan(0); }); expect(screen.getAllByText(/INDEX RUN/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/CONFIGURATION/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/HORIZONS/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/ROUTES/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/REPRESENTATIVE FARES/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/OBSERVATIONS/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/QUALITY/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/EXPLANATION/i).length).toBeGreaterThan(0); expect(screen.getAllByText(/SHA-256 FINGERPRINT/i).length).toBeGreaterThan(0); fireEvent.click(screen.getByText(/01/i).closest('div')!); await waitFor(() => { expect(screen.getAllByText(/Run ID/i).length).toBeGreaterThan(0); }); });

  it('19. Renders exact frozen methodology formulas in Methodology Studio and Route Explanation Modal with KaTeX typography', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getAllByText('Overview')[0]).toBeInTheDocument();
    });

    // 1. Verify Methodology Studio formulas
    const methTab = screen.getAllByText('Methodology Studio')[0];
    fireEvent.click(methTab);

    await waitFor(() => {
      expect(screen.getByText(/METHODOLOGY STUDIO & MEASUREMENT SPECIFICATION/i)).toBeInTheDocument();
    });

    // Select Stage 6
    const stage6Btn = screen.getByText('STAGE 6');
    fireEvent.click(stage6Btn);

    await waitFor(() => {
      expect(screen.getByText(/Stage 6: AeroCPI Basket Aggregation & Log-Linear Attribution/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Weighted Geometric National Aggregation with Active Weight Renormalization/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/1. National Aggregation \(Index Level Form\):/i)).toBeInTheDocument();
      expect(screen.getByText(/2. Equivalent Logarithmic Form:/i)).toBeInTheDocument();
    });

    // Verify Section 5 exact attribution and reconciliation identity
    expect(screen.getByText(/Mathematical Proof: Exact Additive Log-Linear Attribution/i)).toBeInTheDocument();
    expect(screen.getByText(/2. Milestone 5A Route Attribution Identity \(Point Contribution Formula\)/i)).toBeInTheDocument();
    expect(screen.getByText(/3. Exact Reconciliation Identity/i)).toBeInTheDocument();

    // 2. Verify Route Explanation Modal formulas directly
    render(
      <RouteExplanationModal
        routeId="DEL-HYD"
        explanation={mockExplanationData}
        onClose={() => {}}
      />
    );

    expect(screen.getByText(/Milestone 5A Route Attribution Identity:/i)).toBeInTheDocument();
    expect(screen.getByText(/Route Point Contribution Formula:/i)).toBeInTheDocument();
    expect(screen.getByText(/Exact Reconciliation Identity:/i)).toBeInTheDocument();
  });
});

