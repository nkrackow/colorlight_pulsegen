# SingularitySurfer 2020


import numpy as np
from migen import *
from misoc.interconnect.stream import Endpoint
from litex.soc.interconnect.csr import *

from super_interpolator import SuperInterpolator
from fft_generator_migen import Fft


class Pulsegen(Module, AutoCSR):
    """
     Pulsegen for Colorlight
    """

    def __init__(self, width_d=16, size_fft=128, r_max=4096):

        self.out0 = Signal((width_d, False))  # dac output0

        ###

        self.go = CSRStorage(1, description="start pulsegen")
        pos = Signal(int(np.log2(size_fft)))
        slow = Signal(2)
        go = Signal()

        self.submodules.fft = fft = Fft(size_fft, True, width_d, width_d, width_d, 16, False)

        self.submodules.inter = inter = SuperInterpolator(width_d, r_max)

        self.comb += [
            fft.start.eq(go),
            fft.en.eq(1),
            fft.scaling.eq(0xff),
            fft.x_out_adr.eq(pos),
            inter.input.data.eq(fft.x_out),
            inter.r.eq(200),
            #self.out0.eq(pos<<7),
            #self.out0.eq(Cat(~fft.x_out[8], fft.x_out[:7], 0x00)),
            self.out0.eq(Cat(inter.output.data0[:15], ~inter.output.data0[15])),
        ]

        self.sync += [
            slow.eq(slow + 1),
            fft.x_in.eq((2 ** (width_d - 3)) - 1000),
            fft.x_in_adr.eq(1),
            fft.x_in_we.eq(0),
            If((slow[-1] & ~go), go.eq(1), fft.x_in_we.eq(1)),
            If(inter.input.ack & fft.done,
               pos.eq(pos+1),
               #If(pos<70, pos.eq(70)),
               #pos.eq(int(np.log2(size_fft))-1),
               )
        ]
    def sim(self):
        for i in range(2000):
            yield
            #x = yield self.out0
            #if x > 700: print(x)

if __name__ == "__main__":
    test = Pulsegen()
    run_simulation(test, test.sim(), vcd_name="pulsegen.vcd")
