from SerialCommunicator import SerialCommunicator

def main():
    serial = SerialCommunicator()
    serial.setup()
    #rgb = ([0]*10) + ([0, 10, 30, 65, 145, 255]) + ([0]*34)
    #rgb = ([0]*10) + ([0, 4, 10, 17, 30, 43, 65, 90, 108, 145, 195, 255]) + ([0]*28)
    #rgb = ([0]*10) + [0, 2, 4, 6, 9, 13, 17, 22, 28, 34, 43, 53, 65, 77, 89, 102, 115, 145, 195, 255] + ([0]*20)
    rgb = ([0]*24) + ([1, 1]) + ([0]*24)


    serial.send_colors(rgb, rgb, rgb)

if __name__ == '__main__':
    main()
