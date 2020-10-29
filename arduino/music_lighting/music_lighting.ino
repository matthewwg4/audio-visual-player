#include <Adafruit_NeoPixel.h>
#define PIN 6
#define NUMPIXELS 150
#define PIXELSIDE (NUMPIXELS / 2)
#define NEXTPOINT (PIXELSIDE - 1)

Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);
uint8_t red[PIXELSIDE];
uint8_t green[PIXELSIDE];
uint8_t blue[PIXELSIDE];

void setup() {
  pixels.begin();

  for(int i=0; i<PIXELSIDE; i++){
    red[i] = 0;
    green[i] = 0;
    blue[i] = 0;
  }

  Serial.begin(115200);
  while(true) {
    while(Serial.available() == 0){
      digitalWrite(LED_BUILTIN, HIGH);
      delay(1000);
      digitalWrite(LED_BUILTIN, LOW);
      delay(1000);  
    }
    if(Serial.read() == 1) {
      Serial.write((uint8_t)1);
      delay(500);
      while(Serial.available() > 0) {
        Serial.read();
      }
      break;
    }
  }
}

void refresh() {
  Serial.write((uint8_t)1);
  while(Serial.available() > 0) {
    Serial.read();
  }
}

void loop() {

  for(int i=0; i<PIXELSIDE-3; i++){
    red[i] = red[i+3];
    green[i] = green[i+3];
    blue[i] = blue[i+3];
  }

  int startTime = millis();
  while(Serial.available() < 3) {
    int currTime = millis();
    if (currTime - startTime > 500) {
      refresh();
      return;
    }
  }
  red[NEXTPOINT] = Serial.read();
  blue[NEXTPOINT] = Serial.read();
  green[NEXTPOINT] = Serial.read();
  while(Serial.available() > 0) {
    Serial.read();
  }
  Serial.write((uint8_t)1);

  red[NEXTPOINT-1] = (red[NEXTPOINT] * 2 + red[NEXTPOINT-3] + 1) / 3;
  red[NEXTPOINT-2] = (red[NEXTPOINT] + red[NEXTPOINT-3] * 2 + 1) / 3;
  green[NEXTPOINT-1] = (green[NEXTPOINT] * 2 + green[NEXTPOINT-3] + 1) / 3;
  green[NEXTPOINT-2] = (green[NEXTPOINT] + green[NEXTPOINT-3] * 2 + 1) / 3;
  blue[NEXTPOINT-1] = (blue[NEXTPOINT] * 2 + blue[NEXTPOINT-3] + 1) / 3;
  blue[NEXTPOINT-2] = (blue[NEXTPOINT] + blue[NEXTPOINT-3] * 2 + 1) / 3;

  pixels.clear();
  for(uint16_t i=0; i<PIXELSIDE; i++) {
    pixels.setPixelColor(i, red[i], green[i], blue[i]);
    pixels.setPixelColor(NUMPIXELS-i-1, red[i], green[i], blue[i]);
  }
  pixels.show();
}
