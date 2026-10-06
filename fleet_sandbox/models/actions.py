"""Action Space Definitions for Fleet Tactical Sandbox
References: SPEC v1.0 Section 4.0
- 17 Move Actions (1 STOP, 8 SLOW, 8 FAST)
- 4 Attack Actions (FRONT, REAR, LEFT, RIGHT, plus NONE)
- Recon & Rotation interfaces preserved for future expansion
"""

from enum import IntEnum
from typing import Dict, Tuple, Optional


class MoveAction(IntEnum):
    STOP = 0
    # SLOW (1.0 units/sec)
    SLOW_E = 1    # 0 deg
    SLOW_NE = 2   # 45 deg
    SLOW_N = 3    # 90 deg
    SLOW_NW = 4   # 135 deg
    SLOW_W = 5    # 180 deg
    SLOW_SW = 6   # 225 deg
    SLOW_S = 7    # 270 deg
    SLOW_SE = 8   # 315 deg
    # FAST (2.0 units/sec)
    FAST_E = 9    # 0 deg
    FAST_NE = 10  # 45 deg
    FAST_N = 11   # 90 deg
    FAST_NW = 12  # 135 deg
    FAST_W = 13   # 180 deg
    FAST_SW = 14  # 225 deg
    FAST_S = 15   # 270 deg
    FAST_SE = 16  # 315 deg


# Mapping of move action to (target_speed, target_angle_deg or None)
MOVE_ACTION_DATA: Dict[MoveAction, Tuple[float, Optional[float]]] = {
    MoveAction.STOP: (0.0, None),
    MoveAction.SLOW_E: (1.0, 0.0),
    MoveAction.SLOW_NE: (1.0, 45.0),
    MoveAction.SLOW_N: (1.0, 90.0),
    MoveAction.SLOW_NW: (1.0, 135.0),
    MoveAction.SLOW_W: (1.0, 180.0),
    MoveAction.SLOW_SW: (1.0, 225.0),
    MoveAction.SLOW_S: (1.0, 270.0),
    MoveAction.SLOW_SE: (1.0, 315.0),
    MoveAction.FAST_E: (2.0, 0.0),
    MoveAction.FAST_NE: (2.0, 45.0),
    MoveAction.FAST_N: (2.0, 90.0),
    MoveAction.FAST_NW: (2.0, 135.0),
    MoveAction.FAST_W: (2.0, 180.0),
    MoveAction.FAST_SW: (2.0, 225.0),
    MoveAction.FAST_S: (2.0, 270.0),
    MoveAction.FAST_SE: (2.0, 315.0),
}


class AttackAction(IntEnum):
    NONE = 0
    FRONT = 1  # heading ± 45°
    REAR = 2   # heading + 180° ± 45°
    LEFT = 3   # heading + 90° ± 45° (포구 좌현)
    RIGHT = 4  # heading - 90° ± 45° (포구 우현)


# Relative bearing offset for attack actions
ATTACK_BEARING_OFFSET_DEG: Dict[AttackAction, float] = {
    AttackAction.NONE: 0.0,
    AttackAction.FRONT: 0.0,
    AttackAction.REAR: 180.0,
    AttackAction.LEFT: 90.0,
    AttackAction.RIGHT: -90.0,
}


# Reserved for future expansion (SPEC 4.3)
class ReconAction(IntEnum):
    NONE = 0
    RECON_N = 1
    RECON_NE = 2
    RECON_E = 3
    RECON_SE = 4
    RECON_S = 5
    RECON_SW = 6
    RECON_W = 7
    RECON_NW = 8


class TurnAction(IntEnum):
    NONE = 0
    TURN_0 = 1
    TURN_45 = 2
    TURN_90 = 3
    TURN_135 = 4
    TURN_180 = 5
    TURN_225 = 6
    TURN_270 = 7
    TURN_315 = 8
