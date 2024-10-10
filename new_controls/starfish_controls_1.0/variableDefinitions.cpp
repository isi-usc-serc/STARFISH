#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

const int arm1[4] = {13, 23, 24, 25};
const int arm2[4] = {26, 27, 28, 29};
const int arm3[4] = {30, 31, 32, 33};
const int arm4[4] = {34, 35, 36, 37};

const int dutyCycle = 4;
const int delayTime = 500;
String commandInput;
