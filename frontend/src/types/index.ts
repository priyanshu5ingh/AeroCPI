export interface DashboardScope {
  run_id: string;
  reference_date: string;
  calculation_date: string;
  cabin: string;
  dashboard_timestamp: string;
}

export interface DashboardHeadline {
  horizon_code: string;
  index_name: string;
  index_value: number;
  reference_date: string;
  calculation_date: string;
  change_from_base: number;
  direction: 'UP' | 'DOWN' | 'UNCHANGED' | string;
  is_headline: boolean;
}

export interface RouteDriverItem {
  route_id: string;
  origin: string;
  destination: string;
  base_representative_fare: number;
  current_representative_fare: number;
  route_index_value: number;
  point_contribution: number | null;
  direction: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | string;
  active_weight: number;
}

export interface DriverSummary {
  top_positive_drivers: RouteDriverItem[];
  top_negative_drivers: RouteDriverItem[];
}

export interface HorizonCoverageItem {
  horizon_code: string;
  index_value: number | null;
  base_coverage_ratio: number;
  current_coverage_ratio: number;
  matched_coverage_ratio: number;
  active_routes_count: number;
  total_basket_routes_count: number;
  active_weight_sum: number;
}

export interface CoverageSummary {
  headline_horizon_code: string;
  headline_coverage_ratio: number;
  horizon_coverage: HorizonCoverageItem[];
}

export interface DashboardTrustSummary {
  trust_score: number | null;
  trust_status: string;
  reason_codes: string[];
  is_diagnostic_only: boolean;
  trust_evaluation_status: string;
}

export interface MethodologySummary {
  methodology_version: string;
  basket_version: string;
  proxy_weight_version: string;
  software_version: string;
  reference_date: string;
  calculation_date: string;
  cabin: string;
  headline_horizon: string;
  disclaimer: string;
}

export interface DashboardAuditSummary {
  canonical_run_fingerprint: string;
  manifest_sha256: string | null;
  manifest_present: boolean;
  raw_input_artifacts_available: boolean;
  reproducibility_status: string;
  limitations: string[];
}

export interface IndexDashboardResponse {
  dashboard_scope: DashboardScope;
  headline: DashboardHeadline;
  drivers: DriverSummary;
  coverage: CoverageSummary;
  trust: DashboardTrustSummary;
  methodology: MethodologySummary;
  audit: DashboardAuditSummary;
  disclaimer: string;
}

// 5A Explanation Types
export interface RouteContributionExplanation {
  route_id: string;
  horizon_code: string;
  collection_date: string;
  origin_code: string;
  destination_code: string;
  base_representative_fare: number;
  current_representative_fare: number;
  price_relative: number;
  route_index_value: number;
  dgca_basket_weight: number;
  active_weight: number;
  log_contribution: number;
  point_contribution: number | null;
  direction: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | string;
}

export interface MissingRouteInfo {
  route_id: string;
  horizon_code: string;
  reason_code: string;
  description: string;
}

export interface HorizonExplanation {
  horizon_code: string;
  horizon_days: number;
  collection_date: string;
  index_name: string;
  index_value: number | null;
  matched_sample_index_value: number | null;
  is_headline: boolean;
  active_routes_count: number;
  base_routes_count: number;
  total_basket_routes_count: number;
  base_coverage_ratio: number;
  current_coverage_ratio: number;
  matched_coverage_ratio: number;
  active_weight_sum: number;
  reason_codes: string[];
  route_contributions: RouteContributionExplanation[];
  missing_routes: MissingRouteInfo[];
}

export interface TrustExplanation {
  trust_evaluation_id: string | null;
  trust_score: number | null;
  trust_status: string;
  reason_codes: string[];
  is_diagnostic_only: boolean;
}

export interface IndexExplanationResponse {
  explanation_scope: {
    run_id: string;
    reference_date: string;
    calculation_date: string;
    cabin: string;
    basket_version: string;
  };
  index_run_id: string;
  headline_horizon_code: string;
  headline_index_value: number;
  reference_date: string;
  calculation_date: string;
  methodology_version: string;
  route_basket_version: string;
  proxy_weight_version: string;
  software_version: string;
  canonical_run_fingerprint: string;
  horizons: HorizonExplanation[];
  trust_summary: TrustExplanation;
  calculation_manifest: Record<string, any>;
}

