// JARVIS - Modo Centinela Supremo
// Hardware: Arduino Nano + HC-SR501 (PIR Motion Sensor)

const int sensorPIR = 2; // Pin digital 2 para la señal (OUT) del sensor PIR
const int ledPin = 13;   // LED integrado en el Nano (para feedback visual)

void setup() {
  Serial.begin(9600);
  pinMode(sensorPIR, INPUT);
  pinMode(ledPin, OUTPUT);
  Serial.println("INICIO: Arduino Centinela de JARVIS Online");
  delay(2000); // Tiempo para estabilización de energía
}

void loop() {
  int estadoPIR = digitalRead(sensorPIR);
  
  if (estadoPIR == HIGH) {
    digitalWrite(ledPin, HIGH);
    Serial.println("ALERTA: MOVIMIENTO_DETECTADO");
    
    // Evitar spam en el puerto serial (Mandar máximo 1 alerta cada 10 segundos)
    delay(10000); 
  } else {
    digitalWrite(ledPin, LOW);
  }
  
  delay(100);
}
