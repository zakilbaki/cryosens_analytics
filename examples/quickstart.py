from pathlib import Path

from cryosens.io.loader import load_data


sample_path = Path(__file__).with_name("sample_sensor_data.csv")
sensor_data = load_data(sample_path)

print(sensor_data.head())
