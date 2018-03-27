from influxdb import InfluxDBClient
import datetime

time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
print(time)
json_body = [
    {
        "measurement": "jay_egress",
        "tags": {},
        "time": time,
        "fields": {
            "value": 4
        }
    }
]

client = InfluxDBClient('192.168.200.131', 8086, '', '', 'roc')

client.write_points(json_body, time_precision="ms")

result = client.query('select value from jay_egress;')

print("Result: {0}".format(result))

print(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))