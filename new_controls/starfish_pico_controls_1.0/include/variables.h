#ifndef variables_h
#define variables_h

extern const int arm_a[4];
extern const int arm_b[4];
extern const int arm_c[4];
extern const int arm_d[4];

extern const int dutyCycle;
extern int analogDutyCycle;
extern const int delayTime;

extern String commandInput;
extern const String commandList[];
extern int commandListLength;
extern String storedCommand;
extern int acceptedInputCounter;

struct CommandStruct {
  String name;
  int pin;
};

extern CommandStruct commandDict[];
extern const int commandDictSize;

extern const char delimiter;
extern String commandInputList[];
extern int commandInputListLength;
extern bool validCondition;
extern String invalidCommandList[];

extern int invalidCounter;
extern bool initVar;
extern int commaCounter;
extern int blankCounter;
extern int dupeCounter;
#endif