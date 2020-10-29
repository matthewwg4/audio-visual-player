#include <Adafruit_NeoPixel.h>
#define PIN 6
#define NUMPIXELS 150
#define SATURATION 255
#define VALUE 255
#define SPEED 700
#define DELAY 7 


Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);
uint16_t base_hue;

void setup() {
  pixels.begin();
  base_hue = 0;
}

void loop() {

  uint16_t hue = base_hue;
  pixels.clear();
  for(uint16_t i=0; i<NUMPIXELS; i++) {
    uint32_t color = pixels.ColorHSV(hue, SATURATION, VALUE);
    pixels.setPixelColor(i, color);
    hue += SPEED;
  }
  pixels.show();
  base_hue += SPEED;
  delay(DELAY);
}
