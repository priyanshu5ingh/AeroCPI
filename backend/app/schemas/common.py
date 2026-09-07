from enum import Enum

class DataStatus(str, Enum):
    OBSERVED = "OBSERVED"
    FROZEN = "FROZEN"
    OFFICIAL = "OFFICIAL"
    SYNTHETIC = "SYNTHETIC"
    DEMO = "DEMO"

class OutlierStatus(str, Enum):
    VALID = "VALID"
    OUTLIER_FLAGGED = "OUTLIER_FLAGGED"
    EXCLUDED = "EXCLUDED"
    RETAINED_WITH_WARNING = "RETAINED_WITH_WARNING"

VALID_HORIZONS = {1, 7, 15, 30, 45}
