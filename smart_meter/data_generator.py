import random
from datetime import datetime


class EnergyDataGenerator:
    def __init__(self):
        self.energy_kwh = 0.0

    def generate_reading(self):
        voltage = round(random.uniform(225, 235), 2)
        current = round(random.uniform(1, 5), 2)

        power = round(voltage * current, 2)

        # Simulate a small increase in cumulative energy consumption
        self.energy_kwh += power * 3 / 3600000
        self.energy_kwh = round(self.energy_kwh, 6)

        return {
            "meter_id": "SM001",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "voltage": voltage,
            "current": current,
            "power": power,
            "energy_kwh": self.energy_kwh,
            "status": "ONLINE"
        }


if __name__ == "__main__":
    generator = EnergyDataGenerator()

    for _ in range(5):
        reading = generator.generate_reading()
        print(reading)