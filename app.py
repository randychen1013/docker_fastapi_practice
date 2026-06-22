from math import hypot

from fastapi import FastAPI

from data import (
    BevBBox,
    CameraProjection,
    InputData,
    LfdObservation,
    MotionVector,
    OutputData,
    RiskAssessment,
    RiskType,
    TrackData,
    TrackType,
)


app = FastAPI(title="Mock Tracking API")


def _track_type(cls_name: str) -> TrackType:
    """Treat person-like labels as pedestrians and all others as vehicles."""
    if cls_name.lower() in {"person", "pedestrian"}:
        return TrackType.PEDESTRIAN
    return TrackType.VEHICLE


def mock_input_to_output(input_data: InputData) -> OutputData:
    """Build deterministic mock tracking output from the supplied detections."""
    tracks: list[TrackData] = []

    for camera in input_data.cam_data:
        for detection in camera.objects:
            bbox = detection.bbox
            track_id = len(tracks)
            tracks.append(
                TrackData(
                    track_id=track_id,
                    track_type=_track_type(detection.cls_name),
                    motion=MotionVector(dx=0.0, dy=0.0, unit="pixel/frame"),
                    history=[
                        LfdObservation(
                            timestamp=input_data.timestamp,
                            frame_count=input_data.frame_count,
                            bev_bbox=BevBBox(
                                x_min=float(bbox.x_min),
                                y_min=float(bbox.y_min),
                                x_max=float(bbox.x_max),
                                y_max=float(bbox.y_max),
                            ),
                            camera_projections=[
                                CameraProjection(cam_id=camera.cam_id, bbox=bbox)
                            ],
                            missed_frames=0,
                        )
                    ],
                )
            )

    vehicles = [track for track in tracks if track.track_type == TrackType.VEHICLE]
    pedestrians = [
        track for track in tracks if track.track_type == TrackType.PEDESTRIAN
    ]
    risk_assessments: list[RiskAssessment] = []

    for vehicle in vehicles:
        vehicle_box = vehicle.history[-1].bev_bbox
        vehicle_center = (
            (vehicle_box.x_min + vehicle_box.x_max) / 2,
            (vehicle_box.y_min + vehicle_box.y_max) / 2,
        )
        for pedestrian in pedestrians:
            pedestrian_box = pedestrian.history[-1].bev_bbox
            pedestrian_center = (
                (pedestrian_box.x_min + pedestrian_box.x_max) / 2,
                (pedestrian_box.y_min + pedestrian_box.y_max) / 2,
            )
            distance = hypot(
                vehicle_center[0] - pedestrian_center[0],
                vehicle_center[1] - pedestrian_center[1],
            )
            risk_assessments.append(
                RiskAssessment(
                    risk_type=RiskType.HAZARD if distance < 100 else RiskType.SAFE,
                    distance_cm=distance,
                    vehicle_track_id=vehicle.track_id,
                    pedestrian_track_id=pedestrian.track_id,
                )
            )

    return OutputData(
        timestamp=input_data.timestamp,
        frame_count=input_data.frame_count,
        tracks=tracks,
        risk_assessments=risk_assessments,
    )


@app.post("/mock", response_model=OutputData)
def mock_tracking(input_data: InputData) -> OutputData:
    return mock_input_to_output(input_data)
