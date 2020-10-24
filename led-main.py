import glob
import sys

import LedSpectrum1
import LedSpectrum2
import LedSpectrum3
import LedScroll1
import LedScroll2
import LedScroll3

def main():
    light_style = 'default'
    if len(sys.argv) > 1:
        light_style = (''.join(sys.argv[1:])).strip().lower()

    if light_style == 'spectrum1' or light_style == 'spectrum':
        print("Running LED Lighting - Style: Spectrum 1")
        LedSpectrum1.main()
    elif light_style == 'spectrum2':
        print("Running LED Lighting - Style: Spectrum 2")
        LedSpectrum2.main()
    elif light_style == 'spectrum3':
        print("Running LED Lighting - Style: Spectrum 3")
        LedSpectrum3.main()
    elif light_style == 'scroll1':
        print("Running LED Lighting - Style: Scroll 1")
        LedScroll1.main()
    elif light_style == 'scroll2':
        print("Running LED Lighting - Style: Scroll 2")
        LedScroll2.main()
    elif light_style == 'scroll3' or light_style == 'scroll':
        print("Running LED Lighting - Style: Scroll 3")
        LedScroll3.main()
    else:
        print("Running LED Lighting - Style: Default (Scroll 3)")
        LedScroll3.main()

if __name__ == '__main__':
    main()
