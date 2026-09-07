from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.proxy_route_weight import ProxyRouteWeight
from app.models.route import Route

DEMO_PROXY_WEIGHT_VERSION = "DGCA_PROXY_2026_V1"

DEMO_ROUTE_WEIGHT_SHARES: Dict[str, float] = {
    "DEL-BOM": 0.20,
    "BOM-DEL": 0.20,
    "DEL-BLR": 0.15,
    "BLR-DEL": 0.15,
    "BOM-BLR": 0.10,
    "DEL-CCU": 0.08,
    "BLR-HYD": 0.07,
    "MAA-DEL": 0.05
}

class ProxyWeightService:
    @classmethod
    def seed_demo_proxy_weights(cls, db: Session, version_id: str = DEMO_PROXY_WEIGHT_VERSION) -> List[ProxyRouteWeight]:
        """
        Seeds versioned DGCA-derived route-basket / traffic-share proxy weights for demo routes.
        """
        weights: List[ProxyRouteWeight] = []
        for route_id, share in DEMO_ROUTE_WEIGHT_SHARES.items():
            # Ensure route exists
            parts = route_id.split("-")
            r = db.query(Route).filter(Route.route_id == route_id).first()
            if not r:
                r = Route(
                    route_id=route_id,
                    origin_code=parts[0],
                    destination_code=parts[1],
                    directionality="OUTBOUND",
                    active=True
                )
                db.add(r)
                db.flush()

            w = db.query(ProxyRouteWeight).filter(
                ProxyRouteWeight.weight_version_id == version_id,
                ProxyRouteWeight.route_id == route_id
            ).first()

            if not w:
                w = ProxyRouteWeight(
                    weight_version_id=version_id,
                    route_id=route_id,
                    weight_share=share,
                    weight_type="DGCA_TRAFFIC_SHARE_PROXY",
                    is_demo=True,
                    source_metadata={"description": "DGCA Quarterly Traffic Volume Share Proxy (Demo)"}
                )
                db.add(w)
            else:
                w.weight_share = share
            weights.append(w)

        db.commit()
        return weights

    @classmethod
    def get_and_validate_weights(cls, db: Session, version_id: str = DEMO_PROXY_WEIGHT_VERSION) -> Dict[str, float]:
        """
        Retrieves route proxy weights and validates that they sum to 1.0 (within +-0.001 tolerance).
        Fails loudly with ValueError if weight sum is invalid.
        """
        weights = db.query(ProxyRouteWeight).filter(ProxyRouteWeight.weight_version_id == version_id).all()
        if not weights:
            # Seed default demo weights if absent
            weights = cls.seed_demo_proxy_weights(db, version_id)

        weight_map: Dict[str, float] = {w.route_id: float(w.weight_share) for w in weights}
        total_sum = sum(weight_map.values())

        if abs(total_sum - 1.0) > 0.001:
            raise ValueError(f"Invalid DGCA Proxy Weight Configuration '{version_id}': total weight sum is {total_sum:.6f}, which violates the required sum tolerance of 1.0 +- 0.001")

        return weight_map
