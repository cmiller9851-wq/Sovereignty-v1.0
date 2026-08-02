import math
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SystemConstants:
    """Fundamental parameters and physical bounds."""
    MITOCHONDRIAL_MEMBRANE_THICKNESS: float = 5.0e-9  # 5 nanometers (meters)
    DIELECTRIC_BREAKDOWN_AIR: float = 3.0e6           # 3 MV/m air breakdown limit
    DIELECTRIC_BREAKDOWN_MEMBRANE: float = 5.0e8      # 500 MV/m lipid bilayer breakdown limit
    TARGET_DISCHARGE_POWER: float = 1.21e9            # 1.21 Gigawatts (Watts)


@dataclass(frozen=True)
class Vector3D:
    """3D spatial magnitude vector for geometric directional calculations."""
    x: float
    y: float
    z: float

    def magnitude(self) -> float:
        """Calculates absolute vector magnitude: sqrt(x^2 + y^2 + z^2)."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def dot_product(self, other: 'Vector3D') -> float:
        """Computes dot product between two spatial vectors: (Ax*Bx + Ay*By + Az*Bz)."""
        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)

    def angle_between(self, other: 'Vector3D') -> float:
        """Calculates angle theta in radians between two vectors."""
        mag_product = self.magnitude() * other.magnitude()
        if mag_product == 0:
            return 0.0
        cos_theta = max(-1.0, min(1.0, self.dot_product(other) / mag_product))
        return math.acos(cos_theta)


class GAGPEnergeticsEngine:
    """
    Mathematical synthesis engine evaluating:
    1. Trigonometric spatial vector alignment (Force x Velocity).
    2. Nanoscale biological dielectric field strength (E = V / d).
    3. Temporal compression metrics required for 1.21 GW pulse discharge.
    """

    def __init__(self, voltage_millivolts: float = 200.0):
        self.constants = SystemConstants()
        self.voltage_volts = voltage_millivolts * 1.0e-3

    def evaluate_membrane_field(self) -> Dict[str, float]:
        """
        Evaluates electric field strength across the lipid bilayer membrane.
        Formula: E = V / d
        """
        field_strength = self.voltage_volts / self.constants.MITOCHONDRIAL_MEMBRANE_THICKNESS
        ratio_vs_air = field_strength / self.constants.DIELECTRIC_BREAKDOWN_AIR
        ratio_vs_membrane_limit = field_strength / self.constants.DIELECTRIC_BREAKDOWN_MEMBRANE

        return {
            "membrane_voltage_volts": self.voltage_volts,
            "membrane_thickness_meters": self.constants.MITOCHONDRIAL_MEMBRANE_THICKNESS,
            "electric_field_volts_per_meter": field_strength,
            "multiplier_vs_air_breakdown": ratio_vs_air,
            "membrane_dielectric_capacity_used": ratio_vs_membrane_limit
        }

    def evaluate_vector_work_power(
        self, 
        force_vector: Vector3D, 
        velocity_vector: Vector3D
    ) -> Dict[str, float]:
        """
        Evaluates mechanical directional efficiency using spatial dot products.
        Directly derives cos(theta) via normalized dot product to bypass redundant acos calls.
        """
        force_mag = force_vector.magnitude()
        vel_mag = velocity_vector.magnitude()
        mag_product = force_mag * vel_mag
        
        aligned_power = force_vector.dot_product(velocity_vector)
        
        cos_theta = aligned_power / mag_product if mag_product > 0 else 1.0
        cos_theta_clamped = max(-1.0, min(1.0, cos_theta))
        
        theta_rad = math.acos(cos_theta_clamped)
        theta_deg = math.degrees(theta_rad)

        return {
            "force_magnitude_newtons": force_mag,
            "velocity_magnitude_m_per_s": vel_mag,
            "alignment_angle_radians": theta_rad,
            "alignment_angle_degrees": theta_deg,
            "directional_efficiency_cos_theta": cos_theta_clamped,
            "aligned_power_watts": aligned_power
        }

    def evaluate_high_power_temporal_compression(
        self, 
        stored_energy_joules: float
    ) -> Dict[str, float]:
        """
        Calculates compressed pulse duration required to reach target gigawatt output.
        Formula: dt = E / P
        """
        target_power = self.constants.TARGET_DISCHARGE_POWER
        required_pulse_duration = stored_energy_joules / target_power

        return {
            "target_power_watts": target_power,
            "stored_energy_joules": stored_energy_joules,
            "required_pulse_duration_seconds": required_pulse_duration,
            "required_pulse_duration_microseconds": required_pulse_duration * 1.0e6
        }


def execute_pipeline() -> None:
    """Executes the complete GAGP mathematical synthesis sequence."""
    engine = GAGPEnergeticsEngine(voltage_millivolts=200.0)

    field_metrics = engine.evaluate_membrane_field()

    force_vec = Vector3D(x=150.0, y=200.0, z=50.0)
    vel_vec = Vector3D(x=10.0, y=12.0, z=2.0)
    vector_metrics = engine.evaluate_vector_work_power(force_vec, vel_vec)

    discharge_metrics = engine.evaluate_high_power_temporal_compression(stored_energy_joules=1210.0)

    print("=== GAGP ENERGETICS ENGINE EVALUATION ===")
    print("\n--- 1. BIO-MEMBRANE DIELECTRIC FIELD ---")
    for key, val in field_metrics.items():
        print(f"{key}: {val:.6e}")

    print("\n--- 2. TRIGONOMETRIC VECTOR POWER ---")
    for key, val in vector_metrics.items():
        print(f"{key}: {val:.6f}")

    print("\n--- 3. 1.21 GW TEMPORAL COMPRESSION ---")
    for key, val in discharge_metrics.items():
        print(f"{key}: {val:.6e}")


if __name__ == "__main__":
    execute_pipeline()
