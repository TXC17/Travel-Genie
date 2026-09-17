"""
Spatial K-Means Day-Partitioning Clustering Engine.
Partitions candidate tourist attractions into geographically coherent sightseeing days (Day 1..K)
using local Equirectangular projection, adaptive K validation, deterministic k-means++,
and spatial dispersion analysis.
"""

import math
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from sklearn.cluster import KMeans

from app.models.attraction import Attraction
from app.schemas.clustering import (
    ClusterCentroidSchema,
    ClusterDaySchema,
    ExcludedAttractionSchema,
    ClusteringPartitionResponse,
)
from app.schemas.attraction import AttractionResponse


class SpatialDayClusterer:
    """
    Geographic day-partitioning engine.
    Projects WGS84 geographic coordinates onto a local metric tangent plane,
    applies adaptive K-Means++ clustering, and computes spatial coherence metrics.
    """

    EARTH_RADIUS_KM = 6371.0088
    DEFAULT_RANDOM_STATE = 42

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Great-Circle distance between two points on Earth in kilometers.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return SpatialDayClusterer.EARTH_RADIUS_KM * c

    @staticmethod
    def project_to_local_metric(
        coords: List[Tuple[float, float]], origin_lat: float, origin_lon: float
    ) -> np.ndarray:
        """
        Project WGS84 (latitude, longitude) coordinates onto a local Equirectangular tangent plane in kilometers.
        (x, y) coordinates represent distances in km east and north from origin (origin_lat, origin_lon).
        """
        phi0 = math.radians(origin_lat)
        lambda0 = math.radians(origin_lon)
        r = SpatialDayClusterer.EARTH_RADIUS_KM

        projected = []
        for lat, lon in coords:
            phi = math.radians(lat)
            lambda_val = math.radians(lon)
            # Equirectangular projection with mid-latitude cosine scaling
            x = r * (lambda_val - lambda0) * math.cos((phi + phi0) / 2.0)
            y = r * (phi - phi0)
            projected.append([x, y])

        return np.array(projected, dtype=float)

    @staticmethod
    def inverse_project(
        x: float, y: float, origin_lat: float, origin_lon: float
    ) -> Tuple[float, float]:
        """
        Inverse-project a local metric point (x, y) in kilometers back to geographic (latitude, longitude) in degrees.
        """
        phi0 = math.radians(origin_lat)
        lambda0 = math.radians(origin_lon)
        r = SpatialDayClusterer.EARTH_RADIUS_KM

        phi = phi0 + (y / r)
        cos_mid = math.cos((phi + phi0) / 2.0)
        if abs(cos_mid) < 1e-7:
            cos_mid = 1e-7
        lambda_val = lambda0 + (x / (r * cos_mid))

        lat_deg = math.degrees(phi)
        lon_deg = math.degrees(lambda_val)
        return lat_deg, lon_deg

    @staticmethod
    def validate_and_filter_attractions(
        attractions: List[Attraction],
    ) -> Tuple[List[Attraction], List[ExcludedAttractionSchema]]:
        """
        Validate coordinates and filter out invalid/null coordinate entities.
        """
        valid: List[Attraction] = []
        excluded: List[ExcludedAttractionSchema] = []

        for attr in attractions:
            lat = getattr(attr, "latitude", None)
            lon = getattr(attr, "longitude", None)

            if lat is None or lon is None:
                excluded.append(
                    ExcludedAttractionSchema(
                        attraction_id=str(attr.id),
                        name=str(attr.name),
                        reason="Coordinates are missing or null.",
                    )
                )
            elif not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                excluded.append(
                    ExcludedAttractionSchema(
                        attraction_id=str(attr.id),
                        name=str(attr.name),
                        reason=f"Coordinates ({lat}, {lon}) are out of valid WGS84 range.",
                    )
                )
            elif abs(lat) < 1e-5 and abs(lon) < 1e-5:
                excluded.append(
                    ExcludedAttractionSchema(
                        attraction_id=str(attr.id),
                        name=str(attr.name),
                        reason="Coordinates represent null island (0, 0).",
                    )
                )
            else:
                valid.append(attr)

        return valid, excluded

    def partition_days(
        self,
        destination_id: str,
        attractions: List[Attraction],
        requested_k: int,
    ) -> ClusteringPartitionResponse:
        """
        Execute deterministic spatial day partitioning with adaptive K validation.
        """
        # 1. Coordinate Validation
        valid_attractions, excluded = self.validate_and_filter_attractions(attractions)
        n_valid = len(valid_attractions)

        # 2. Adaptive K Validation & Guardrails
        if n_valid == 0:
            return ClusteringPartitionResponse(
                destination_id=destination_id,
                requested_k=requested_k,
                effective_k=0,
                is_k_adjusted=True,
                k_adjustment_reason="No valid candidate attractions available to cluster.",
                total_attractions=0,
                total_inertia_km2=0.0,
                clusters=[],
                excluded_attractions=excluded,
            )

        is_adjusted = False
        adjustment_reason = None
        effective_k = requested_k

        if n_valid < requested_k:
            effective_k = n_valid
            is_adjusted = True
            adjustment_reason = (
                f"Requested K={requested_k} days exceeds number of eligible attractions (N={n_valid}). "
                f"Adjusted effective K to {effective_k} (1 attraction per day)."
            )
        elif requested_k <= 0:
            effective_k = 1
            is_adjusted = True
            adjustment_reason = "Requested K was <= 0; adjusted effective K to 1."

        # 3. Coordinate Projection onto Local Tangent Plane
        raw_coords = [(attr.latitude, attr.longitude) for attr in valid_attractions]
        origin_lat = sum(c[0] for c in raw_coords) / n_valid
        origin_lon = sum(c[1] for c in raw_coords) / n_valid

        projected_points = self.project_to_local_metric(raw_coords, origin_lat, origin_lon)

        # 4. K-Means Execution
        if effective_k == 1:
            labels = np.zeros(n_valid, dtype=int)
            centroids_metric = np.array([projected_points.mean(axis=0)])
            total_inertia = float(np.sum((projected_points - centroids_metric[0]) ** 2))
        elif effective_k == n_valid:
            labels = np.arange(n_valid, dtype=int)
            centroids_metric = projected_points.copy()
            total_inertia = 0.0
        else:
            kmeans = KMeans(
                n_clusters=effective_k,
                init="k-means++",
                n_init=10,
                random_state=self.DEFAULT_RANDOM_STATE,
            )
            labels = kmeans.fit_predict(projected_points)
            centroids_metric = kmeans.cluster_centers_
            total_inertia = float(kmeans.inertia_)

        # 5. Build Cluster Day Schemas
        cluster_groups: Dict[int, List[Attraction]] = {i: [] for i in range(effective_k)}
        for idx, cluster_idx in enumerate(labels):
            cluster_groups[cluster_idx].append(valid_attractions[idx])

        # Sort clusters by geographic latitude (North to South) for natural day flow
        cluster_order = sorted(
            range(effective_k),
            key=lambda c_idx: centroids_metric[c_idx][1],
            reverse=True,
        )

        cluster_days: List[ClusterDaySchema] = []
        for day_num, c_idx in enumerate(cluster_order, start=1):
            members = cluster_groups[c_idx]
            c_x, c_y = centroids_metric[c_idx]
            c_lat, c_lon = self.inverse_project(c_x, c_y, origin_lat, origin_lon)

            # Compute spatial dispersion metrics
            distances_to_centroid = [
                self.haversine_distance_km(attr.latitude, attr.longitude, c_lat, c_lon)
                for attr in members
            ]
            avg_dist = float(np.mean(distances_to_centroid)) if distances_to_centroid else 0.0
            max_dist = float(np.max(distances_to_centroid)) if distances_to_centroid else 0.0

            # Max pairwise distance in cluster (dispersion)
            dispersion = 0.0
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    d_ij = self.haversine_distance_km(
                        members[i].latitude, members[i].longitude,
                        members[j].latitude, members[j].longitude,
                    )
                    if d_ij > dispersion:
                        dispersion = d_ij

            is_low_util = len(members) == 1
            util_note = (
                "Single attraction in this geographic zone; candidate for lighter sightseeing pace."
                if is_low_util else None
            )

            cluster_days.append(
                ClusterDaySchema(
                    day_number=day_num,
                    cluster_id=c_idx,
                    attraction_count=len(members),
                    centroid=ClusterCentroidSchema(
                        latitude=round(c_lat, 6),
                        longitude=round(c_lon, 6),
                    ),
                    avg_distance_to_centroid_km=round(avg_dist, 3),
                    max_distance_to_centroid_km=round(max_dist, 3),
                    dispersion_km=round(dispersion, 3),
                    is_low_utilization=is_low_util,
                    utilization_note=util_note,
                    attractions=[AttractionResponse.model_validate(m) for m in members],
                )
            )

        return ClusteringPartitionResponse(
            destination_id=destination_id,
            requested_k=requested_k,
            effective_k=effective_k,
            is_k_adjusted=is_adjusted,
            k_adjustment_reason=adjustment_reason,
            total_attractions=n_valid,
            total_inertia_km2=round(total_inertia, 3),
            clusters=cluster_days,
            excluded_attractions=excluded,
        )