// 5B Audit Types
export interface IndexAuditResponse {
  audit_scope: {
    run_id: string;
    reference_date: string;
    calculation_date: string;
    cabin: string;
    basket_version: string;
    audit_timestamp: string;
  };
  run_identity: {
    run_id: string;
    run_timestamp: string;
    reference_period: string;
    comparison_period: string;
    index_method: string;
    frequency: string;
    headline_index_value: number;
    headline_horizon_code: string;
  };
  versions: {
    methodology_version: string;
    route_basket_version: string;
    proxy_weight_version: string;
    software_version: string;
    quality_rule_version: string;
    normalization_version: string;
  };
  population_audit: {
    total_observations_queried: number;
    total_eligible_observations: number;
    total_excluded_observations: number;
    rejection_breakdown: Record<string, number>;
    reference_date_count: number | null;
    calculation_date_count: number | null;
    provenance_status: string;
  };
  route_audit: {
    total_basket_routes: number;
    expected_route_horizon_pairs: number;
    calculated_route_horizon_pairs: number;
    unavailable_route_horizon_pairs: number;
    horizon_route_counts: {
      horizon_code: string;
      horizon_days: number;
      active_routes_count: number;
      base_routes_count: number;
      missing_routes_count: number;
      total_basket_routes_count: number;
    }[];
  };
  coverage_audit: {
    headline_coverage_ratio: number;
    horizon_coverage: {
      horizon_code: string;
      base_coverage_ratio: number;
      current_coverage_ratio: number;
      matched_coverage_ratio: number;
      active_weight_sum: number;
    }[];
    temporal_coverage_status: string;
  };
  trust_audit: {
    trust_evaluation_id: string | null;
    trust_score: number | null;
    trust_status: string;
    reason_codes: string[];
    is_diagnostic_only: boolean;
    trust_evaluation_status: string;
  };
  reproducibility_audit: {
    canonical_run_fingerprint: string;
    manifest_sha256: string | null;
    manifest_present: boolean;
    raw_input_artifacts_available: boolean;
    is_reproducible: boolean;
    reproducibility_status: string;
  };
  calculation_manifest: Record<string, any>;
  limitations: string[];
}

export interface SimpleIndexRun {
  run_id: string;
  run_timestamp: string;
  reference_period: string;
  comparison_period: string;
  index_value: number;
}

export interface ObservationExplorerItem {
  observation_id: string;
  route_id: string;
  source: string;
  collection_timestamp: string;
  search_timestamp?: string;
  travel_date: string | null;
  advance_purchase_days: number;
  carrier: string;
  cabin: string;
  total_fare: number;
  base_fare?: number | null;
  taxes?: number | null;
  fees?: number | null;
  stops: number;
  duration_minutes: number;
  currency: string;
  validation_status: string;
  index_eligibility: string;
  quality_status: string;
  anomaly_flags: string[];
}

export interface ObservationExplorerResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
  observations: ObservationExplorerItem[];
}

export interface RouteHorizonResultItem {
  horizon_code: string;
  base_representative_fare: number;
  current_representative_fare: number;
  price_relative: number;
  point_contribution: number | null;
}

export interface RouteIntelligenceResponse {
  route_id: string;
  origin: string;
  destination: string;
  dgca_weight: number;
  active_weight: number;
  collection_dates: string[];
  route_index_value: number;
  base_representative_fare: number;
  current_representative_fare: number;
  point_contribution: number | null;
  direction: string;
  horizon_results: RouteHorizonResultItem[];
  coverage_ratio: number;
  quality_summary: {
    completeness: string;
    eligibility_ratio: number;
    anomalies_detected: number;
  };
}

