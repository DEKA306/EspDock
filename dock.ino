#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

const int DATA_SIZE = SCREEN_WIDTH * SCREEN_HEIGHT / 8;
byte frameBuffer[DATA_SIZE];
int imgIndex = 0;

void setup() {
  Serial.begin(115200);

  // OLED 초기화
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)){
    for(;;); // 초기화 실패 시 멈춤
  }

  // OLED 켜질 때 초기 메시지
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("OLED Ready");
  display.println("Waiting for data...");
  display.display();
}

void loop() {
  // 시리얼 데이터 수신 대기
  if (Serial.available() > 0) {
    imgIndex = 0;
    while(imgIndex < DATA_SIZE){
      if(Serial.available() > 0){
        frameBuffer[imgIndex++] = Serial.read();
      }
    }

    // 수신 완료 후 화면 표시
    display.clearDisplay();
    display.drawBitmap(0, 0, frameBuffer, SCREEN_WIDTH, SCREEN_HEIGHT, WHITE);
    display.display();
  } else {
    // 연결 안 됐을 때 메시지 유지
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 0);
    display.println("Waiting for data...");
    display.display();
    delay(500); // 화면 깜빡임 방지
  }
}
