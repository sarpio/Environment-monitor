import time

class SHT41:

    def __init__(self, i2c, address=0x44):
        self.i2c = i2c
        self.address = address

    def read(self):
        self.i2c.writeto(self.address, b'\xFD')
        time.sleep_ms(10)

        data = self.i2c.readfrom(self.address, 6)

        raw_temp = (data[0] << 8) | data[1]
        raw_hum = (data[3] << 8) | data[4]

        temperature = -45 + (175 * raw_temp / 65535)
        humidity = -6 + (125 * raw_hum / 65535)

        humidity = max(0, min(100, humidity))

        return temperature, humidity