export interface HorizonIntelligenceResponse {
  horizon_code: string;
  horizon_days: number;
  index_value: number;
  base_coverage_ratio: number;
  current_coverage_ratio: number;
  matched_coverage_ratio: number;
  active_routes_count: number;
  total_basket_routes_count: number;
  active_weight_sum: number;
  is_headline: boolean;
  top_positive_routes: RouteDriverItem[];
  top_negative_routes: RouteDriverItem[];
}

export interface DataQualitySummaryResponse {
  run_id: string;
  total_observations: number;
  eligible_observations: number;
  eligibility_ratio: number;
  completeness: Record<string, number>;
  timestamp_validity: Record<string, number>;
  fare_integrity: Record<string, number>;
  route_mapping: Record<string, number>;
  duplicate_risk: Record<string, number>;
  anomaly_flags_breakdown: Record<string, number>;
  source_health_breakdown: Record<string, number>;
  quality_rule_version: string;
}

export interface DataQualityRouteItem {
  route_id: string;
  total_quotes: number;
  eligible_quotes: number;
  eligibility_ratio: number;
  anomaly_flags: string[];
}

export interface DataQualityRoutesResponse {
  run_id: string;
  routes: DataQualityRouteItem[];
}

export interface DataQualitySourceItem {
  source_name: string;
  status: string;
  observations_contributed: number;
  latency_ms: number;
}

export interface DataQualitySourcesResponse {
  run_id: string;
  sources: DataQualitySourceItem[];
}

export interface MethodologyInfoResponse {
  configuration_version: string;
  configuration_fingerprint: string;
  basket_version: string;
  horizon_set: string[];
  validation_rule_version: string;
  outlier_rule_version: string;
  source_policy_version: string;
  aggregation_version: string;
  publication_threshold_version: string;
  effective_from: string;
  effective_to?: string | null;
  human_descriptions: Record<string, string>;
}

export interface PublicationReadinessResponse {
  run_id: string;
  status: string;
  is_publishable: boolean;
  reasons: string[];
  headline_coverage_ratio: number;
  active_weight_sum: number;
  trust_status: string;
  evaluated_at: string;
}

export interface ValidationBenchmark {
  benchmark_id: string;
  name: string;
  description?: string | null;
  source: string;
  reference_period: string;
  created_at: string;
}

export interface ValidationMetric {
  metric_id: string;
  validation_run_id: string;
  coverage?: number | null;
  directional_agreement?: number | null;
  correlation?: number | null;
  absolute_deviation?: number | null;
  relative_deviation?: number | null;
  route_level_deviation?: Record<string, number> | null;
  created_at: string;
}

export interface ValidationRun {
  validation_run_id: string;
  run_id: string;
  benchmark_id?: string | null;
  status: string; // "ACTIVE" | "DISABLED_NO_BENCHMARK_DATA"
  validation_timestamp: string;
  metrics?: ValidationMetric | null;
}

export interface TraceIndexRunNode { run_id: string; headline_index_value: number; headline_horizon_code: string; reference_date: string; calculation_date: string; } export interface TraceConfigurationNode { configuration_version: string; basket_version: string; aggregation_version: string; configuration_fingerprint: string; } export interface TraceHorizonNode { horizon_code: string; index_value: number; is_headline: boolean; active_routes_count: number; } export interface TraceRouteNode { route_id: string; route_index_value: number; point_contribution: number | null; dgca_weight: number; base_representative_fare: number; current_representative_fare: number; } export interface TraceObservationsNode { total_observations_queried: number; eligible_observations: number; rejection_rate_pct: number; } export interface TraceQualityNode { completeness_pct: number; fare_integrity_pct: number; rule_version: string; } export interface TraceExplanationNode { top_positive_driver: string; top_positive_points: number; top_negative_driver: string; top_negative_points: number; } export interface MeasurementTraceResponse { run_id: string; provenance_chain: string[]; index_run: TraceIndexRunNode; configuration: TraceConfigurationNode; horizons: TraceHorizonNode[]; routes: TraceRouteNode[]; observation_summary: TraceObservationsNode; quality_summary: TraceQualityNode; explanation_summary: TraceExplanationNode; canonical_run_fingerprint: string; manifest_sha256: string | null; }
