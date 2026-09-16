import axios from 'axios';
import {
  IndexDashboardResponse,
  IndexExplanationResponse,
  IndexAuditResponse,
  SimpleIndexRun,
  ObservationExplorerResponse,
  RouteIntelligenceResponse,
  HorizonIntelligenceResponse,
  DataQualitySummaryResponse,
  DataQualityRoutesResponse,
  DataQualitySourcesResponse,
  MethodologyInfoResponse,
  PublicationReadinessResponse,
  ValidationBenchmark,
  ValidationRun,
  ValidationMetric,
  AeroGuideAnalyzeRequest,
  AeroGuideAnalyzeResponse,
  ForecastingReadinessResponse,
  RouteUniverseItem,
  AirlineRegistryItem,
  SourceCapabilityItem,
  SourceHealthItem,
  RouteCoverageItem
} from '../types';

const API_BASE = '/api/v1';

export interface ObservationExplorerParams {
  run_id?: string;
  collection_date?: string;
  route_id?: string;
  origin?: string;
  destination?: string;
  horizon?: number;
  source?: string;
  carrier?: string;
  cabin?: string;
  validation_status?: string;
  index_eligibility?: string;
  page?: number;
  page_size?: number;
}

export const fetchDashboard = async (runId: string): Promise<IndexDashboardResponse> => {
  const response = await axios.get<IndexDashboardResponse>(`${API_BASE}/index-runs/${runId}/dashboard`);
  return response.data;
};

export const fetchExplanation = async (runId: string): Promise<IndexExplanationResponse> => {
  const response = await axios.get<IndexExplanationResponse>(`${API_BASE}/index-runs/${runId}/explanation`);
  return response.data;
};

export const fetchAudit = async (runId: string): Promise<IndexAuditResponse> => {
  const response = await axios.get<IndexAuditResponse>(`${API_BASE}/index-runs/${runId}/audit`);
  return response.data;
};

export const fetchIndexRuns = async (): Promise<SimpleIndexRun[]> => {
  const response = await axios.get<SimpleIndexRun[]>(`${API_BASE}/index-runs`);
  return response.data;
};

export const fetchObservationExplorer = async (
  params: ObservationExplorerParams = {}
): Promise<ObservationExplorerResponse> => {
  const response = await axios.get<ObservationExplorerResponse>(`${API_BASE}/observations/explorer`, {
    params,
  });
  return response.data;
};

export const fetchRouteIntelligence = async (
  routeId: string,
  runId?: string
): Promise<RouteIntelligenceResponse> => {
  const response = await axios.get<RouteIntelligenceResponse>(
    `${API_BASE}/routes/${routeId}/intelligence`,
    { params: { run_id: runId } }
  );
  return response.data;
};

export const fetchHorizonsIntelligence = async (
  runId?: string
): Promise<HorizonIntelligenceResponse[]> => {
  const response = await axios.get<HorizonIntelligenceResponse[]>(
    `${API_BASE}/horizons`,
    { params: { run_id: runId } }
  );
  return response.data;
};

export const fetchDataQualitySummary = async (
  runId?: string
): Promise<DataQualitySummaryResponse> => {
  const response = await axios.get<DataQualitySummaryResponse>(
    `${API_BASE}/data-quality/summary`,
    { params: { run_id: runId } }
  );
  return response.data;
};

export const fetchDataQualityRoutes = async (
  runId?: string
): Promise<DataQualityRoutesResponse> => {
  const response = await axios.get<DataQualityRoutesResponse>(
    `${API_BASE}/data-quality/routes`,
    { params: { run_id: runId } }
  );
  return response.data;
};

export const fetchDataQualitySources = async (
  runId?: string
): Promise<DataQualitySourcesResponse> => {
  const response = await axios.get<DataQualitySourcesResponse>(
    `${API_BASE}/data-quality/sources`,
    { params: { run_id: runId } }
  );
  return response.data;
};

export const fetchMethodologyConfiguration = async (
  version?: string
): Promise<MethodologyInfoResponse> => {
  const endpoint = version
    ? `${API_BASE}/methodology/${encodeURIComponent(version)}`
    : `${API_BASE}/methodology/current`;
  const response = await axios.get<MethodologyInfoResponse>(endpoint);
  return response.data;
};

export const fetchPublicationReadiness = async (
  runId: string
): Promise<PublicationReadinessResponse> => {
  const response = await axios.get<PublicationReadinessResponse>(
    `${API_BASE}/index-runs/${runId}/publication-readiness`
  );
  return response.data;
};

