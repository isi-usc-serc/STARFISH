const int armTL[4] = {13, 23, 24, 25};
const int armTR[4] = {26, 27, 28, 29};
const int armBL[4] = {30, 31, 32, 33};
const int armBR[4] = {34, 35, 36, 37};

const int dutyCycle = 100;
const int pullBackDelay = 500;
const int singleWireDelay = 5000;

void setup() {
  // Start serial communication at a baud rate of 9600
  Serial.begin(9600);


  for (int i = 0; i < 4; i++) {
    pinMode(armTL[i], OUTPUT);
    pinMode(armTR[i], OUTPUT);
    pinMode(armBL[i], OUTPUT);
    pinMode(armBR[i], OUTPUT);
  }
}

void stopWireStart(int armList[4], int index, int dutyCycle){

  int delayStop = 1000;
  analogWrite(armList[index], 0);

  if (index == 0) {
    analogWrite(armList[3], (dutyCycle / 100.0) * 255);
    

  } else if (index == 1){
    analogWrite(armList[2], (dutyCycle / 100.0) * 255);
    

  }else if (index == 2){
    analogWrite(armList[1], (dutyCycle / 100.0) * 255);
    
    
  }else {
    analogWrite(armList[0], (dutyCycle / 100.0) * 255);
    
    
  }

  

}

void stopWireStop(int armList[4], int index, int dutyCycle){


  if (index == 0) {
   
    analogWrite(armList[3], 0);

  } else if (index == 1){
    
    
    analogWrite(armList[3], 0);

  }else if (index == 2){
    
    analogWrite(armList[3], 0);
    
  }else {
    
    analogWrite(armList[3], 0);
    
  }

  

}

void singleWireActivate(int armList[4], int index, int dutyCycle){
  
  analogWrite(armList[index], (dutyCycle / 100.0) * 255);
  Serial.println(armList[index]);
  delay(singleWireDelay);
  
  stopWireStart(armList, index, dutyCycle);
  
  delay(pullBackDelay);

  stopWireStop(armList, index, dutyCycle);
  

}

void pushPull(int funcTL[4], int funcTR[4], int funcBL[4], int funcBR[4], int dutyCycle){
  //start back lift
  analogWrite(funcBR[0], (dutyCycle / 100.0) * 255);
  analogWrite(funcBR[1], (dutyCycle / 100.0) * 255);
  analogWrite(funcBL[0], (dutyCycle / 100.0) * 255);
  analogWrite(funcBL[1], (dutyCycle / 100.0) * 255);
  
  delay(2000);

  //turtle pull forward
  analogWrite(funcTR[1], (dutyCycle / 100.0) * 255);
  analogWrite(funcTR[3], (dutyCycle / 100.0) * 255);
  analogWrite(funcTL[0], (dutyCycle / 100.0) * 255);
  analogWrite(funcTL[2], (dutyCycle / 100.0) * 255);
  
  delay(3000);  

  //drop back
  /*
  analogWrite(funcBR[0], 0);
  analogWrite(funcBR[1], 0);
  analogWrite(funcBL[0], 0);
  analogWrite(funcBL[1], 0);
  */

  stopWireStart(funcBR, 0, dutyCycle);
  stopWireStart(funcBR, 1, dutyCycle);
  stopWireStart(funcBL, 0, dutyCycle);
  stopWireStart(funcBL, 1, dutyCycle);
  
  delay(pullBackDelay);

  stopWireStop(funcBR, 0, dutyCycle);
  stopWireStop(funcBR, 1, dutyCycle);
  stopWireStop(funcBL, 0, dutyCycle);
  stopWireStop(funcBL, 1, dutyCycle);




  delay (5000);

  //stop pulling forward

  /*
  analogWrite(funcTR[3], 0);
  analogWrite(funcTL[2], 0);
  */


  stopWireStart(funcTR, 3, dutyCycle);
  stopWireStart(funcTL, 2, dutyCycle);
  
  delay(pullBackDelay);

  stopWireStop(funcTR, 3, dutyCycle);
  stopWireStop(funcTL, 2, dutyCycle);


  
  //start front lift
  analogWrite(funcTR[0], (dutyCycle / 100.0) * 255);
  analogWrite(funcTL[1], (dutyCycle / 100.0) * 255);


  delay(2000);
  

  //turtle push forward
  analogWrite(funcBR[1], (dutyCycle / 100.0) * 255);
  analogWrite(funcBR[3], (dutyCycle / 100.0) * 255);
  analogWrite(funcBL[0], (dutyCycle / 100.0) * 255);
  analogWrite(funcBL[2], (dutyCycle / 100.0) * 255);

  


  delay(3000);  

  //drop front

  /*
  analogWrite(funcTR[0], 0);
  analogWrite(funcTR[1], 0);
  analogWrite(funcTL[0], 0);
  analogWrite(funcTL[1], 0);
  */

  stopWireStart(funcTR, 0, dutyCycle);
  stopWireStart(funcTR, 1, dutyCycle);
  stopWireStart(funcTL, 0, dutyCycle);
  stopWireStart(funcTL, 1, dutyCycle);
  
  delay(pullBackDelay);

  stopWireStop(funcTR, 0, dutyCycle);
  stopWireStop(funcTR, 1, dutyCycle);
  stopWireStop(funcTL, 0, dutyCycle);
  stopWireStop(funcTL, 1, dutyCycle);

  delay(500);
  /*
  analogWrite(funcBR[3], 0);
  analogWrite(funcBL[2], 0);
  */

  stopWireStart(funcBR, 3, dutyCycle);
  stopWireStart(funcBL, 2, dutyCycle);
  
  
  delay(pullBackDelay);

  stopWireStop(funcBR, 3, dutyCycle);
  stopWireStop(funcBR, 2, dutyCycle);
  

}

