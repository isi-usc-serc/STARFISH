const int dutyCycle = 100;

void setup() {
  // Start serial communication at a baud rate of 9600
  Serial.begin(9600);

  // Initialize pin 13 as an output (built-in LED on many Arduino boards)
  pinMode(13, OUTPUT);
}

void loop() {
  // Check if data is available to read
  if (Serial.available() > 0) {
    // Read the incoming byte as a string
    String receivedString = Serial.readStringUntil('\n');
    receivedString.trim(); // Remove any whitespace characters

    // Perform actions based on the received string
    if (receivedString == "W") {
      
      analogWrite(13, (dutyCycle / 100.0) * 255);
      
      delay(2000);

      analogWrite(11, (dutyCycle / 100.0) * 255);
      analogWrite(22, (dutyCycle / 100.0) * 255);

      delay(5000);

      analogWrite(13,0);
      analogWrite(11, 0);
      analogWrite(22, 0);





    } else if (receivedString == "S") {
      // Turn off LED on pin 13
      
    } else {
      // Handle other commands or invalid input
      Serial.println("Invalid Command");
    }
  }
}