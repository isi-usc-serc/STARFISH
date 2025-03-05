#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

void setup() {
Serial.begin(9600);

delay(1000);
pinActivate();

}

void loop() {

  while (!Serial.available()) {
    initializationScript();
  }
  readInput();
  runCommand(commandInputList);
}
