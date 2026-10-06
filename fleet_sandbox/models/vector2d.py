"""2D Continuous Vector Mathematics for Fleet Tactical Sandbox
References: SPEC v1.0 Section 2.1 & 2.2
"""

import math
from dataclasses import dataclass


def normalize_angle_deg(angle: float) -> float:
    """Normalize angle to [0, 360) degrees."""
    a = angle % 360.0
    return a if a >= 0.0 else a + 360.0


def shortest_angular_difference_deg(target_angle: float, current_angle: float) -> float:
    """
    Calculate shortest signed angle difference from current_angle to target_angle.
    Result in range [-180, 180]. Positive means counter-clockwise (turn left),
    Negative means clockwise (turn right).
    """
    diff = (target_angle - current_angle + 180.0) % 360.0 - 180.0
    return diff


@dataclass(frozen=True)
class Vector2D:
    x: float
    y: float

    def __add__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2D":
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2D":
        return Vector2D(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vector2D":
        if scalar == 0.0:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / scalar, self.y / scalar)

    @property
    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    @property
    def length(self) -> float:
        return math.sqrt(self.length_sq)

    def distance_to(self, other: "Vector2D") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def normalized(self) -> "Vector2D":
        l = self.length
        if l < 1e-9:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / l, self.y / l)

    def dot(self, other: "Vector2D") -> float:
        return self.x * other.x + self.y * other.y

    def rotate_deg(self, angle_degrees: float) -> "Vector2D":
        """
        Rotate vector by angle_degrees counter-clockwise using 2D rotation matrix:
        [ cos(θ)  -sin(θ) ]
        [ sin(θ)   cos(θ) ]
        """
        rad = math.radians(angle_degrees)
        cos_val = math.cos(rad)
        sin_val = math.sin(rad)
        new_x = self.x * cos_val - self.y * sin_val
        new_y = self.x * sin_val + self.y * cos_val
        return Vector2D(new_x, new_y)

    @property
    def angle_deg(self) -> float:
        """Angle in degrees [0, 360) measured counter-clockwise from +X axis."""
        rad = math.atan2(self.y, self.x)
        deg = math.degrees(rad)
        return normalize_angle_deg(deg)
