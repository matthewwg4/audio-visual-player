import glob
import sys

import LedScroll3
import LedPowerScroll

def main(code_directory=".", light_style='default'):
    light_style = 'default'

    if False:
        pass
    # if light_style == 'spectrum1' or light_style == 'spectrum':
    #     print("Running LED Lighting - Style: Spectrum 1")
    #     LedSpectrum1.main()
    # elif light_style == 'spectrum2':
    #     print("Running LED Lighting - Style: Spectrum 2")
    #     LedSpectrum2.main()
    # elif light_style == 'spectrum3':
    #     print("Running LED Lighting - Style: Spectrum 3")
    #     LedSpectrum3.main()
    # elif light_style == 'scroll1':
    #     print("Running LED Lighting - Style: Scroll 1")
    #     LedScroll1.main()
    # elif light_style == 'scroll2':
    #     print("Running LED Lighting - Style: Scroll 2")
    #     LedScroll2.main()
    # elif light_style == 'scroll3' or light_style == 'scroll':
    #     print("Running LED Lighting - Style: Scroll 3")
    #     LedScroll3.main()
    else:
        print("Running LED Lighting - Style: Default (Scroll 3)")
        return LedScroll3.main(code_directory)

if __name__ == '__main__':
    light_style = 'default'
    if len(sys.argv) > 1:
        light_style = (''.join(sys.argv[1:])).strip().lower()
    main(".", light_style)
