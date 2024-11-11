#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

void setup() {
Serial.begin(9600);

pinActivate();

}

void loop() {
  readInput();
  runCommand(storedCommand);
  resetVariables();
}
