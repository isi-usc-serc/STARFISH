#ifndef variables_h
#define variables_h
#include <vector>
#include <string>
#include <unordered_map>

// System constants
extern const int MAX_PIN_NUMBER;

// Pin configurations
extern const int arm_a[4];
extern const int arm_b[4];
extern const int arm_c[4];
extern const int arm_d[4];

// Control parameters
extern const int dutyCycle;
extern int analogDutyCycle;
extern const int delayTime;

// Command related variables
extern String commandInput;
extern const std::vector<String> commandList; 
extern String storedCommand;
extern int acceptedInputCounter;

struct CommandStruct {
  String name;
  int pin;
};

extern const size_t commandDictSize;

extern const char delimiter;
extern std::vector<String> commandInputList;
extern std::vector<String> invalidCommandList;

extern int invalidCounter;
extern bool initVar;
extern int commaCounter;
extern int blankCounter;
extern int dupeCounter;
extern bool validCondition;

extern std::unordered_map<std::string, int> commandCount;
extern std::unordered_map<std::string, int> commandDict;
extern std::unordered_map<std::string, int> commandMap;


#endif