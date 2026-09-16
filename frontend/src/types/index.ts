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

// ==========================================
// AeroGuide Consumer Airfare Intelligence Types
// ==========================================

export interface AirlineAlternative {
  carrier_code: string;
  airline_name: string;
  observed_fare: number;
  currency: string;
  stops: number;
  duration_minutes: number;
  source_id: string;
  source_evidence: string;
  source_state: string;
  is_direct_airline: boolean;
  current_position: 'LOW' | 'TYPICAL' | 'HIGH' | string;
  departure_time?: string | null;
  observation_id?: string | null;
}

export interface FlexibleDateOption {
  travel_date: string;
  days_diff: number;
  observed_fare: number;
  difference_from_requested: number;
  percent_difference: number;
  carrier_code: string;
  stops: number;
  source_evidence: string;
  is_lower_fare: boolean;
  label: string;
}

export interface DecisionTraceNode {
  stage_number: number;
  stage_name: string;
  status: 'VERIFIED' | 'PASSED' | 'COLLECTED' | 'EVALUATED' | 'DECIDED' | string;
  evidence_summary: string;
  structured_payload: Record<string, any>;
}

export interface GroundedExplanation {
  headline?: string;
  market_context?: string;
  carrier_comparison?: string;
  timing_recommendation?: string;
  evidence_anchor?: Record<string, any>;
}

export interface LongitudinalReadinessInfo {
  dataset_classification: string;
  model_training_status: string;
  required_target_pairs: number;
  current_target_pairs: number;
}

export interface AeroGuideAnalyzeRequest {
  origin: string;
  destination: string;
  travel_date: string;
  flexibility_days?: number;
  priority?: 'CHEAPEST' | 'FASTEST' | string;
  adults?: number;
  cabin?: string;
  currency?: string;
}

export interface AeroGuideAnalyzeResponse {
  request_id: string;
  origin: string;
  destination: string;
  route_id: string;
  travel_date: string;
  days_to_departure: number;
  current_observed_fare: number;
  currency: string;
  price_position: 'LOW' | 'TYPICAL' | 'HIGH' | 'INSUFFICIENT_DATA' | string;
  route_historical_median: number;
  route_historical_min: number;
  route_historical_max: number;
  observations_in_sample: number;
  model_outlook_status: string;
  model_probabilities?: Record<string, number> | null;
  model_outlook_message: string;
  booking_guidance: 'BOOK' | 'WAIT' | 'WATCH' | 'FLEX_DATE' | 'INSUFFICIENT_DATA' | string;
  guidance_reason: string;
  decision_policy_version: string;
  airline_alternatives: AirlineAlternative[];
  flexible_dates: FlexibleDateOption[];
  sources_available: string[];
  decision_trace: DecisionTraceNode[];
  grounded_explanation: string;
  longitudinal_readiness: LongitudinalReadinessInfo;
}

export interface ForecastingReadinessResponse {
  dataset_classification: string;
  model_training_status: string;
  total_observations: number;
  unique_routes: number;
  unique_travel_dates: number;
  unique_search_dates: number;
  longitudinal_pairs_count: number;
  repeated_trajectories: number;
  trajectories_with_gte_3_searches: number;
  seven_day_target_pairs: number;
  fourteen_day_target_pairs: number;
  longest_history_days: number;
  source_coverage: string[];
  airline_coverage: string[];
  overall_readiness: string;
  readiness_notes: string;
  required_collection_schedule: {
    pinned_travel_dates: number;
    routes_per_run: number;
    consecutive_collection_days_required: number;
    target_observations_required: number;
  };
}

export interface RouteUniverseItem {
  route_id: string;
  origin: string;
  destination: string;
  city_pair: string;
  tier: 'TIER_1_DGCA_CORE' | 'TIER_2_NATIONAL_HIGH_TRAFFIC' | 'TIER_3_REGIONAL_CONNECTIVITY' | 'TIER_4_DYNAMIC_DISCOVERY' | string;
  is_cpi_basket_member: boolean;
  description: string;
}

export interface AirlineRegistryItem {
  airline_id: string;
  iata_code: string;
  name: string;
  official_api_available: boolean;
  ndc_available: boolean;
  ndc_portal_url: string | null;
  api_access_type: string;
  requires_authentication: boolean;
  partner_restriction: boolean;
  documented_endpoints: string[];
  observable_content: string[];
  is_documented: boolean;
  is_accessible: boolean;
  is_actually_collected: boolean;
  is_currently_observed: boolean;
  verification_source: string;
  verification_status: string;
}

export interface SourceCapabilityItem {
  source_id: string;
  source_name: string;
  source_type: string;
  access_status: string;
  is_public_unrestricted: boolean;
  fare_breakdown_supported: boolean;
  health_status: string;
  availability_rate: number;
  median_response_time_ms: number | null;
}

export interface SourceHealthItem {
  source_id: string;
  source_name: string;
  health_status: string;
  availability_rate: number;
  median_response_time_ms: number | null;
}

export interface CarrierQuotePoint {
  carrier_code: string;
  airline_name: string;
  fare: number;
  stops: number;
  duration_minutes: number;
}

export interface TrajectorySearchPoint {
  search_date: string;
  search_timestamp: string | null;
  days_to_departure: number;
  median_fare: number;
  min_fare: number;
  max_fare: number;
  carrier_quotes: CarrierQuotePoint[];
}

export interface MatchedCarrierTarget {
  carrier_code: string;
  airline_name: string;
  prediction_fare: number;
  future_fare: number;
  delta_fare: number;
  delta_pct: number;
  direction: 'UP' | 'DOWN' | 'STABLE' | string;
}

export interface TrajectoryTargetEvaluation {
  prediction_search_date: string;
  future_search_date: string;
  days_gap: number;
  is_valid_7d_target: boolean;
  is_valid_14d_target: boolean;
  prediction_median_fare: number;
  future_median_fare: number;
  delta_fare: number;
  delta_pct: number;
  direction: 'UP' | 'DOWN' | 'STABLE' | string;
  market_target?: {
    prediction_median: number;
    future_median: number;
    delta_fare: number;
    delta_pct: number;
    direction: string;
  };
  carrier_composition_status: 'IDENTICAL' | 'PARTIAL_OVERLAP' | 'DISJOINT' | string;
  matched_carriers_count: number;
  matched_carrier_mean_delta_fare: number | null;
  matched_carrier_mean_delta_pct: number | null;
  matched_carrier_targets: MatchedCarrierTarget[];
}

export interface TrajectoryDetailResponse {
  route_id: string;
  origin: string;
  destination: string;
  travel_date: string;
  search_dates_count: number;
  observations_count: number;
  search_points: TrajectorySearchPoint[];
  target_evaluations: TrajectoryTargetEvaluation[];
  has_7_day_pair: boolean;
  status: string;
}

export interface RouteCoverageItem {
  route_id: string;
  origin: string;
  destination: string;
  tier: string;
  description: string;
  is_cpi_basket_member: boolean;
  airlines_observed: string[];
  sources_configured: string[];
  sources_accessible: string[];
  sources_collected: string[];
  observations_count: number;
  last_collection: string | null;
  coverage_status: string;
}

