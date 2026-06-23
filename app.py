import random

from fastapi import FastAPI

from data import (
    BevBBox,
    CameraId,
    CameraProjection,
    ImageBBox,
    InputData,
    LfdObservation,
    MotionVector,
    ObjectType,
    OutputData,
    RiskAssessment,
    RiskType,
    TrackData,
)

app = FastAPI(title="Mock Tracking API")

VEHICLE_TYPES = [ObjectType.TRUCK, ObjectType.FORKLIFT, ObjectType.CAR]

def random_image_bbox() -> ImageBBox:
    width = random.randint(40, 120)
    height = random.randint(50, 140)
    x_min = random.randint(0, 640 - width)
    y_min = random.randint(0, 384 - height)

    return ImageBBox(
        x_min=x_min,
        y_min=y_min,
        x_max=x_min + width,
        y_max=y_min + height,
    )


def random_camera_projection(cam_id: CameraId) -> CameraProjection:
    bbox = random_image_bbox()
    return CameraProjection(cam_id=cam_id, bbox=bbox)


def random_lfd_observation() -> LfdObservation:
    bev_bbox = BevBBox(
        x_center=random.uniform(0, 640),
        y_center=random.uniform(0, 384),
        width=random.uniform(20, 100),
        height=random.uniform(20, 100),
        rotation=random.uniform(-180, 180),
    )

    cam_ids = random.choices(list(CameraId), k=random.randint(1, 3))
    camera_projections = [random_camera_projection(cam_id) for cam_id in cam_ids]
    return LfdObservation(bev_bbox=bev_bbox, camera_projections=camera_projections, missed_frames=random.randint(0, 2))

def random_track_data(track_id: int, object_type: ObjectType) -> TrackData:

    motion = MotionVector(
        dx=random.uniform(-6, 6),
        dy=random.uniform(-6, 6),
        unit="m/s",
    )
    history = [random_lfd_observation() for _ in range(random.randint(1, 5))]

    return TrackData(
        track_id=track_id,
        object_type=object_type,
        motion=motion,
        history=history,
    )

def random_risk_assessment(vehicle_track_id: int, person_track_id: int) -> RiskAssessment:
    return RiskAssessment(
        risk_type=random.choice(list(RiskType)),
        distance_cm=random.uniform(10, 500),
        vehicle_track_id=vehicle_track_id,
        person_track_id=person_track_id,
    )

def random_output_data(input_data: InputData) -> OutputData:

    vehicles = [random_track_data(track_id, random.choice(VEHICLE_TYPES)) for track_id in range(2)]
    persons = [random_track_data(track_id, ObjectType.PERSON) for track_id in range(2,4)]
    tracks = vehicles + persons

    risk_pairs = [(vehicle, person) for vehicle in vehicles for person in persons]
    selected_pairs = random.sample(risk_pairs, k=3)
    risk_assessments = [
        random_risk_assessment(vehicle.track_id, person.track_id)
        for vehicle, person in selected_pairs
    ]

    return OutputData(
        timestamp=input_data.timestamp,
        frame_count=input_data.frame_count,
        tracks=tracks,
        risk_assessments=risk_assessments,
    )



@app.post("/mock", response_model=OutputData)
def mock_tracking(input_data: InputData) -> OutputData:
    return random_output_data(input_data)


def process_input_data(input_data: InputData) -> OutputData:
    """Randomly build OutputData with vehicle/person tracks and three risks."""
    return random_output_data(input_data)