export const fetchValidationBenchmarks = async (): Promise<ValidationBenchmark[]> => {
  const response = await axios.get<ValidationBenchmark[]>(
    `${API_BASE}/validation-lab/benchmarks`
  );
  return response.data;
};

export const fetchValidationRun = async (
  runId: string
): Promise<ValidationRun> => {
  const response = await axios.get<ValidationRun>(
    `${API_BASE}/validation-lab/runs/${runId}`
  );
  return response.data;
};

export const fetchValidationMetrics = async (
  runId?: string
): Promise<ValidationMetric | null> => {
  const response = await axios.get<ValidationMetric | null>(
    `${API_BASE}/validation-lab/metrics`,
    { params: { run_id: runId } }
  );
  return response.data;
};

export const fetchIndexExplanation = async (runId: string) => { 
  const response = await axios.get(`${API_BASE}/index-runs/${runId}/explanation`); 
  return response.data; 
}; 
export const fetchIndexAudit = async (runId: string) => { 
  const response = await axios.get(`${API_BASE}/index-runs/${runId}/audit`); 
  return response.data; 
}; 
export const fetchMeasurementTrace = async (runId: string) => { 
  const response = await axios.get(`${API_BASE}/index-runs/${runId}/trace`); 
  return response.data; 
};

// ==========================================
// AeroGuide Consumer Intelligence APIs
// ==========================================

export const analyzeAirfare = async (payload: AeroGuideAnalyzeRequest): Promise<AeroGuideAnalyzeResponse> => {
  const response = await axios.post<AeroGuideAnalyzeResponse>(`${API_BASE}/aeroguide/analyze`, payload);
  return response.data;
};

export const fetchForecastingReadiness = async (): Promise<ForecastingReadinessResponse> => {
  const response = await axios.get<ForecastingReadinessResponse>(`${API_BASE}/aeroguide/readiness`);
  return response.data;
};

export const fetchRouteUniverse = async (tier?: string): Promise<RouteUniverseItem[]> => {
  const response = await axios.get<RouteUniverseItem[]>(`${API_BASE}/aeroguide/routes`, {
    params: { tier }
  });
  return response.data;
};

export const fetchAirlines = async (): Promise<AirlineRegistryItem[]> => {
  const response = await axios.get<AirlineRegistryItem[]>(`${API_BASE}/aeroguide/airlines`);
  return response.data;
};

export const fetchSourceCapabilities = async (): Promise<SourceCapabilityItem[]> => {
  const response = await axios.get<SourceCapabilityItem[]>(`${API_BASE}/aeroguide/sources`);
  return response.data;
};

export const fetchSourceHealth = async (): Promise<SourceHealthItem[]> => {
  const response = await axios.get<SourceHealthItem[]>(`${API_BASE}/aeroguide/source-health`);
  return response.data;
};

export const fetchModelStatus = async () => {
  const response = await axios.get(`${API_BASE}/aeroguide/model-status`);
  return response.data;
};

export const fetchCollectionStatus = async () => {
  const response = await axios.get(`${API_BASE}/aeroguide/collection-status`);
  return response.data;
};

export const fetchTrajectoryDetail = async (routeId: string, travelDate: string) => {
  const response = await axios.get(`${API_BASE}/aeroguide/trajectories/${routeId}/${travelDate}`);
  return response.data;
};

export const fetchMarketState = async (runId?: string) => {
  const response = await axios.get(`${API_BASE}/aeroguide/market-state`, {
    params: { run_id: runId }
  });
  return response.data;
};

export const fetchWhatChanged = async (runId?: string) => {
  const response = await axios.get(`${API_BASE}/aeroguide/what-changed`, {
    params: { run_id: runId }
  });
  return response.data;
};

export const fetchCollectionRuns = async (limit = 20) => {
  const response = await axios.get(`${API_BASE}/aeroguide/collection-runs`, {
    params: { limit }
  });
  return response.data;
};

export const fetchModelEvaluation = async () => {
  const response = await axios.get(`${API_BASE}/aeroguide/model-evaluation`);
  return response.data;
};

export const fetchRouteCoverage = async (): Promise<RouteCoverageItem[]> => {
  const response = await axios.get<RouteCoverageItem[]>(`${API_BASE}/aeroguide/route-coverage`);
  return response.data;
};