void turn(int turnTop, int turnBottom, int otherTop, int dutyCycle){

  //rotates in given direction
  analogWrite(armBR[turnTop], (dutyCycle / 100.0) * 255);
  analogWrite(armBR[turnBottom], (dutyCycle / 100.0) * 255);
  analogWrite(armBL[turnTop], (dutyCycle / 100.0) * 255);
  analogWrite(armBL[turnBottom], (dutyCycle / 100.0) * 255);
  analogWrite(armTR[turnTop], (dutyCycle / 100.0) * 255);
  analogWrite(armTR[turnBottom], (dutyCycle / 100.0) * 255);
  analogWrite(armTL[turnTop], (dutyCycle / 100.0) * 255);
  analogWrite(armTL[turnBottom], (dutyCycle / 100.0) * 255);

  delay(5000);// changing this value will change how far it turns

  // starts lifting and ends rotation, allowing shift back to the center

  analogWrite(armBR[otherTop], (dutyCycle / 100.0) * 255);
  analogWrite(armBL[otherTop], (dutyCycle / 100.0) * 255);
  analogWrite(armTR[otherTop], (dutyCycle / 100.0) * 255);
  analogWrite(armTL[otherTop], (dutyCycle / 100.0) * 255);

  delay(100);

  /*
  analogWrite(armBR[turnBottom], 0);
  analogWrite(armBL[turnBottom], 0);
  analogWrite(armTR[turnBottom], 0);
  analogWrite(armTL[turnBottom], 0);
  */
  

  stopWireStart(armBR, turnBottom, dutyCycle);
  stopWireStart(armBL, turnBottom, dutyCycle);
  stopWireStart(armTR, turnBottom, dutyCycle);
  stopWireStart(armTL, turnBottom, dutyCycle);
  
  delay(pullBackDelay);

  stopWireStop(armBR, turnBottom, dutyCycle);
  stopWireStop(armBL, turnBottom, dutyCycle);
  stopWireStop(armTR, turnBottom, dutyCycle);
  stopWireStop(armTL, turnBottom, dutyCycle);



  delay(5000); 

  //places down
  /*
  analogWrite(armBR[turnTop], 0);
  
  analogWrite(armBL[turnTop], 0);
  
  analogWrite(armTR[turnTop], 0);
  
  analogWrite(armTL[turnTop], 0);

  analogWrite(armBR[otherTop], 0);
  
  analogWrite(armBL[otherTop], 0);
  
  analogWrite(armTR[otherTop], 0);
  
  analogWrite(armTL[otherTop], 0);
  */
  
  stopWireStart(armBR, turnTop, dutyCycle);
  stopWireStart(armBL, turnTop, dutyCycle);
  stopWireStart(armTR, turnTop, dutyCycle);
  stopWireStart(armTL, turnTop, dutyCycle);

  stopWireStart(armBR, otherTop, dutyCycle);
  stopWireStart(armBL, otherTop, dutyCycle);
  stopWireStart(armTR, otherTop, dutyCycle);
  stopWireStart(armTL, otherTop, dutyCycle);
  
  delay(pullBackDelay);

  stopWireStop(armBR, turnTop, dutyCycle);
  stopWireStop(armBL, turnTop, dutyCycle);
  stopWireStop(armTR, turnTop, dutyCycle);
  stopWireStop(armTL, turnTop, dutyCycle);

  stopWireStop(armBR, otherTop, dutyCycle);
  stopWireStop(armBL, otherTop, dutyCycle);
  stopWireStop(armTR, otherTop, dutyCycle);
  stopWireStop(armTL, otherTop, dutyCycle);


}


