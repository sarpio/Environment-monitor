import time

class LPS22HH:

    def __init__(self, i2c, address=0x5D):
        self.i2c = i2c
        self.address = address

    def init(self):
        # CTRL_REG1
        self.i2c.writeto_mem(
            self.address,
            0x10,
            b'\x02'
        )

        # CTRL_REG2
        self.i2c.writeto_mem(
            self.address,
            0x11,
            b'\x10'
        )

    def whoami(self):
        return self.i2c.readfrom_mem(
            self.address,
            0x0F,
            1
        )[0]

    def read(self):

        ctrl2 = self.i2c.readfrom_mem(
            self.address,
            0x11,
            1
        )[0]

        self.i2c.writeto_mem(
            self.address,
            0x11,
            bytes([ctrl2 | 0x01])
        )

        for _ in range(50):
            status = self.i2c.readfrom_mem(
                self.address,
                0x27,
                1
            )[0]

            if (status & 0x03) == 0x03:
                break

            time.sleep_ms(10)

        data = self.i2c.readfrom_mem(
            self.address,
            0x28 | 0x80,
            5
        )

        raw_pressure = (
            data[0]
            | (data[1] << 8)
            | (data[2] << 16)
        )

        if raw_pressure & 0x800000:
            raw_pressure -= 0x1000000

        pressure = raw_pressure / 4096.0

        raw_temp = (
            data[3]
            | (data[4] << 8)
        )

        if raw_temp & 0x8000:
            raw_temp -= 0x10000

        temperature = raw_temp / 100.0

        return pressure, temperature