#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

void setup() {
Serial.begin(9600);

pinActivate();
}

void loop() {
  initializationScript();

  readInput();
  runCommand(commandInputList);
  resetVariables();

}