void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Read the incoming string
    String receivedString = Serial.readStringUntil('\n');
    receivedString.trim(); // Remove any whitespace characters

    // Parse the command
    parseCommand(receivedString);
  }
}
void parseThreeLetterCommand(char* command) {
  int index = command[2] - '0'; // Convert character to integer
  
  if (command[0] == 'T' && command[1] == 'L') {
    if (index >= 0 && index <= 3) {
      singleWireActivate(armTL, index, dutyCycle);
    } else {
      Serial.println("Invalid third character.");
    }
  } else if (command[0] == 'T' && command[1] == 'R') {
    if (index >= 0 && index <= 3) {
      singleWireActivate(armTR, index, dutyCycle);
    } else {
      Serial.println("Invalid third character.");
    }
  } else if (command[0] == 'B' && command[1] == 'L') {
    if (index >= 0 && index <= 3) {
      singleWireActivate(armBL, index, dutyCycle);
    } else {
      Serial.println("Invalid third character.");
    }
  } else if (command[0] == 'B' && command[1] == 'R') {
    if (index >= 0 && index <= 3) {
      singleWireActivate(armBR, index, dutyCycle);
    } else {
      Serial.println("Invalid third character.");
    }
  } else {
    Serial.println("Invalid command.");
  }
}

void parseCommand(String receivedString) {
  if (receivedString.length() == 1) {
    // Handle single-letter commands
    char singleCommand = receivedString.charAt(0);
    executeSingleCommand(singleCommand);
  } else if (receivedString.length() == 3) {
    // Handle three-letter commands
    char command[4];
    receivedString.toCharArray(command, 4);
    parseThreeLetterCommand(command);
  } else {
    Serial.println("Invalid input length. Please enter a single letter or a 3-character command.");
  }
}




void executeSingleCommand(char command) {
  if (command == 'w') {
      
      
      
        
      pushPull(armTL, armTR, armBL, armBR, dutyCycle);
       
      analogWrite(armBR[1], 0);
      analogWrite(armBL[0], 0);

      
      
    
      
      // Turn on LED on pin 13
      //digitalWrite(13, HIGH);
      //Serial.println("LED is ON");

      
  } else if (command == 'a') {
    
    
      
    pushPull(armBR, armTL, armBR, armTR, dutyCycle);
    
    analogWrite(armTR[1], 0);
    analogWrite(armBR[0], 0);
    

    /*
    stopWireStart(funcTR, 1, dutyCycle);
    stopWireStart(funBR, 0, dutyCycle);
    
    
    delay(pullBackDelay);

    stopWireStop(funcBR, 3, dutyCycle);
    stopWireStop(funcBR, 2, dutyCycle);      
    */
    
    // Turn off LED on pin 13
    //digitalWrite(13, LOW);
    //Serial.println("LED is OFF");
  }  else if (command == 's') {
    
    
    pushPull(armBR, armBL, armTR, armTL, dutyCycle);
    
    analogWrite(armTL[1], 0);
    analogWrite(armTR[0], 0);
    
    
    
    // Turn off LED on pin 13
    //digitalWrite(13, LOW);
    //Serial.println("LED is OFF");
  }  else if (command == 'd') {
    
    
    pushPull(armTR, armBR, armTL, armBL, dutyCycle);
    
    analogWrite(armBL[1], 0);
    analogWrite(armTL[0], 0);
    
    
    
    
    // Turn off LED on pin 13
    //digitalWrite(13, LOW);
    //Serial.println("LED is OFF");
  }  else if (command == 'q') {
    
    
    turn(1,3,0,dutyCycle);
    
    
    
    
    
    // Turn off LED on pin 13
    //digitalWrite(13, LOW);
    //Serial.println("LED is OFF");
  } else if (command == 'e') {
    
    
    turn(0,2,1,dutyCycle);
    
    
    
    
    
    // Turn off LED on pin 13
    //digitalWrite(13, LOW);
    //Serial.println("LED is OFF");
  } else if (command == 'i') {
    
    
    // this pushes up
    analogWrite(armBR[2], (dutyCycle / 100.0) * 255);
    analogWrite(armBR[3], (dutyCycle / 100.0) * 255);
    analogWrite(armBL[2], (dutyCycle / 100.0) * 255);
    analogWrite(armBL[3], (dutyCycle / 100.0) * 255);
    analogWrite(armTR[2], (dutyCycle / 100.0) * 255);
    analogWrite(armTR[3], (dutyCycle / 100.0) * 255);
    analogWrite(armTL[2], (dutyCycle / 100.0) * 255);
    analogWrite(armTL[3], (dutyCycle / 100.0) * 255);

    delay(5000);


    analogWrite(armBR[2], 0);

    analogWrite(armBL[2], 0);
    
    analogWrite(armTR[2], 0);
    
    analogWrite(armTL[2], 0);

    analogWrite(armBR[3], 0);
    
    analogWrite(armBL[3], 0);
    
    analogWrite(armTR[3], 0);
    
    analogWrite(armTL[3], 0);

    
    
    
    
    
    // Turn off LED on pin 13
    //digitalWrite(13, LOW);
    //Serial.println("LED is OFF");
  } else {
    // Handle other commands or invalid input
    Serial.println("Invalid Command");
  }
}
