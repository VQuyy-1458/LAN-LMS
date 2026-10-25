from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    time_ms: int = 2000
    memory_mib: int = 256
    output_bytes: int = 1024 * 1024

    def validate(self):
        if (
            not 100 <= self.time_ms <= 10000
            or not 64 <= self.memory_mib <= 1024
            or not 1 <= self.output_bytes <= 1024 * 1024
        ):
            raise ValueError("Invalid execution limits")
