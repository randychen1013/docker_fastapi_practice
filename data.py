from enum import Enum, IntEnum
from typing import Optional

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from typing_extensions import Self

TRACK_HISTORY_MAX_LENGTH = 5
MISS_FRAMES_MAX_NUM = 3

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 384


# ====================== 共用設定 ======================


class ApiModel(BaseModel):
    """所有 API Model 的共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class CameraId(IntEnum):
    CAM_21 = 21
    CAM_22 = 22
    CAM_23 = 23
    CAM_24 = 24
    CAM_25 = 25
    CAM_26 = 26
    CAM_27 = 27
    CAM_28 = 28


class RiskType(str, Enum):
    HAZARD = "hazard"
    SAFE = "safe"


class TrackType(str, Enum):
    VEHICLE = "vehicle"
    PEDESTRIAN = "pedestrian"


# ====================== Bounding Box ======================


class ImageBBox(ApiModel):
    """原始鏡頭影像上的物件框，採半開區間 [min, max)。"""

    x_min: int = Field(
        ge=0,
        lt=IMAGE_WIDTH,
        description="左上角 x 座標",
    )
    y_min: int = Field(
        ge=0,
        lt=IMAGE_HEIGHT,
        description="左上角 y 座標",
    )
    x_max: int = Field(
        gt=0,
        le=IMAGE_WIDTH,
        description="右下角 x 座標，不包含此位置",
    )
    y_max: int = Field(
        gt=0,
        le=IMAGE_HEIGHT,
        description="右下角 y 座標，不包含此位置",
    )

    @model_validator(mode="after")
    def validate_coordinates(self) -> Self:
        if self.x_min >= self.x_max:
            raise ValueError("x_min 必須小於 x_max")

        if self.y_min >= self.y_max:
            raise ValueError("y_min 必須小於 y_max")

        return self


class BevBBox(ApiModel):
    """
    BEV 座標系統上的物件框。

    必須在 API 文件另外固定：
    1. 座標單位是 pixel 還是 cm
    2. 原點位置
    3. x、y 軸方向
    """

    x_min: float = Field(description="BEV 左上角 x 座標")
    y_min: float = Field(description="BEV 左上角 y 座標")
    x_max: float = Field(description="BEV 右下角 x 座標")
    y_max: float = Field(description="BEV 右下角 y 座標")

    @model_validator(mode="after")
    def validate_coordinates(self) -> Self:
        if self.x_min >= self.x_max:
            raise ValueError("x_min 必須小於 x_max")

        if self.y_min >= self.y_max:
            raise ValueError("y_min 必須小於 y_max")

        return self


# ====================== API Input ======================


class Detection(ApiModel):
    """單一 YOLO 偵測結果。"""

    detection_id: Optional[str] = Field(
        default=None,
        description="呼叫端產生的偵測框識別碼",
    )
    cls_name: str = Field(
        min_length=1,
        max_length=64,
        description="物件分類名稱",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="偵測信心值，範圍為 0 到 1",
    )
    bbox: ImageBBox


class CameraFrame(ApiModel):
    """單一鏡頭在目前影格中的偵測資料。"""

    cam_id: CameraId
    objects: list[Detection] = Field(
        default_factory=list,
        description="此鏡頭目前影格中的所有偵測結果",
    )


class InputData(ApiModel):
    """成大辨識 API 的輸入資料。"""

    timestamp: AwareDatetime = Field(
        description="影格時間，ISO 8601 格式且必須包含時區",
    )
    frame_count: int = Field(
        ge=0,
        description="目前工作階段內單調遞增的影格編號",
    )
    cam_data: list[CameraFrame] = Field(
        min_length=1,
        max_length=8,
        description="各鏡頭目前影格的偵測資料",
    )

    @model_validator(mode="after")
    def validate_camera_ids(self) -> Self:
        camera_ids = [camera.cam_id for camera in self.cam_data]

        if len(camera_ids) != len(set(camera_ids)):
            raise ValueError("cam_data 不可包含重複的 cam_id")

        return self


# ====================== API Output ======================


class CameraProjection(ApiModel):
    """
    LfD 結果投影到原始鏡頭後的物件框。

    此 bbox 不保證和輸入 Detection 的 bbox 一一對應。
    """

    cam_id: CameraId
    bbox: ImageBBox


class LfdObservation(ApiModel):
    """單一追蹤物件在某個影格的 LfD 結果。"""

    timestamp: AwareDatetime = Field(
        description="此追蹤點對應的時間",
    )
    frame_count: int = Field(
        ge=0,
        description="此追蹤點對應的影格編號",
    )
    bev_bbox: BevBBox
    camera_projections: list[CameraProjection] = Field(
        default_factory=list,
        description="LfD 結果投影至各鏡頭的物件框",
    )
    missed_frames: int = Field(
        ge=0,
        le=MISS_FRAMES_MAX_NUM,
        description=(
            "0 表示此幀有實際追蹤結果；" "1 到 3 表示已連續漏追的影格數並使用預測結果"
        ),
    )


class MotionVector(ApiModel):
    """追蹤物件在 BEV 座標系統中的運動向量。"""

    dx: float = Field(
        description="x 軸方向位移或速度",
    )
    dy: float = Field(
        description="y 軸方向位移或速度",
    )
    unit: str = Field(
        description="向量單位，例如 pixel/frame 或 cm/s",
    )


class TrackData(ApiModel):
    """一個物件的追蹤結果。"""

    track_id: int = Field(
        ge=0,
        description="目前工作階段內唯一的追蹤編號",
    )
    track_type: TrackType
    motion: MotionVector
    history: list[LfdObservation] = Field(
        min_length=1,
        max_length=TRACK_HISTORY_MAX_LENGTH,
        description="由舊到新排列的追蹤歷史，最多保留 5 筆",
    )


class RiskAssessment(ApiModel):
    """一組人車追蹤物件的風險評估結果。"""

    risk_type: RiskType
    distance_cm: float = Field(
        ge=0,
        allow_inf_nan=False,
        description="人與車的距離，單位為公分",
    )
    vehicle_track_id: int = Field(
        ge=0,
        description="車輛追蹤編號",
    )
    pedestrian_track_id: int = Field(
        ge=0,
        description="行人追蹤編號",
    )


class OutputData(ApiModel):
    """成大辨識 API 的輸出資料。"""

    timestamp: AwareDatetime = Field(
        description="本次辨識結果時間，ISO 8601 格式且必須包含時區",
    )
    frame_count: int = Field(
        ge=0,
        description="對應輸入資料的影格編號",
    )
    tracks: list[TrackData] = Field(
        default_factory=list,
        description="目前有效的追蹤物件",
    )
    risk_assessments: list[RiskAssessment] = Field(
        default_factory=list,
        description="目前所有人車配對的風險評估",
    )

    @model_validator(mode="after")
    def validate_track_references(self) -> Self:
        track_map: dict[int, TrackData] = {}

        for track in self.tracks:
            if track.track_id in track_map:
                raise ValueError(f"track_id 不可重複：{track.track_id}")

            track_map[track.track_id] = track

        for assessment in self.risk_assessments:
            vehicle = track_map.get(assessment.vehicle_track_id)
            pedestrian = track_map.get(assessment.pedestrian_track_id)

            if vehicle is None:
                raise ValueError(
                    "vehicle_track_id 找不到對應的追蹤物件："
                    f"{assessment.vehicle_track_id}"
                )

            if pedestrian is None:
                raise ValueError(
                    "pedestrian_track_id 找不到對應的追蹤物件："
                    f"{assessment.pedestrian_track_id}"
                )

            if vehicle.track_type != TrackType.VEHICLE:
                raise ValueError("vehicle_track_id 指向的物件不是 vehicle")

            if pedestrian.track_type != TrackType.PEDESTRIAN:
                raise ValueError("pedestrian_track_id 指向的物件不是 pedestrian")

        return self
